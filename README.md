# Marqo-InstantAPI [In Development]

`marqo-instantapi` is a Python package that integrates Marqo with Instant API, enabling users to create, index, and search documents efficiently with multimodal capabilities. This package simplifies the process of extracting data from web pages and indexing it in Marqo for fast and accurate searches.

## Prerequisites

- Docker installed on your machine.
- Python 3.8 or above.
- An [InstantAPI API key](https://instantapi.ai/)

## Installation

To get started, you need to run the Marqo container:

```bash
docker run --name marqo -it -p 8882:8882 marqoai/marqo:latest
```

Install the required dependencies:
```bash
pip install -r requirements.txt
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
python example.py
```

## Creating documentation

Eun the following command to locally build the documentation:

```bash
sphinx-build -b html docs/source docs/build
```

## Running tests

To run tests use pytest:

```bash
python -m pytest
```

To run the integration tests as well add the flag `--integration`:

```bash
python -m pytest --integration
```

## Formatting code

We use the `black` code formatter. To format the code run:

```bash
black .
```