"""Improved tests for create_rdf_node function following pytest best practices."""

import pytest
from pyoxigraph import Literal, NamedNode

from mcp_rdf_memory.converters import create_rdf_node

# Test data organized as module-level constants for better readability
VALID_URIS = [
    "http://example.org/test",
    "https://schema.org/Person",
    "ftp://files.example.com/data",
    "mailto:user@example.com",
    "file:///path/to/file",
    "urn:uuid:12345-67890",
    "urn:isbn:0451450523",
]

VALID_CURIES = [
    "rdf:type",
    "rdfs:label",
    "foaf:Person",
    "schema:name",
    "dc:title",
    "owl:Class",
]

LITERAL_STRINGS = [
    "plain text",
    "Text with spaces",
    "123456",
    "Mixed text and 123 numbers",
    "Special chars: !@#$%^&*()",
    "Unicode: café, naïve, 中文",
    "Line\nbreaks\nand\ttabs",
]


# Fixtures for reusable test data
@pytest.fixture
def whitespace_strings():
    """Provide various whitespace-only strings."""
    return ["   ", "\t", "\n", "\r\n", "  \t  \n  "]


@pytest.fixture
def numeric_strings():
    """Provide various numeric string formats."""
    return ["123", "456.789", "-42", "1.23e-4", "0"]


# Better parametrization with descriptive IDs
@pytest.mark.parametrize("uri", VALID_URIS, ids=lambda x: f"uri_{x.split('://')[0]}")
def test_creates_named_node_for_valid_uris(uri: str) -> None:
    """Valid URIs should create NamedNode objects."""
    result = create_rdf_node(uri)

    assert isinstance(result, NamedNode)
    assert result.value == uri


@pytest.mark.parametrize("curie", VALID_CURIES, ids=lambda x: x.replace(":", "_"))
def test_creates_named_node_for_curies(curie: str) -> None:
    """CURIE strings should create NamedNode objects."""
    result = create_rdf_node(curie)

    assert isinstance(result, NamedNode)
    assert result.value == curie


@pytest.mark.parametrize("text", LITERAL_STRINGS, ids=lambda x: x[:20].replace(" ", "_"))
def test_creates_literal_for_text_strings(text: str) -> None:
    """Non-URI text strings should create Literal objects."""
    result = create_rdf_node(text)

    assert isinstance(result, Literal)
    assert result.value == text


def test_creates_literal_for_empty_string() -> None:
    """Empty string should create a Literal."""
    result = create_rdf_node("")

    assert isinstance(result, Literal)
    assert result.value == ""


def test_creates_literal_for_whitespace_strings(whitespace_strings) -> None:
    """Whitespace-only strings should create Literals."""
    for ws_string in whitespace_strings:
        result = create_rdf_node(ws_string)

        assert isinstance(result, Literal)
        assert result.value == ws_string


def test_creates_literal_for_numeric_strings(numeric_strings) -> None:
    """Numeric strings should create Literals."""
    for num_string in numeric_strings:
        result = create_rdf_node(num_string)

        assert isinstance(result, Literal)
        assert result.value == num_string


# Better use of pytest.param with descriptive IDs
@pytest.mark.parametrize(
    "test_input,expected_type",
    [
        pytest.param("http://example.org#fragment", NamedNode, id="uri_with_fragment"),
        pytest.param("https://api.example.com/data?format=json", NamedNode, id="uri_with_query"),
        pytest.param("localhost:8080", NamedNode, id="localhost_port"),
        pytest.param("scheme:", NamedNode, id="scheme_only"),
        pytest.param("true", Literal, id="boolean_string"),
        pytest.param("123", Literal, id="numeric_string"),
    ],
)
def test_node_type_determination_for_edge_cases(test_input: str, expected_type) -> None:
    """Node type should be determined correctly for edge cases."""
    result = create_rdf_node(test_input)
    assert isinstance(result, expected_type)


def test_preserves_input_value_exactly() -> None:
    """The created node should preserve the exact input value."""
    test_cases = [
        "http://example.org/test",
        "plain text with spaces",
        "unicode: 中文",
        "",
        "  whitespace  ",
    ]

    for test_input in test_cases:
        result = create_rdf_node(test_input)
        assert result.value == test_input


def test_handles_very_long_strings() -> None:
    """Should handle very long input strings."""
    long_string = "a" * 10000
    result = create_rdf_node(long_string)

    assert result.value == long_string


def test_handles_special_unicode_characters() -> None:
    """Should handle special Unicode characters correctly."""
    unicode_cases = [
        "emoji😀text",
        "combining_á_characters",
        "null\x00byte",
        "control\x1fcharacter",
    ]

    for unicode_str in unicode_cases:
        result = create_rdf_node(unicode_str)
        assert result.value == unicode_str


@pytest.mark.parametrize("protocol", ["http", "https", "ftp", "file", "mailto", "urn"], ids=lambda x: f"protocol_{x}")
def test_recognizes_various_uri_protocols(protocol: str) -> None:
    """Should recognize various URI protocols as NamedNodes."""
    uri = f"{protocol}://example.com/test"
    result = create_rdf_node(uri)

    assert isinstance(result, NamedNode)
    assert result.value == uri
