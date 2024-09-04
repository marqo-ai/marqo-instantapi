# Marqo-InstantAPI [In Development]

`marqo-instantapi` is a Python package that integrates Marqo with Instant API, enabling users to create, index, and search documents efficiently with multimodal capabilities. This package simplifies the process of extracting data from web pages and indexing it in Marqo for fast and accurate searches.

## Prerequisites

- Docker installed on your machine.
- Python 3.7 or above.
- An Instant API key

## Installation

To get started, you need to run the Marqo container:

```bash
docker run --name marqo -it -p 8882:8882 marqoai/marqo:latest
```

Then, install the marqo-instantapi package:
```bash
pip install .
```

## Running the Example

To run the example, you need to set the `INSTANTAPI_KEY` environment variable. You can do this by creating a `.env` file in the root directory of the project and adding the following line:

```
INSTANTAPI_KEY=your_instantapi_key
```

Then, run the example script:

```bash
pip install python-dotenv
python example.py
```