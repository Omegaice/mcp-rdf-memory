"""Tests for RDF prefix management functionality."""

import json

import pytest
from fastmcp.client.client import Client
from mcp.types import TextResourceContents


def assert_tool_returns_empty(result) -> None:
    """Assert that tool call result is empty (tool returned None)."""
    __tracebackhide__ = True
    assert len(result) == 0


async def get_prefixes_from_resource(client: Client, uri: str) -> dict[str, str]:
    """Get prefixes from a resource URI."""
    __tracebackhide__ = True
    result = await client.read_resource(uri)
    assert len(result) == 1
    assert isinstance(result[0], TextResourceContents)
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_rdf_define_prefix_tool_available(client: Client):
    """Test that the rdf_define_prefix tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "rdf_define_prefix" in tool_names


@pytest.mark.asyncio
async def test_define_global_prefix(client: Client):
    """Test defining a global prefix."""
    result = await client.call_tool(
        "rdf_define_prefix", {"prefix": "method", "namespace_uri": "http://example.org/methods/"}
    )

    assert_tool_returns_empty(result)

    # Verify prefix was added via resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/prefix")
    assert "method" in prefixes
    assert prefixes["method"] == "http://example.org/methods/"


@pytest.mark.asyncio
async def test_define_graph_specific_prefix(client: Client):
    """Test defining a graph-specific prefix."""
    result = await client.call_tool(
        "rdf_define_prefix",
        {"prefix": "rel", "namespace_uri": "http://example.org/relations/", "graph_name": "test-graph"},
    )

    assert_tool_returns_empty(result)

    # Verify prefix was added via resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/test-graph/prefix")
    assert "rel" in prefixes
    assert prefixes["rel"] == "http://example.org/relations/"


@pytest.mark.asyncio
async def test_remove_global_prefix(client: Client):
    """Test removing a global prefix."""
    # First define a prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://example.org/test/"})

    # Then remove it
    result = await client.call_tool("rdf_define_prefix", {"prefix": "test"})

    assert_tool_returns_empty(result)

    # Verify prefix was removed via resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/prefix")
    assert "test" not in prefixes


@pytest.mark.asyncio
async def test_remove_graph_specific_prefix(client: Client):
    """Test removing a graph-specific prefix."""
    # First define a graph-specific prefix
    await client.call_tool(
        "rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://example.org/test/", "graph_name": "test-graph"}
    )

    # Then remove it
    result = await client.call_tool("rdf_define_prefix", {"prefix": "test", "graph_name": "test-graph"})

    assert_tool_returns_empty(result)

    # Verify prefix was removed via resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/test-graph/prefix")
    assert "test" not in prefixes


@pytest.mark.asyncio
async def test_remove_nonexistent_prefix(client: Client):
    """Test removing a prefix that doesn't exist."""
    result = await client.call_tool("rdf_define_prefix", {"prefix": "nonexistent"})

    # Tool returns None even when prefix doesn't exist (idempotent)
    assert_tool_returns_empty(result)


@pytest.mark.asyncio
async def test_invalid_prefix_format(client: Client):
    """Test that invalid prefix formats are rejected."""
    with pytest.raises(Exception) as exc_info:
        await client.call_tool(
            "rdf_define_prefix", {"prefix": "invalid:prefix", "namespace_uri": "http://example.org/"}
        )

    # The error should mention colons are not allowed
    error_msg = str(exc_info.value).lower()
    assert "colon" in error_msg or "invalid prefix" in error_msg


@pytest.mark.asyncio
async def test_invalid_namespace_uri(client: Client):
    """Test that invalid namespace URIs are rejected."""
    with pytest.raises(Exception) as exc_info:
        await client.call_tool("rdf_define_prefix", {"prefix": "test", "namespace_uri": "not-a-valid-uri"})

    # The error should mention invalid URI
    error_msg = str(exc_info.value)
    assert "Invalid namespace URI" in error_msg or "invalid" in error_msg.lower()


@pytest.mark.asyncio
async def test_global_prefix_resource(client: Client):
    """Test reading global prefixes via resource."""
    # Define some global prefixes
    await client.call_tool("rdf_define_prefix", {"prefix": "ex", "namespace_uri": "http://example.org/"})
    await client.call_tool("rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://test.org/"})

    # Read the global prefix resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/prefix")

    assert "ex" in prefixes
    assert "test" in prefixes
    assert prefixes["ex"] == "http://example.org/"
    assert prefixes["test"] == "http://test.org/"


@pytest.mark.asyncio
async def test_graph_specific_prefix_resource(client: Client):
    """Test reading graph-specific prefixes via resource."""
    # Define global and graph-specific prefixes
    await client.call_tool("rdf_define_prefix", {"prefix": "global", "namespace_uri": "http://global.org/"})
    await client.call_tool(
        "rdf_define_prefix", {"prefix": "local", "namespace_uri": "http://local.org/", "graph_name": "test-graph"}
    )

    # Read the graph-specific prefix resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/test-graph/prefix")

    # Should include both global and graph-specific prefixes
    assert "global" in prefixes
    assert "local" in prefixes
    assert prefixes["global"] == "http://global.org/"
    assert prefixes["local"] == "http://local.org/"


@pytest.mark.asyncio
async def test_graph_specific_prefix_overrides_global(client: Client):
    """Test that graph-specific prefixes override global ones."""
    # Define a global prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://global.org/"})

    # Define a graph-specific prefix with the same name
    await client.call_tool(
        "rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://local.org/", "graph_name": "test-graph"}
    )

    # Read the graph-specific prefix resource
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/test-graph/prefix")

    # Graph-specific should override global
    assert prefixes["test"] == "http://local.org/"


@pytest.mark.asyncio
async def test_empty_prefix_resources(client: Client):
    """Test reading prefix resources when no prefixes are defined."""
    # Read global prefixes (should be empty)
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/prefix")
    assert prefixes == {}

    # Read graph-specific prefixes (should be empty)
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/nonexistent/prefix")
    assert prefixes == {}
