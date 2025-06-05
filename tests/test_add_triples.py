"""
Tests for the add_triples tool.
"""

import pytest
from fastmcp.exceptions import ToolError
from mcp.types import TextContent


@pytest.mark.asyncio
async def test_add_triples_tool_available(client):
    """Test that add_triples tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "add_triples" in tool_names


@pytest.mark.asyncio
async def test_add_simple_triple(client):
    """Test adding a basic RDF triple."""
    result = await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/john",
            "predicate": "http://schema.org/name", 
            "object": "John Doe"
        }]
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "success" in result[0].text.lower()


@pytest.mark.asyncio  
async def test_add_triple_with_named_graph(client, sample_graph_uri):
    """Test adding a triple to a specific named graph context."""
    result = await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/alice",
            "predicate": "http://schema.org/name",
            "object": "Alice Smith",
            "graph": sample_graph_uri
        }]
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_add_triple_with_uri_object(client):
    """Test adding a triple where the object is also a URI."""
    result = await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/john",
            "predicate": "http://xmlns.com/foaf/0.1/knows",
            "object": "http://example.org/person/alice"
        }]
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent) 
    assert "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_add_multiple_triples(client):
    """Test adding multiple triples in a single call."""
    result = await client.call_tool("add_triples", {
        "triples": [
            {
                "subject": "http://example.org/person/multi1",
                "predicate": "http://schema.org/name", 
                "object": "Person One"
            },
            {
                "subject": "http://example.org/person/multi2",
                "predicate": "http://schema.org/name", 
                "object": "Person Two"
            },
            {
                "subject": "http://example.org/person/multi1",
                "predicate": "http://xmlns.com/foaf/0.1/knows", 
                "object": "http://example.org/person/multi2"
            }
        ]
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "success" in result[0].text.lower()
    assert "3 triple(s)" in result[0].text


@pytest.mark.asyncio
async def test_add_triple_validation_error(client):
    """Test that invalid URIs are properly validated."""
    with pytest.raises(ToolError):  # Should raise ToolError via FastMCP
        await client.call_tool("add_triples", {
            "triples": [{
                "subject": "not-a-valid-uri",
                "predicate": "http://schema.org/name", 
                "object": "John Doe"
            }]
        })