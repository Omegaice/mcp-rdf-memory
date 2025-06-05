"""
Tests for the quads_for_pattern tool.
"""

import json

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import TextContent

from mcp_rdf_memory.server import QuadResult


@pytest.mark.asyncio
async def test_quads_for_pattern_tool_available(client: Client) -> None:
    """Test that quads_for_pattern tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "quads_for_pattern" in tool_names


@pytest.mark.asyncio
async def test_quads_for_pattern_find_by_subject(client: Client) -> None:
    """Test finding quads by subject pattern."""
    # First add a triple
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/bob",
                    "predicate": "http://schema.org/name",
                    "object": "Bob Smith",
                }
            ]
        },
    )

    # Find quads with specific subject
    result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/person/bob"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)

    # Parse JSON response into Pydantic models
    quads_data = json.loads(result[0].text)
    quads = [QuadResult(**quad) for quad in quads_data]

    assert len(quads) == 1
    assert quads[0].subject == "<http://example.org/person/bob>"
    assert quads[0].predicate == "<http://schema.org/name>"
    assert '"Bob Smith"' in quads[0].object
    assert quads[0].graph == "default graph"


@pytest.mark.asyncio
async def test_quads_for_pattern_find_by_predicate(client: Client) -> None:
    """Test finding quads by predicate pattern."""
    # Add multiple triples with same predicate
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/charlie",
                    "predicate": "http://schema.org/email",
                    "object": "charlie@example.com",
                },
                {
                    "subject": "http://example.org/person/diana",
                    "predicate": "http://schema.org/email",
                    "object": "diana@example.com",
                },
            ]
        },
    )

    # Find all email triples
    result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/email"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "charlie@example.com" in result[0].text
    assert "diana@example.com" in result[0].text


@pytest.mark.asyncio
async def test_quads_for_pattern_with_named_graph(client: Client, sample_graph_uri: str) -> None:
    """Test finding quads in a specific named graph."""
    # Add triple to specific graph
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/eve",
                    "predicate": "http://schema.org/name",
                    "object": "Eve Johnson",
                    "graph": sample_graph_uri,
                }
            ]
        },
    )

    # Find quads in specific graph
    result = await client.call_tool("quads_for_pattern", {"graph": sample_graph_uri})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Eve Johnson" in result[0].text
    assert sample_graph_uri in result[0].text


@pytest.mark.asyncio
async def test_quads_for_pattern_wildcard_search(client: Client) -> None:
    """Test finding all quads with wildcard pattern."""
    # Add a test triple
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {"subject": "http://example.org/person/frank", "predicate": "http://schema.org/age", "object": "30"}
            ]
        },
    )

    # Find all quads (no pattern specified)
    result = await client.call_tool("quads_for_pattern", {})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    # Should contain multiple results from previous tests
    assert "frank" in result[0].text.lower()


@pytest.mark.asyncio
async def test_quads_for_pattern_no_matches(client: Client) -> None:
    """Test pattern that matches no quads."""
    # Search for non-existent subject
    result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/person/nonexistent"})

    # No matches returns empty list
    assert len(result) == 0


@pytest.mark.asyncio
async def test_quads_for_pattern_invalid_identifiers(client: Client) -> None:
    """Test that invalid identifiers in pattern queries raise errors."""
    with pytest.raises(ToolError):
        await client.call_tool("quads_for_pattern", {"subject": ""})  # Empty string

    with pytest.raises(ToolError):
        await client.call_tool("quads_for_pattern", {"predicate": "   "})  # Whitespace only


@pytest.mark.asyncio
async def test_quads_for_pattern_all_none(client: Client) -> None:
    """Test pattern query with all None values (wildcard)."""
    result = await client.call_tool("quads_for_pattern", {})
    # Should not raise error, may return empty or existing data
    assert isinstance(result, list)
