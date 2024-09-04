import marqo
import tldextract
from marqo_instantapi.instant_api_client import InstantAPIClient
from collections import deque
import hashlib
from typing import Optional, Union, Literal, Any


class InstantAPIMarqoAdapter:
    """A class for interfacing with Marqo and InstantAPI."""

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

        Examples:
            >>> marqo_adapter = InstantAPIMarqoAdapter()
            >>> marqo_adapter.create_index("my-index")
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

    def delete_index(self, index_name: str, confirm: bool = False) -> dict:
        """Delete a Marqo index.

        Args:
            index_name (str): The name of the index to delete.
            confirm (bool, optional): Automatically confirms the deletion. Defaults to False.

        Returns:
            dict: The deletion response.
        """
        if not confirm:
            choice = None
            while choice not in ("y", "n"):
                choice = input(
                    f"Are you sure you want to delete the index '{index_name}'? (y/n): "
                )
            if choice == "n":
                return {"message": "Deletion cancelled."}

        response = self.mq.delete_index(index_name)
        return response

    def _extract_page_data(
        self, webpage_url: str, api_method_name: str, api_response_structure: dict
    ):
        """
        Extract structured page data from a webpage using the InstantAPI Retrieve API.

        Args:
            webpage_url (str): The URL of the webpage to extract.
            api_method_name (str): The name of the API method to use for data extraction.
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
            total_image_weight (float): The total weight for images.
            total_text_weight (float): The total weight for text.

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
        """Check if a schema conforms to Marqo's requirements. Schemas must be flat documents.

        Args:
            schema (dict): The schema to check.

        Raises:
            ValueError: If the schema does not conform to Marqo's requirements.
        """
        for k in schema:
            if not isinstance(schema[k], str):
                raise ValueError(
                    "All schema values must be strings. Marqo only accepts flat documents so you cannot nest JSON."
                )

    def _check_against_schema(
        self, schema: Union[dict, list, Any], response: Union[dict, list, Any]
    ) -> bool:
        """Check if a response conforms to a schema.

        Args:
            schema (Union[dict, list, Any]): The schema to check against.
            response (Union[dict, list, Any]): The response to check.

        Returns:
            bool: True if the response conforms to the schema, False otherwise.
        """
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
        """Check if a Marqo index exists.

        Args:
            index_name (str): The name of the index to check.

        Returns:
            bool: True if the index exists, False otherwise.
        """
        response = self.mq.get_indexes()
        return index_name in [index["indexName"] for index in response["results"]]

    def _check_index_can_use_images(self, index_name: str) -> bool:
        """Check if a Marqo index can use images.

        Args:
            index_name (str): The name of the index to check.

        Returns:
            bool: True if the index can use images, False otherwise.
        """
        response = self.mq.index(index_name).get_settings()
        return response["treatUrlsAndPointersAsImages"]

    def _create_index_from_fields(
        self,
        index_name: str,
        text_fields_to_index: list[str] = [],
        image_fields_to_index: list[str] = [],
    ) -> dict:
        """Create a Marqo index based on the fields to index.

        Args:
            index_name (str): The name of the index to create.
            text_fields_to_index (list[str], optional): A list of text fields for indexing. Defaults to [].
            image_fields_to_index (list[str], optional): A list of image fields for indexing. Defaults to [].

        Raises:
            ValueError: If no fields are provided for indexing.

        Returns:
            dict: The index creation response.
        """
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
        """Add documents to a Marqo index from a list of webpage URLs, data is extracted using the InstantAPI Retrieve API.

        Args:
            webpage_urls (list[str]): A list of webpage URLs to index.
            index_name (str): The name of the index to add documents to. If the index does not exist, it will be created based on the fields to index.
            api_response_structure (dict): The expected structure of the API's response, this is passed to InstantAPI.
            api_method_name (str): The name of the API method to use for data extraction, this is passed to InstantAPI and should be descriptive to help to AI know what information to get.
            text_fields_to_index (list[str], optional): A list of text fields for indexing. Defaults to [].
            image_fields_to_index (list[str], optional): A list of image fields for indexing. Defaults to [].
            client_batch_size (int, optional): The client batch size for Marqo, controls how many docs are sent at a time. Defaults to 8.
            total_image_weight (float, optional): The total weight for images, applies when both image and text fields are provided. Defaults to 0.9.
            total_text_weight (float, optional): The total weight for text, applies when both image and text fields are provided. Defaults to 0.1.
            enforce_schema (bool, optional): Toggle strict enforcement of InstantAPI responses against the schema. Defaults to True.

        Raises:
            ValueError: If no fields are provided for indexing.

        Returns:
            list[dict]: A list of responses for each document added.
        """

        if not text_fields_to_index and not image_fields_to_index:
            raise ValueError(
                "At least one field must be specified in text_fields_to_index and/or image_fields_to_index."
            )

        if not self._check_index_exists(index_name):
            self._create_index_from_fields(
                index_name, text_fields_to_index, image_fields_to_index
            )

        if image_fields_to_index and not self._check_index_can_use_images(index_name):
            raise ValueError(
                "The index does not support images, please recreate the index create_index(index_name, multimodal=True)"
            )

        if not image_fields_to_index and self._check_index_can_use_images(index_name):
            raise ValueError(
                "The index supports images, please either provide image fields to index or recreate the index create_index(index_name, multimodal=False)"
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
            url (str): The URL to extract the domain from.

        Returns:
            str: The subdomain, domain, and suffix of the URL combined.
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
        total_image_weight: float = 0.9,
        total_text_weight: float = 0.1,
        enforce_schema: bool = True,
        max_pages: Optional[int] = None,
    ) -> list[dict]:
        """Crawl a set of webpages and add them to a Marqo index.

        Args:
            initial_webpage_urls (list[str]): A list of initial webpage URLs to start the crawl from.
            allowed_domains (set[str]): A set of domains to exclude from the crawl.
            index_name (str): The name of the index to add documents to. If the index does not exist, it will be created based on the fields to index.
            api_response_structure (dict): The expected structure of the API's response, this is passed to InstantAPI.
            text_fields_to_index (list[str], optional): A list of text fields for indexing. Defaults to [].
            image_fields_to_index (list[str], optional): A list of image fields for indexing. Defaults to [].
            client_batch_size (int, optional): The client batch size for Marqo, controls how many docs are sent at a time. Defaults to 8.
            total_image_weight (float, optional): The total weight for images, applies when both image and text fields are provided. Defaults to 0.9.
            total_text_weight (float, optional): The total weight for text, applies when both image and text fields are provided. Defaults to 0.1.
            enforce_schema (bool, optional): Toggle strict enforcement of InstantAPI responses against the schema. Defaults to True.
            max_pages (Optional[int], optional): The maximum number of pages to crawl. Defaults to None.

        Raises:
            ValueError: If no fields are provided for indexing.

        Returns:
            list[dict]: A list of responses for each document added.
        """

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
                total_image_weight,
                total_text_weight,
                enforce_schema,
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
        offset: int = 0,
        searchable_attributes: Optional[list] = None,
        method: Literal["tensor", "lexical", "hybrid"] = "hybrid",
    ) -> dict:
        """Search a Marqo index via a simplified interface.

        Args:
            q (str): The query string to search for.
            index_name (str): The name of the index to search.
            limit (int, optional): The number of results to retrieve. Defaults to 10.
            offset (int, optional): The offset for the search results. Defaults to 0.
            searchable_attributes (Optional[list], optional): The attributes to search. Defaults to None.
            method (Literal["tensor", "lexical", "hybrid"], optional): The search method to use, tensor uses only vectors, lexical uses only text, hybrid combines both with RRF. Defaults to "hybrid".

        Raises:
            ValueError: If an invalid search method is provided.

        Returns:
            dict: The search response from Marqo.
        """

        if method not in ("tensor", "lexical", "hybrid"):
            raise ValueError(
                "Invalid search method, must be one of 'tensor', 'lexical', or 'hybrid'."
            )

        ef_search = None
        if limit + offset > 2000:
            ef_search = limit + offset

        response = self.mq.index(index_name).search(
            q,
            limit=limit,
            offset=offset,
            ef_search=ef_search,
            searchable_attributes=searchable_attributes,
            search_method=method,
        )

        return response
