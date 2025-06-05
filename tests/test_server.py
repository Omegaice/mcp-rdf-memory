"""
Tests for the MCP RDF Memory server.
"""

import pytest
from fastmcp import Client
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