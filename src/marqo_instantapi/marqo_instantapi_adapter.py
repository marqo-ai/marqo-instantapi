import marqo
from collections import deque
from typing import Optional, Union

class InstantAPIMarqoAdapter():
    def __init__(
        self,
        marqo_url: str = "http://localhost:8882",
        marqo_api_key: Optional[str] = None,
        instantapi_key: Optional[str] = None,
    ):
        self.mq = marqo.Client(url=marqo_url, api_key=marqo_api_key)
        self.instant_api_key = instantapi_key

    def create_index(self, index_name: str, multimodal: bool = False, model: Optional[str] = None):
        if model is None:
            if multimodal:
                model = "open_clip/ViT-B-32/laion2b_s34b_b79k"
            else:
                model = "hf/e5-base-v2"

        return self.mq.create_index(index_name, model=model, treat_urls_and_pointers_as_images=multimodal)

    def _extract_page_data(self, webpage_url: str, api_response_structure: dict):
        pass

    def _make_mappings(self, text_fields_to_index: list[str], image_fields_to_index: list[str]) -> Union[dict, list]:
        pass

    def add_documents(
        self,
        webpage_urls: list[str],
        index_name: str,
        api_response_structure: dict,
        text_fields_to_index: list[str],
        image_fields_to_index: list[str],
        client_batch_size: int = 8,
    ) -> dict:

        documents = []
        for webpage_url in webpage_urls:
            page_data = self._extract_page_data(webpage_url, api_response_structure)
            documents.append(page_data)

        mappings, tensor_fields = self._make_mappings(text_fields_to_index, image_fields_to_index)
        response = self.mq.index(index_name).add_documents(
            documents=documents,
            tensor_fields=tensor_fields,
            mappings=mappings,
            client_batch_size=client_batch_size,
        )

        return response
    
    def crawl(
        self,
        initial_webpage_urls: list[str],
        allowed_domains: list[str],
        index_name: str,
        api_response_structure: dict,
        text_fields_to_index: list[str],
        image_fields_to_index: list[str],
        client_batch_size: int = 8,
        max_pages: Optional[int] = None,
    ):
        q = deque(initial_webpage_urls)
        pages = 0
        while q:
            pages += 1
            if max_pages and pages > max_pages:
                break

            webpage_url = q.popleft()
            page_data = self._extract_page_data(webpage_url, api_response_structure)
            response = self.add_documents(
                [webpage_url],
                index_name,
                api_response_structure,
                text_fields_to_index,
                image_fields_to_index,
                client_batch_size,
            )

    def search(self, query: str, index_name: str, limit: int = 10, searchable_attributes: Optional[list] = None):
        return self.mq.index(index_name).search(query, limit=limit, searchable_attributes=searchable_attributes)