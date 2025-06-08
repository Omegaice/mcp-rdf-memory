"""
Unit tests for helper functions with complex logic.

Tests focused on business logic we wrote, not framework behavior.
Following testing documentation principles for meaningful unit tests.
"""

import pytest
from fastmcp.exceptions import ToolError
from pyoxigraph import NamedNode

from mcp_rdf_memory.server import (
    create_graph_uri,
)


class TestCreateGraphUri:
    """Unit tests for create_graph_uri() function."""

    def test_none_input_returns_none(self) -> None:
        """Test that None input returns None (for default graph)."""
        result = create_graph_uri(None)
        assert result is None

    def test_valid_graph_name_creates_named_node(self) -> None:
        """Test that valid graph names create NamedNode with correct URI."""
        result = create_graph_uri("test-graph")
        assert isinstance(result, NamedNode)
        assert result.value == "http://mcp.local/test-graph"

    def test_graph_name_with_slashes_preserves_structure(self) -> None:
        """Test that slash-separated names create hierarchical URIs."""
        result = create_graph_uri("conversation/chat-123")
        assert isinstance(result, NamedNode)
        assert result.value == "http://mcp.local/conversation/chat-123"

        result = create_graph_uri("project/myapp/data")
        assert isinstance(result, NamedNode)
        assert result.value == "http://mcp.local/project/myapp/data"

    def test_whitespace_trimming(self) -> None:
        """Test that leading/trailing whitespace is trimmed."""
        test_cases = [
            ("  test-graph  ", "http://mcp.local/test-graph"),
            ("\ttest-graph\t", "http://mcp.local/test-graph"),
            ("\n test-graph \n", "http://mcp.local/test-graph"),
            ("   conversation/chat-123   ", "http://mcp.local/conversation/chat-123"),
        ]

        for input_name, expected_uri in test_cases:
            result = create_graph_uri(input_name)
            assert isinstance(result, NamedNode)
            assert result.value == expected_uri

    def test_empty_string_raises_tool_error(self) -> None:
        """Test that empty string raises ToolError with helpful message."""
        with pytest.raises(ToolError) as exc_info:
            create_graph_uri("")

        error_msg = str(exc_info.value)
        assert "empty" in error_msg.lower()
        assert "graph name" in error_msg.lower()

    def test_whitespace_only_raises_tool_error(self) -> None:
        """Test that whitespace-only strings raise ToolError."""
        whitespace_cases = [
            "   ",      # spaces
            "\t\t",    # tabs
            "\n\n",    # newlines
            " \t\n ",  # mixed whitespace
        ]

        for whitespace_input in whitespace_cases:
            with pytest.raises(ToolError) as exc_info:
                create_graph_uri(whitespace_input)

            error_msg = str(exc_info.value)
            assert "empty" in error_msg.lower()
            assert "graph name" in error_msg.lower()

    def test_special_characters_in_graph_names(self) -> None:
        """Test graph names with special characters are handled correctly."""
        # These should work - valid URI path components
        valid_cases = [
            ("test-graph_123", "http://mcp.local/test-graph_123"),
            ("user@domain", "http://mcp.local/user@domain"),
            ("session.2024-01-01", "http://mcp.local/session.2024-01-01"),
        ]

        for input_name, expected_uri in valid_cases:
            result = create_graph_uri(input_name)
            assert isinstance(result, NamedNode)
            assert result.value == expected_uri

    def test_unicode_in_graph_names(self) -> None:
        """Test that Unicode characters in graph names are preserved."""
        unicode_cases = [
            ("测试图", "http://mcp.local/测试图"),
            ("café-graph", "http://mcp.local/café-graph"),
            ("🌍-global", "http://mcp.local/🌍-global"),
        ]

        for input_name, expected_uri in unicode_cases:
            result = create_graph_uri(input_name)
            assert isinstance(result, NamedNode)
            assert result.value == expected_uri

    def test_very_long_graph_names(self) -> None:
        """Test that very long graph names are handled correctly."""
        long_name = "very-long-graph-name-" + "x" * 1000
        result = create_graph_uri(long_name)
        assert isinstance(result, NamedNode)
        assert result.value == f"http://mcp.local/{long_name}"


