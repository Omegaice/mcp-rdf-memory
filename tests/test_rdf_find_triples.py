"""
Tests for the rdf_find_triples tool.
"""

import json

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import TextContent

from mcp_rdf_memory.server import QuadResult


@pytest.mark.asyncio
async def test_rdf_find_triples_tool_available(client: Client) -> None:
    """Test that rdf_find_triples tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "rdf_find_triples" in tool_names


@pytest.mark.asyncio
async def test_rdf_find_triples_find_by_subject(client: Client) -> None:
    """Test finding quads by subject pattern."""
    # First add a triple with unique subject
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/find_test_subject",
                    "predicate": "http://schema.org/name",
                    "object": "Find Test Subject",
                }
            ]
        },
    )

    # Find quads with specific subject
    result = await client.call_tool("rdf_find_triples", {"subject": "http://example.org/person/find_test_subject"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)

    # Validate JSON structure before reconstruction
    quads_data = json.loads(result[0].text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)

    # Validate required fields exist in JSON
    for item in quads_data:
        assert "subject" in item
        assert "predicate" in item
        assert "object" in item
        assert "graph" in item
        assert isinstance(item["subject"], str)
        assert isinstance(item["predicate"], str)
        assert isinstance(item["object"], str)
        assert isinstance(item["graph"], str)

    # Then reconstruct and verify content
    quads = [QuadResult(**quad) for quad in quads_data]
    assert len(quads) == 1
    assert quads[0].subject == "<http://example.org/person/find_test_subject>"
    assert quads[0].predicate == "<http://schema.org/name>"
    assert '"Find Test Subject"' in quads[0].object
    assert quads[0].graph == "default graph"


@pytest.mark.asyncio
async def test_rdf_find_triples_find_by_predicate(client: Client) -> None:
    """Test finding quads by predicate pattern."""
    # Add multiple triples with same predicate
    await client.call_tool(
        "rdf_add_triples",
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

    # Find all email triples with JSON validation
    result = await client.call_tool("rdf_find_triples", {"predicate": "http://schema.org/email"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)

    # Validate JSON structure
    quads_data = json.loads(result[0].text)
    assert isinstance(quads_data, list)
    assert len(quads_data) >= 2  # Should have both email triples
    assert all(isinstance(item, dict) for item in quads_data)

    # Validate schema
    for item in quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])

    # Verify content exists in raw text
    assert "charlie@example.com" in result[0].text
    assert "diana@example.com" in result[0].text


@pytest.mark.asyncio
async def test_rdf_find_triples_with_named_graph(client: Client, sample_graph_uri: str) -> None:
    """Test finding quads in a specific named graph."""
    # Add triple to specific graph
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/eve",
                    "predicate": "http://schema.org/name",
                    "object": "Eve Johnson",
                    "graph_name": "conversation/test-123",
                }
            ]
        },
    )

    # Find quads in specific graph
    result = await client.call_tool("rdf_find_triples", {"graph_name": "conversation/test-123"})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Eve Johnson" in result[0].text
    assert sample_graph_uri in result[0].text


@pytest.mark.asyncio
async def test_rdf_find_triples_wildcard_search(client: Client) -> None:
    """Test finding all quads with wildcard pattern."""
    # Add a test triple
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {"subject": "http://example.org/person/frank", "predicate": "http://schema.org/age", "object": "30"}
            ]
        },
    )

    # Find all quads (no pattern specified)
    result = await client.call_tool("rdf_find_triples", {})

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    # Should contain multiple results from previous tests
    assert "frank" in result[0].text.lower()


@pytest.mark.asyncio
async def test_rdf_find_triples_no_matches(client: Client) -> None:
    """Test pattern that matches no quads."""
    # Search for non-existent subject
    result = await client.call_tool("rdf_find_triples", {"subject": "http://example.org/person/nonexistent"})

    # No matches returns empty JSON array (wrapped in TextContent)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)

    # Validate JSON structure
    quads_data = json.loads(result[0].text)
    assert isinstance(quads_data, list)
    assert len(quads_data) == 0
    assert quads_data == []


@pytest.mark.asyncio
async def test_rdf_find_triples_invalid_identifiers(client: Client) -> None:
    """Test that invalid identifiers in pattern queries raise errors."""
    with pytest.raises(ToolError):
        await client.call_tool("rdf_find_triples", {"subject": ""})  # Empty string

    with pytest.raises(ToolError):
        await client.call_tool("rdf_find_triples", {"predicate": "   "})  # Whitespace only


@pytest.mark.asyncio
async def test_rdf_find_triples_all_none(client: Client) -> None:
    """Test pattern query with all None values (wildcard)."""
    result = await client.call_tool("rdf_find_triples", {})
    # Should not raise error, may return empty or existing data
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_rdf_find_triples_unicode_data(client: Client) -> None:
    """Test pattern matching with Unicode and special characters."""
    # Add triple with Unicode content
    unicode_data = {
        "subject": "http://example.org/unicode/测试",
        "predicate": "http://schema.org/name",
        "object": "Unicode Name: 世界 🌍 àáâãäå",
    }

    await client.call_tool("rdf_add_triples", {"triples": [unicode_data]})

    # Find by Unicode subject
    result = await client.call_tool("rdf_find_triples", {"subject": unicode_data["subject"]})

    assert len(result) == 1
    content = result[0]
    assert isinstance(content, TextContent)

    # Validate JSON structure
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert len(quads_data) == 1

    quad = quads_data[0]
    assert isinstance(quad, dict)
    assert all(field in quad for field in ["subject", "predicate", "object", "graph"])

    # Verify Unicode preservation
    assert unicode_data["subject"] in quad["subject"]
    assert "世界" in quad["object"]
    assert "🌍" in quad["object"]
    assert "àáâãäå" in quad["object"]
