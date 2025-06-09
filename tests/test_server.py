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
    expected_tools = ["rdf_add_triples", "rdf_find_triples", "rdf_sparql_query"]
    for tool in expected_tools:
        assert tool in tool_names
