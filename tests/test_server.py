"""
General server tests - basic functionality and integration.
"""

import pytest
from fastmcp import Client


@pytest.mark.asyncio
async def test_server_tools_available(client: Client) -> None:
    """Test that the server has the expected tools."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]

    # Check all expected tools are present
    expected_tools = ["add_triples", "quads_for_pattern", "rdf_query"]
    for tool in expected_tools:
        assert tool in tool_names


@pytest.mark.asyncio
async def test_server_info(client: Client) -> None:
    """Test server basic info."""
    # Verify server is responding
    tools = await client.list_tools()
    assert isinstance(tools, list)

    # Check that we have at least one tool
    assert len(tools) > 0
