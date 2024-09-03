import pytest
from marqo_instantapi import InstantAPIMarqoAdapter


@pytest.fixture
def adapter() -> InstantAPIMarqoAdapter:
    return InstantAPIMarqoAdapter()


def test_mappings_one_text(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=["title"],
        image_fields_to_index=[],
        total_image_weight=0,
        total_text_weight=1,
    )
    assert mappings == None
    assert fields == ["title"]


def test_mappings_one_image(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=[],
        image_fields_to_index=["image"],
        total_image_weight=1,
        total_text_weight=0,
    )
    assert mappings == None
    assert fields == ["image"]


def text_mappings_many_text(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=["title", "description"],
        image_fields_to_index=[],
        total_image_weight=0,
        total_text_weight=1,
    )
    assert mappings == None
    assert fields == ["title", "description"]


def test_mappings_many_image(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=[],
        image_fields_to_index=["image", "thumbnail"],
        total_image_weight=1,
        total_text_weight=0,
    )
    assert mappings == None
    assert fields == ["image", "thumbnail"]


def test_mappings_one_text_one_image(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=["title"],
        image_fields_to_index=["image"],
        total_image_weight=0.5,
        total_text_weight=0.5,
    )
    assert len(mappings[adapter.combination_field]["weights"]) == 2
    assert mappings[adapter.combination_field]["weights"]["title"] == 0.5
    assert mappings[adapter.combination_field]["weights"]["image"] == 0.5
    assert fields == [adapter.combination_field]


def test_mappings_many_text_one_image(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=["title", "description"],
        image_fields_to_index=["image"],
        total_image_weight=0.9,
        total_text_weight=0.1,
    )
    assert len(mappings[adapter.combination_field]["weights"]) == 3
    assert mappings[adapter.combination_field]["weights"]["title"] == 0.05
    assert mappings[adapter.combination_field]["weights"]["description"] == 0.05
    assert mappings[adapter.combination_field]["weights"]["image"] == 0.9
    assert fields == [adapter.combination_field]


def test_mappings_one_text_many_image(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=["title"],
        image_fields_to_index=["image", "thumbnail"],
        total_image_weight=0.9,
        total_text_weight=0.1,
    )
    assert len(mappings[adapter.combination_field]["weights"]) == 3
    assert mappings[adapter.combination_field]["weights"]["title"] == 0.1
    assert mappings[adapter.combination_field]["weights"]["image"] == 0.45
    assert mappings[adapter.combination_field]["weights"]["thumbnail"] == 0.45
    assert fields == [adapter.combination_field]


def test_mappings_many_text_many_image(adapter: InstantAPIMarqoAdapter):
    mappings, fields = adapter._make_mappings(
        text_fields_to_index=["title", "description"],
        image_fields_to_index=["image", "thumbnail"],
        total_image_weight=0.9,
        total_text_weight=0.1,
    )
    assert len(mappings[adapter.combination_field]["weights"]) == 4
    assert mappings[adapter.combination_field]["weights"]["title"] == 0.05
    assert mappings[adapter.combination_field]["weights"]["description"] == 0.05
    assert mappings[adapter.combination_field]["weights"]["image"] == 0.45
    assert mappings[adapter.combination_field]["weights"]["thumbnail"] == 0.45
    assert fields == [adapter.combination_field]
