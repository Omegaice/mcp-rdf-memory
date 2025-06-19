"""Tests for MCP resources functionality."""

import pytest
from fastmcp import Client
from mcp.types import TextResourceContents


def find_resource_by_uri(resources, uri: str):
    """Find a resource by URI."""
    __tracebackhide__ = True
    return next((r for r in resources if str(r.uri) == uri), None)


async def get_resource_content(client: Client, uri: str) -> str:
    """Get content from a resource URI."""
    __tracebackhide__ = True
    result = await client.read_resource(uri)
    assert len(result) == 1
    assert isinstance(result[0], TextResourceContents)
    return result[0].text


def assert_quad_in_content(content: str, subject: str, predicate: str, obj: str, graph: str | None = None):
    """Assert that a specific quad exists in N-Quads content."""
    __tracebackhide__ = True
    if graph:
        expected_quad = f"<{subject}> <{predicate}> \"{obj}\" <{graph}> ."
    else:
        expected_quad = f"<{subject}> <{predicate}> \"{obj}\" ."
    assert expected_quad in content, f"Expected quad not found: {expected_quad}"


@pytest.mark.asyncio
async def test_export_all_resource_available(client: Client):
    """Test that the export_all_triples resource is available."""
    resources = await client.list_resources()

    # Find the export resource
    export_resource = find_resource_by_uri(resources, "rdf://graph")
    assert export_resource is not None, "rdf://graph resource not found"
    assert export_resource.name == "export_all_graphs"
    assert export_resource.mimeType == "application/n-quads"
    assert "Export all RDF data from the triple store" in export_resource.description


@pytest.mark.asyncio
async def test_export_empty_store(client: Client):
    """Test exporting when the store is empty."""
    # Read the resource
    content = await get_resource_content(client, "rdf://graph")
    assert content == ""  # Empty store should return empty string


@pytest.mark.asyncio
async def test_export_with_data(client: Client):
    """Test exporting when the store contains data."""
    # Add some test data
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/alice",
                    "predicate": "http://xmlns.com/foaf/0.1/name",
                    "object": "Alice",
                },
                {
                    "subject": "http://example.org/bob",
                    "predicate": "http://xmlns.com/foaf/0.1/name",
                    "object": "Bob",
                    "graph_name": "people",
                },
            ]
        },
    )

    # Read the export resource
    content = await get_resource_content(client, "rdf://graph")

    # Parse N-Quads format
    lines = content.strip().split("\n")
    assert len(lines) == 2

    # Check that both quads are present with correct format
    assert_quad_in_content(content, "http://example.org/alice", "http://xmlns.com/foaf/0.1/name", "Alice")
    assert_quad_in_content(content, "http://example.org/bob", "http://xmlns.com/foaf/0.1/name", "Bob", "http://mcp.local/people")


@pytest.mark.asyncio
async def test_export_preserves_literal_types(client: Client):
    """Test that export preserves different literal types."""
    # Add triples with different literal types
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/test",
                    "predicate": "http://example.org/text",
                    "object": "Plain text",
                },
                {
                    "subject": "http://example.org/test",
                    "predicate": "http://example.org/unicode",
                    "object": "Unicode: 你好世界 🌍",
                },
                {
                    "subject": "http://example.org/test",
                    "predicate": "http://example.org/multiline",
                    "object": "Line 1\nLine 2\nLine 3",
                },
            ]
        },
    )

    # Read the export
    content = await get_resource_content(client, "rdf://graph")

    # Check all literals are properly serialized
    assert_quad_in_content(content, "http://example.org/test", "http://example.org/text", "Plain text")
    assert_quad_in_content(content, "http://example.org/test", "http://example.org/unicode", "Unicode: 你好世界 🌍")
    # N-Quads escapes newlines - check manually since it's complex
    assert '"Line 1\\nLine 2\\nLine 3"' in content


@pytest.mark.asyncio
async def test_export_multiple_graphs(client: Client):
    """Test exporting data from multiple named graphs."""
    # Add data to multiple graphs
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/default",
                    "predicate": "http://example.org/in",
                    "object": "default graph",
                },
                {
                    "subject": "http://example.org/graph1",
                    "predicate": "http://example.org/in",
                    "object": "graph 1",
                    "graph_name": "graph1",
                },
                {
                    "subject": "http://example.org/graph2",
                    "predicate": "http://example.org/in",
                    "object": "graph 2",
                    "graph_name": "graph2",
                },
            ]
        },
    )

    # Read the export
    content = await get_resource_content(client, "rdf://graph")

    # Check all quads are present with correct format
    assert_quad_in_content(content, "http://example.org/default", "http://example.org/in", "default graph")
    assert_quad_in_content(content, "http://example.org/graph1", "http://example.org/in", "graph 1", "http://mcp.local/graph1")
    assert_quad_in_content(content, "http://example.org/graph2", "http://example.org/in", "graph 2", "http://mcp.local/graph2")

    # Verify N-Quads format
    lines = content.strip().split("\n")
    assert len(lines) == 3
    for line in lines:
        assert line.endswith(".")


@pytest.mark.asyncio
async def test_export_named_graph(client: Client):
    """Test exporting a specific named graph."""
    # Add data to multiple graphs
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/alice",
                    "predicate": "http://xmlns.com/foaf/0.1/name",
                    "object": "Alice",
                    "graph_name": "people",
                },
                {
                    "subject": "http://example.org/bob",
                    "predicate": "http://xmlns.com/foaf/0.1/name",
                    "object": "Bob",
                    "graph_name": "other",
                },
            ]
        },
    )

    # Read just the people graph
    content = await get_resource_content(client, "rdf://graph/people")

    # Should only contain Alice as a triple (no graph part when exporting single graph)
    assert_quad_in_content(content, "http://example.org/alice", "http://xmlns.com/foaf/0.1/name", "Alice")

    # Should NOT contain Bob (he's in the 'other' graph)
    assert "Bob" not in content
    assert "<http://example.org/bob>" not in content

    # When exporting a specific graph, it becomes triples (no graph part)
    # This is expected behavior when exporting from a single graph


@pytest.mark.asyncio
async def test_export_named_graph_detailed(client: Client):
    """Test exporting a named graph in detail."""
    # Add data to a named graph
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/alice",
                    "predicate": "http://xmlns.com/foaf/0.1/name",
                    "object": "Alice",
                    "graph_name": "people",
                }
            ]
        },
    )

    # Export the named graph
    content = await get_resource_content(client, "rdf://graph/people")

    # Should contain the data as a triple (single graph export)
    assert_quad_in_content(content, "http://example.org/alice", "http://xmlns.com/foaf/0.1/name", "Alice")
    assert content.strip().endswith(".")  # N-Triples format ends with period


@pytest.mark.asyncio
async def test_resource_templates_available(client: Client):
    """Test that the expected resource templates are available."""
    # List resource templates
    templates = await client.list_resource_templates()
    template_uris = [t.uriTemplate for t in templates]

    # Should have the named graph template
    assert "rdf://graph/{graph_name}" in template_uris

    # Should NOT have format templates (we removed them)
    format_templates = [uri for uri in template_uris if "format=" in uri]
    assert len(format_templates) == 0, f"Found unexpected format templates: {format_templates}"
