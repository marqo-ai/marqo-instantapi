import pytest
import marqo
from unittest.mock import patch
import hashlib
from marqo_instantapi import InstantAPIMarqoAdapter


@pytest.fixture
def adapter():
    return InstantAPIMarqoAdapter()


@pytest.fixture
def mq():
    return marqo.Client()


@pytest.mark.integration
def test_create_index(adapter: InstantAPIMarqoAdapter):
    adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
    response = adapter.create_index(
        "example-index", multimodal=True, skip_if_exists=True
    )
    # Expected: {"acknowledged":true, "index":"my-first-index"}

    assert response["acknowledged"] is True
    assert response["index"] == "example-index"


@pytest.mark.integration
def test_error_if_exists(adapter: InstantAPIMarqoAdapter):
    adapter.create_index("example-index", multimodal=True, skip_if_exists=True)
    with pytest.raises(Exception):
        adapter.create_index("example-index", multimodal=True, skip_if_exists=False)


@pytest.mark.integration
def test_error_if_not_exists(adapter: InstantAPIMarqoAdapter):
    adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
    with pytest.raises(Exception):
        response = adapter.delete_index(
            "example-index", confirm=True, skip_if_not_exists=False
        )
        print(response)


@pytest.mark.integration
def test_check_exists(adapter: InstantAPIMarqoAdapter):
    adapter.create_index("example-index", multimodal=True, skip_if_exists=True)
    assert adapter._check_index_exists("example-index") is True
    adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
    assert adapter._check_index_exists("example-index") is False


@pytest.mark.integration
def test_check_modality(adapter: InstantAPIMarqoAdapter):
    adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
    adapter.create_index("example-index", multimodal=True)
    assert adapter._check_index_can_use_images("example-index") is True
    adapter.delete_index("example-index", confirm=True)

    adapter.create_index("example-index", multimodal=False)
    assert adapter._check_index_can_use_images("example-index") is False
    adapter.delete_index("example-index", confirm=True)


@pytest.mark.integration
def test_search_index(adapter: InstantAPIMarqoAdapter, mq: marqo.Client):
    adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
    adapter.create_index("example-index", multimodal=False)

    response = mq.index("example-index").add_documents(
        [
            {"title": "Hello, World!", "content": "This is a test document."},
            {"title": "Goodbye, World!", "content": "This is another test document."},
        ],
        tensor_fields=["title"],
    )

    assert not response["errors"]

    search_results = adapter.search(
        q="hello",
        index_name="example-index",
    )

    assert len(search_results["hits"]) == 2
    assert search_results["hits"][0]["title"] == "Hello, World!"
    assert search_results["hits"][1]["title"] == "Goodbye, World!"

    adapter.delete_index("example-index", confirm=True)


# TODO: introduce back with Marqo 2.12
# @pytest.mark.integration
# def test_search_index_searchable_attrs(
#     adapter: InstantAPIMarqoAdapter, mq: marqo.Client
# ):
#     adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
#     adapter.create_index("example-index", multimodal=False)

#     response = mq.index("example-index").add_documents(
#         [
#             {"title": "Hello, World!", "content": "This is a test document."},
#             {"title": "Goodbye, World!", "content": "This is another test document."},
#         ],
#         tensor_fields=["title"],
#     )

#     assert not response["errors"]

#     search_results = adapter.search(
#         q="hello",
#         index_name="example-index",
#         searchable_attributes=["title"],
#     )

#     assert len(search_results["hits"]) == 2
#     assert search_results["hits"][0]["title"] == "Hello, World!"
#     assert search_results["hits"][1]["title"] == "Goodbye, World!"

#     adapter.delete_index("example-index", confirm=True)


@pytest.mark.integration
def test_add_documents(adapter: InstantAPIMarqoAdapter):
    with patch.object(adapter, "_extract_page_data") as mock_extract_page_data:
        mock_extract_page_data.return_value = {
            "title": "Hello, World!",
            "content": "This is a test document.",
        }

        adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
        adapter.create_index("example-index", multimodal=False)

        schema = {
            "title": "the title of the page",
            "content": "text content summarising the page",
        }

        response = adapter.add_documents(
            webpage_urls=["https://example.com"],
            index_name="example-index",
            api_response_structure=schema,
            api_method_name="getPageSummary",
            text_fields_to_index=["title", "content"],
        )

        url_md5 = hashlib.md5("https://example.com".encode()).hexdigest()

        response_ids = [doc["url_md5"] for doc in response]

        assert len(response_ids) == 1
        assert response_ids[0] == url_md5
