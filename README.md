# Marqo-InstantAPI

`marqo-instantapi` is a Python package that integrates Marqo with Instant API, enabling users to create, index, and search documents efficiently with multimodal capabilities. This package simplifies the process of extracting data from web pages and indexing it in Marqo for fast and accurate searches.

## Prerequisites

- Docker installed on your machine.
- Python 3.7 or above.
- An Instant API key (you can set this in your environment variables).

## Installation

To get started, you need to run the Marqo container:

```bash
docker run --name marqo -it -p 8882:8882 marqoai/marqo:latest
```

Then, install the marqo-instantapi package:

bash```
<!-- pip install marqo-instantapi -->
pip install .
```