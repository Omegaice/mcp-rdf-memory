"""Improved tests for create_graph_uri function following pytest best practices."""

import pytest
from fastmcp.exceptions import ToolError
from pyoxigraph import NamedNode

from mcp_rdf_memory.converters import create_graph_uri

# Test data as module constants for better organization
VALID_SIMPLE_NAMES = [
    "test-graph",
    "conversation",
    "project",
    "data123",
    "graph_with_underscore",
    "CamelCaseGraph",
]

HIERARCHICAL_NAMES = [
    "conversation/chat-123",
    "project/myapp",
    "users/alice/data",
    "path/with/multiple/slashes",
]

WHITESPACE_ONLY_STRINGS = [" ", "  ", "\t", "\n", "\r", "\r\n", "   \t  ", "\t\n  \r  \n\t"]


# Fixtures for reusable test data
@pytest.fixture
def expected_namespace():
    """Provide the expected MCP namespace."""
    return "http://mcp.local/"


@pytest.fixture
def trimming_test_cases():
    """Provide test cases for whitespace trimming."""
    return [
        ("  test-graph  ", "test-graph"),
        ("\tconversation\t", "conversation"),
        ("\nproject\n", "project"),
        ("   conversation/chat-123   ", "conversation/chat-123"),
        ("\t\n  mixed-whitespace  \n\t", "mixed-whitespace"),
    ]


# Default behavior tests
def test_none_input_returns_none() -> None:
    """None input should return None for default graph."""
    result = create_graph_uri(None)
    assert result is None


def test_empty_string_returns_none() -> None:
    """Empty string should return None for default graph."""
    result = create_graph_uri("")
    assert result is None


# Valid URI creation tests
@pytest.mark.parametrize("name", VALID_SIMPLE_NAMES, ids=lambda x: f"simple_{x}")
def test_creates_named_node_for_valid_names(name: str, expected_namespace: str) -> None:
    """Valid graph names should create NamedNode with correct URI."""
    result = create_graph_uri(name)

    assert isinstance(result, NamedNode)
    assert result.value == f"{expected_namespace}{name}"


@pytest.mark.parametrize("name", HIERARCHICAL_NAMES, ids=lambda x: f"hierarchical_{x.replace('/', '_')}")
def test_creates_hierarchical_uris(name: str, expected_namespace: str) -> None:
    """Hierarchical names should create properly structured URIs."""
    result = create_graph_uri(name)

    assert isinstance(result, NamedNode)
    assert result.value == f"{expected_namespace}{name}"
    assert "/" in result.value  # Verify hierarchy is preserved


def test_trims_whitespace_from_input(trimming_test_cases, expected_namespace: str) -> None:
    """Leading and trailing whitespace should be trimmed."""
    for input_name, expected_clean_name in trimming_test_cases:
        result = create_graph_uri(input_name)

        assert isinstance(result, NamedNode)
        assert result.value == f"{expected_namespace}{expected_clean_name}"


def test_preserves_valid_special_characters(expected_namespace: str) -> None:
    """Valid special characters should be preserved in URIs."""
    valid_names = [
        "graph-with-dashes",
        "graph_with_underscores",
        "graph123with456numbers",
        "graph.with.dots",
    ]

    for name in valid_names:
        result = create_graph_uri(name)

        assert isinstance(result, NamedNode)
        assert result.value == f"{expected_namespace}{name}"


# Validation and error handling tests
@pytest.mark.parametrize("whitespace_name", WHITESPACE_ONLY_STRINGS, ids=lambda x: f"whitespace_{x!r}")
def test_rejects_whitespace_only_names(whitespace_name: str) -> None:
    """Whitespace-only names should raise ToolError."""
    with pytest.raises(ToolError) as exc_info:
        create_graph_uri(whitespace_name)

    assert "Graph name cannot be whitespace-only" in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_name",
    [
        pytest.param("graph#with#hashes", id="contains_hash"),
        pytest.param("graph with spaces", id="contains_spaces"),
        pytest.param("graph<with>brackets", id="contains_brackets"),
        pytest.param('graph"with"quotes', id="contains_quotes"),
    ],
)
def test_rejects_invalid_iri_characters(invalid_name: str) -> None:
    """Names with invalid IRI characters should raise ValueError."""
    with pytest.raises(ValueError):
        create_graph_uri(invalid_name)


def test_error_message_is_descriptive() -> None:
    """Error messages should be clear and helpful."""
    with pytest.raises(ToolError) as exc_info:
        create_graph_uri("   ")

    error_message = str(exc_info.value)
    assert "Graph name" in error_message
    assert "whitespace-only" in error_message


# Consistency and edge case tests
def test_namespace_consistency(expected_namespace: str) -> None:
    """All generated URIs should use consistent namespace."""
    test_names = ["test1", "test2", "conversation/chat1", "project/app"]

    for name in test_names:
        result = create_graph_uri(name)

        assert isinstance(result, NamedNode)
        assert result.value.startswith(expected_namespace)
        assert result.value.endswith(name)


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("a", id="single_character"),
        pytest.param("123", id="purely_numeric"),
        pytest.param("graph.with.many.dots", id="many_dots"),
        pytest.param("very-long-graph-name-with-many-components", id="very_long"),
    ],
)
def test_handles_edge_case_valid_names(name: str, expected_namespace: str) -> None:
    """Edge case valid names should be handled correctly."""
    result = create_graph_uri(name)

    assert isinstance(result, NamedNode)
    assert result.value == f"{expected_namespace}{name}"


def test_unicode_support(expected_namespace: str) -> None:
    """Unicode characters should be supported in graph names."""
    unicode_names = [
        "café-graph",
        "naïve-data",
        "中文图表",
        "русский-граф",
    ]

    for name in unicode_names:
        result = create_graph_uri(name)

        assert isinstance(result, NamedNode)
        assert result.value == f"{expected_namespace}{name}"


def test_returns_none_vs_named_node_distinction() -> None:
    """Clear distinction between None returns and NamedNode returns."""
    # Cases that return None
    none_cases = [None, ""]
    for case in none_cases:
        assert create_graph_uri(case) is None

    # Cases that return NamedNode
    valid_cases = ["test", " test ", "a"]
    for case in valid_cases:
        result = create_graph_uri(case)
        assert isinstance(result, NamedNode)
        assert result is not None
