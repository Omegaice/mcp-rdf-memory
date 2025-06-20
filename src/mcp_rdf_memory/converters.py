"""
RDF type conversion functionality.

This module provides functions for converting string values into appropriate
RDF node types (NamedNode, Literal) and creating graph URIs. These converters
handle the logic for determining when to create identifiers vs literals and
manage the MCP namespace for graph names.

The conversion strategies are:
- Try NamedNode creation first for potential identifiers
- Fall back to Literal for non-URI strings
- Handle graph name to URI conversion with proper validation
"""

from fastmcp.exceptions import ToolError
from pyoxigraph import Literal, NamedNode

# Constants
MCP_NAMESPACE = "http://mcp.local/"


def create_rdf_node(value: str) -> NamedNode | Literal:
    """Convert validated string to appropriate RDF node type.

    Attempts to create a NamedNode first (for URIs, CURIEs, etc.),
    and falls back to creating a Literal if the string cannot be
    used as an identifier.

    Args:
        value: The string value to convert

    Returns:
        NamedNode if the value can be used as an identifier,
        Literal otherwise

    Examples:
        >>> create_rdf_node("http://example.org/test")
        NamedNode('http://example.org/test')
        >>> create_rdf_node("plain text")
        Literal('plain text')
        >>> create_rdf_node("rdf:type")
        NamedNode('rdf:type')
    """
    try:
        return NamedNode(value)  # Try as identifier first
    except ValueError:
        return Literal(value)  # Fall back to literal


def create_graph_uri(graph_name: str | None) -> NamedNode | None:
    """Convert simple graph name to namespaced URI.

    Creates a NamedNode with the MCP namespace for non-empty graph names.
    Returns None for None or empty string inputs (indicating default graph).
    Raises error for whitespace-only names which are invalid.

    Args:
        graph_name: The graph name to convert, or None for default graph

    Returns:
        NamedNode with MCP namespace URI for valid names,
        None for None or empty string (default graph)

    Raises:
        ToolError: If graph_name is whitespace-only

    Examples:
        >>> create_graph_uri("test-graph")
        NamedNode('http://mcp.local/test-graph')
        >>> create_graph_uri("conversation/chat-123")
        NamedNode('http://mcp.local/conversation/chat-123')
        >>> create_graph_uri(None)
        None
        >>> create_graph_uri("")
        None
        >>> create_graph_uri("   ")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ToolError: Graph name cannot be whitespace-only
    """
    if graph_name is None or graph_name == "":
        return None

    if not graph_name.strip():
        raise ToolError("Graph name cannot be whitespace-only")

    return NamedNode(f"{MCP_NAMESPACE}{graph_name.strip()}")
