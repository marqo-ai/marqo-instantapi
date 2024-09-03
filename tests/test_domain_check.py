import pytest
from unittest.mock import patch, MagicMock
from marqo_instantapi import InstantAPIMarqoAdapter


@pytest.fixture
def adapter():
    return InstantAPIMarqoAdapter()


def test_valid_domains(adapter: InstantAPIMarqoAdapter):
    domains = [
        "https://www.google.com",
        "https://www.facebook.com",
        "https://www.twitter.com",
        "https://www.linkedin.com/profile/53542",
        "https://ww2.thisisadomain.io/route/search?query=hello",
    ]

    for domain in domains:
        root = adapter._get_root_domain(domain)
        assert root in domain
        assert "https://" not in root
        assert "http://" not in root
        assert "/" not in root

    assert adapter._get_root_domain("https://www.google.com") == "www.google.com"
    assert (
        adapter._get_root_domain(
            "https://ww2.thisisadomain.io/route/search?query=hello"
        )
        == "ww2.thisisadomain.io"
    )


def test_strange_domains(adapter: InstantAPIMarqoAdapter):
    assert adapter._get_root_domain("thisisnotadomain") == ".thisisnotadomain."
    assert adapter._get_root_domain("localhost") == ".localhost."
    assert adapter._get_root_domain("localhost:8080") == ".localhost."
