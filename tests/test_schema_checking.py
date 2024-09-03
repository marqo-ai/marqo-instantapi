import pytest
from marqo_instantapi import InstantAPIMarqoAdapter


@pytest.fixture
def adapter() -> InstantAPIMarqoAdapter:
    return InstantAPIMarqoAdapter()


@pytest.fixture
def simple_schema() -> dict:
    schema = {
        "response": {
            "name": "<the name of the user>",
            "email": "<the email address of the user>",
        }
    }
    return schema


@pytest.fixture
def simple_flat_schema() -> dict:
    schema = {
        "name": "<the name of the user>",
        "email": "<the email address of the user>",
    }
    return schema


def test_basic_schema(adapter: InstantAPIMarqoAdapter, simple_schema: dict):

    correct_response = {"response": {"name": "John Doe", "email": "john.doe@email.com"}}

    assert adapter._check_against_schema(simple_schema, correct_response)


def test_incorrect_nested_response(
    adapter: InstantAPIMarqoAdapter, simple_schema: dict
):
    wrong_nested_response = {"name": "John Doe", "email": "john.doe@email.com"}

    assert not adapter._check_against_schema(simple_schema, wrong_nested_response)


def test_missing_key_in_response(adapter: InstantAPIMarqoAdapter, simple_schema: dict):
    missing_key_response = {"response": {"name": "John Doe"}}

    assert not adapter._check_against_schema(simple_schema, missing_key_response)


def test_extra_key_in_response(adapter: InstantAPIMarqoAdapter, simple_schema: dict):
    extra_key_response = {
        "response": {"name": "John Doe", "email": "john.doe@email.com", "age": 30}
    }

    assert not adapter._check_against_schema(simple_schema, extra_key_response)


def test_extra_nesting_in_response(
    adapter: InstantAPIMarqoAdapter, simple_schema: dict
):
    extra_nesting_response = {
        "response": {
            "name": "John Doe",
            "email": {"domain": "email.com", "username": "john.doe"},
        }
    }
    # we can't enforce the type of the value in the schema for how it is returned, Marqo will error here in practice
    assert adapter._check_against_schema(simple_schema, extra_nesting_response)


def test_marqo_schema_validator(
    adapter: InstantAPIMarqoAdapter, simple_schema: dict, simple_flat_schema: dict
):
    assert adapter._check_schema_for_marqo(simple_flat_schema) == None

    with pytest.raises(ValueError):
        adapter._check_schema_for_marqo(simple_schema)
