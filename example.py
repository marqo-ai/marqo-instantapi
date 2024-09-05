import os
from marqo_instantapi import InstantAPIMarqoAdapter

from dotenv import load_dotenv

load_dotenv()


def main():
    adapter = InstantAPIMarqoAdapter(instantapi_key=os.getenv("INSTANTAPI_KEY"))

    adapter.delete_index("example-index", confirm=True, skip_if_not_exists=True)
    response = adapter.create_index(
        "example-index", multimodal=True, skip_if_exists=True
    )
    print("Create index response:")
    print(response)

    webpage_urls = [
        "https://www.ebay.com/itm/175955440726",
        "https://www.ebay.com/itm/194951252662",
    ]

    api_response_structure = {
        "image_url": "<the url of the product image (string)>",
        "title": "<the name of the product (string)>",
        "description": "<the description of the product (string)>",
        "price": "<the price of the product (float)>",
    }

    response = adapter.add_documents(
        webpage_urls=webpage_urls,
        index_name="example-index",
        api_response_structure=api_response_structure,
        api_method_name="getProductListingDetails",
        text_fields_to_index=["title", "description"],
        image_fields_to_index=["image_url"],
    )

    print("Add documents response:")
    print(response)

    response = adapter.search(
        q="coffee mug", index_name="example-index", limit=10, search_method="tensor"
    )

    print("Search results:")
    print(
        *[
            f"{hit['_source_webpage_url']} - {hit['title']}: {hit['_score']}"
            for hit in response["hits"]
        ],
        sep="\n",
    )


if __name__ == "__main__":
    main()
