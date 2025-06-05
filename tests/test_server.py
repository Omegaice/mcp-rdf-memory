"""
Tests for the MCP RDF Memory server.
"""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import TextContent

from mcp_rdf_memory.server import mcp


@pytest.mark.asyncio
async def test_server_tools_available():
    """Test that the server has the expected tools."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "hello_world" in tool_names


@pytest.mark.asyncio
async def test_hello_world_tool():
    """Test the hello_world tool functionality."""
    async with Client(mcp) as client:
        # Test with default parameter
        result = await client.call_tool("hello_world", {})
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Hello, World!" in result[0].text
        assert "RDF Memory server" in result[0].text
        
        # Test with custom name
        result = await client.call_tool("hello_world", {"name": "Alice"})
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Hello, Alice!" in result[0].text
        assert "RDF Memory server" in result[0].text


@pytest.mark.asyncio
async def test_server_info():
    """Test server basic info."""
    async with Client(mcp) as client:
        # Verify server is responding
        tools = await client.list_tools()
        assert isinstance(tools, list)
        
        # Check that we have at least one tool
        assert len(tools) > 0


@pytest.mark.asyncio
async def test_add_triple_tool_available():
    """Test that add_triple tool is available."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "add_triple" in tool_names


@pytest.mark.asyncio
async def test_add_simple_triple():
    """Test adding a basic RDF triple."""
    async with Client(mcp) as client:
        # Add a simple person-name triple
        result = await client.call_tool("add_triple", {
            "subject": "http://example.org/person/john",
            "predicate": "http://schema.org/name", 
            "object": "John Doe"
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "success" in result[0].text.lower()


@pytest.mark.asyncio  
async def test_add_triple_with_named_graph():
    """Test adding a triple to a specific named graph context."""
    async with Client(mcp) as client:
        # Add triple to conversation context
        conversation_id = "conv-123"
        graph_uri = f"http://mcp.local/conversation/{conversation_id}"
        
        result = await client.call_tool("add_triple", {
            "subject": "http://example.org/person/alice",
            "predicate": "http://schema.org/name",
            "object": "Alice Smith",
            "graph": graph_uri
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_add_triple_with_uri_object():
    """Test adding a triple where the object is also a URI."""
    async with Client(mcp) as client:
        # Add a relationship between two people
        result = await client.call_tool("add_triple", {
            "subject": "http://example.org/person/john",
            "predicate": "http://xmlns.com/foaf/0.1/knows",
            "object": "http://example.org/person/alice"
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent) 
        assert "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_add_triple_validation_error():
    """Test that invalid URIs are properly validated."""
    async with Client(mcp) as client:
        # Try to add triple with invalid subject URI
        with pytest.raises(ToolError):  # Should raise ToolError via FastMCP
            await client.call_tool("add_triple", {
                "subject": "not-a-valid-uri",
                "predicate": "http://schema.org/name", 
                "object": "John Doe"
            })