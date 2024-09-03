import marqo
import tldextract
from marqo_instantapi.instant_api_client import InstantAPIClient
from collections import deque
import hashlib
from typing import Optional, Union, Literal, Any


class InstantAPIMarqoAdapter:
    def __init__(
        self,
        marqo_url: str = "http://localhost:8882",
        marqo_api_key: Optional[str] = None,
        instantapi_key: Optional[str] = None,
    ):
        self.mq = marqo.Client(url=marqo_url, api_key=marqo_api_key)
        self.instant_api = InstantAPIClient(api_key=instantapi_key)
        self.combination_field = "combination"

        self.default_marqo_settings_dict = {
            "type": "unstructured",
            "vectorNumericType": "float",
            "treatUrlsAndPointersAsImages": True,
            "model": "open_clip/ViT-L-14/laion2b_s32b_b82k",
            "normalizeEmbeddings": True,
            "textPreprocessing": {
                "splitLength": 3,
                "splitOverlap": 1,
                "splitMethod": "sentence",
            },
            "annParameters": {
                "spaceType": "prenormalized-angular",
                "parameters": {"efConstruction": 512, "m": 16},
            },
            "filterStringMaxLength": 50,
        }

    def create_index(
        self,
        index_name: str,
        multimodal: bool = False,
        model: Optional[str] = None,
        skip_if_exists: bool = False,
    ) -> dict:
        """Simplified method for creating a Marqo index, recommended when fine grained control is not needed.

        Args:
            index_name (str): The name of the index to create.
            multimodal (bool, optional): Toggles image downloading on or off, if model is not provided then also influences model selection. Defaults to False.
            model (Optional[str], optional): Optionally specify a specific model. Defaults to None.
            skip_if_exists (bool, optional): Skip index creation if the index already exists, does not check if the index conforms to the provided parameters. Defaults to False.

        Returns:
            dict: index creation response
        """
        settings = {**self.default_marqo_settings_dict}

        if model is None:
            if multimodal:
                settings["model"] = "open_clip/ViT-B-32/laion2b_s34b_b79k"
            else:
                settings["model"] = "hf/e5-base-v2"

        settings["treatUrlsAndPointersAsImages"] = multimodal

        if self._check_index_exists(index_name) and skip_if_exists:
            self.mq.index(index_name).search(q="")
            return {
                "acknowledged": True,
                "index": index_name,
                "message": "Index already exists, skipping creation.",
            }

        response = self.mq.create_index(index_name, settings_dict=settings)
        self.mq.index(index_name).search(q="")
        return response

    def _extract_page_data(
        self, webpage_url: str, api_method_name: str, api_response_structure: dict
    ):
        """
        Extract structured page data from a webpage using the InstantAPI Retrieve API.

        Args:
            webpage_url (str): The URL of the webpage to extract.
            api_response_structure (dict): The expected structure of the API's response.

        Returns:
            dict: The structured data extracted from the webpage, or an error message.
        """

        response = self.instant_api.retrieve(
            webpage_url=webpage_url,
            api_method_name=api_method_name,
            api_response_structure=api_response_structure,
        )

        return response

    def _make_mappings(
        self,
        text_fields_to_index: list[str],
        image_fields_to_index: list[str],
        total_image_weight: float,
        total_text_weight: float,
    ) -> tuple[Union[dict, None], list]:
        """Automatically make a multimodal combination field mapping based on the text and image fields to index.

        Args:
            text_fields_to_index (list[str]): The text fields to index.
            image_fields_to_index (list[str]): The image fields to index.

        Returns:
            Union[Union[dict, None], list]: A mappings object for Marqo
        """
        if not text_fields_to_index:
            return None, image_fields_to_index

        if not image_fields_to_index:
            return None, text_fields_to_index

        if total_image_weight == 0:
            image_fields_to_index = []

        if total_text_weight == 0:
            text_fields_to_index = []

        text_weight = (
            total_text_weight / len(text_fields_to_index) if text_fields_to_index else 0
        )
        image_weight = (
            total_image_weight / len(image_fields_to_index)
            if image_fields_to_index
            else 0
        )
        weights = {}
        for field in text_fields_to_index:
            weights[field] = text_weight

        for field in image_fields_to_index:
            weights[field] = image_weight

        mappings = {
            self.combination_field: {
                "type": "multimodal_combination",
                "weights": weights,
            }
        }

        return mappings, [self.combination_field]

    def _check_schema_for_marqo(self, schema: dict) -> None:
        for k in schema:
            if not isinstance(schema[k], str):
                raise ValueError(
                    "All schema values must be strings. Marqo only accepts flat documents."
                )

    def _check_against_schema(
        self, schema: dict | list | Any, response: dict | list | Any
    ) -> bool:
        if isinstance(schema, dict):
            if not isinstance(response, dict):
                return False
            for key in schema:
                if key not in response or not self._check_against_schema(
                    schema[key], response[key]
                ):
                    return False

            if len(schema) != len(response):
                return False
            return True
        elif isinstance(schema, list):
            if not isinstance(response, list) or len(response) != len(schema):
                return False
            return all(
                self._check_against_schema(s, r) for s, r in zip(schema, response)
            )

        return True

    def _check_index_exists(self, index_name: str) -> bool:
        response = self.mq.get_indexes()
        return index_name in [index["indexName"] for index in response["results"]]

    def _create_index_from_fields(
        self,
        index_name: str,
        text_fields_to_index: list[str] = [],
        image_fields_to_index: list[str] = [],
    ):
        if not text_fields_to_index and not image_fields_to_index:
            raise ValueError(
                "At least one field must be specified in text_fields_to_index and/or image_fields_to_index."
            )

        if text_fields_to_index and not image_fields_to_index:
            return self.create_index(index_name, multimodal=False)

        return self.create_index(index_name, multimodal=True)

    def add_documents(
        self,
        webpage_urls: list[str],
        index_name: str,
        api_response_structure: dict,
        api_method_name: str,
        text_fields_to_index: list[str] = [],
        image_fields_to_index: list[str] = [],
        client_batch_size: int = 8,
        total_image_weight: float = 0.9,
        total_text_weight: float = 0.1,
        enforce_schema: bool = True,
    ) -> list[dict]:

        if not text_fields_to_index and not image_fields_to_index:
            raise ValueError(
                "At least one field must be specified in text_fields_to_index and/or image_fields_to_index."
            )

        if not self._check_index_exists(index_name):
            self._create_index_from_fields(
                index_name, text_fields_to_index, image_fields_to_index
            )

        self._check_schema_for_marqo(api_response_structure)

        failed_schema_checks = []
        urls_to_index = []
        documents = []
        for webpage_url in webpage_urls:
            page_data = self._extract_page_data(
                webpage_url=webpage_url,
                api_method_name=api_method_name,
                api_response_structure=api_response_structure,
            )

            if enforce_schema:
                if not self._check_against_schema(api_response_structure, page_data):
                    failed_schema_checks.append(
                        {
                            "url": webpage_url,
                            "response_data": page_data,
                            "response": "Schema check failed",
                        }
                    )
                    continue

            urls_to_index.append(webpage_url)
            page_data["_id"] = hashlib.md5(webpage_url.encode()).hexdigest()
            page_data["_source_webpage_url"] = webpage_url

            documents.append(page_data)
        print(documents)
        mappings, tensor_fields = self._make_mappings(
            text_fields_to_index,
            image_fields_to_index,
            total_image_weight,
            total_text_weight,
        )

        responses = self.mq.index(index_name).add_documents(
            documents=documents,
            tensor_fields=tensor_fields,
            mappings=mappings,
            client_batch_size=client_batch_size,
        )

        if not isinstance(responses, list):
            responses = [responses]

        outcomes = failed_schema_checks
        for response in responses:
            for item in response["items"]:
                outcomes.append({"url_md5": item["_id"], "response": item})

        return outcomes

    def _get_root_domain(self, url: str) -> str:
        """Get the root domain of a URL.

        Args:
            url (str): _description_

        Returns:
            str: _description_
        """
        extracted = tldextract.extract(url)
        domain = f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}"
        return domain

    def crawl(
        self,
        initial_webpage_urls: list[str],
        allowed_domains: set[str],
        index_name: str,
        api_response_structure: dict,
        text_fields_to_index: list[str] = [],
        image_fields_to_index: list[str] = [],
        client_batch_size: int = 8,
        max_pages: Optional[int] = None,
    ) -> list[dict]:

        if not text_fields_to_index and not image_fields_to_index:
            raise ValueError(
                "At least one field must be specified in text_fields_to_index and/or image_fields_to_index."
            )

        q = deque(initial_webpage_urls)
        pages = 0
        responses = []
        visited = set()
        while q:
            pages += 1
            if max_pages and pages > max_pages:
                break

            webpage_url = q.popleft()

            if webpage_url in visited:
                continue

            visited.add(webpage_url)

            if self._get_root_domain(webpage_url) in allowed_domains:
                continue

            response = self.add_documents(
                [webpage_url],
                index_name,
                api_response_structure,
                text_fields_to_index,
                image_fields_to_index,
                client_batch_size,
            )
            responses += response

            next_pages = self.instant_api.next_pages(webpage_url)
            for next_page in next_pages["webpage_urls"]:
                q.append(next_page)

        return responses

    def search(
        self,
        q: str,
        index_name: str,
        limit: int = 10,
        searchable_attributes: Optional[list] = None,
        method: Literal["tensor", "lexical", "hybrid"] = "hybrid",
    ) -> dict:
        response = self.mq.index(index_name).search(
            q, limit=limit, searchable_attributes=searchable_attributes
        )
        return response
