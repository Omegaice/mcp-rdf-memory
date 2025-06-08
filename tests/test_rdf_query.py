"""
Tests for the rdf_query tool.
"""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import TextContent


@pytest.mark.asyncio
async def test_rdf_query_tool_available(client: Client) -> None:
    """Test that rdf_query tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "rdf_query" in tool_names


@pytest.mark.asyncio
async def test_rdf_query_select(client: Client) -> None:
    """Test SPARQL SELECT query."""
    # First add some test data
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/sparql1",
                    "predicate": "http://schema.org/name",
                    "object": "SPARQL Person One",
                },
                {
                    "subject": "http://example.org/person/sparql2",
                    "predicate": "http://schema.org/name",
                    "object": "SPARQL Person Two",
                },
            ]
        },
    )

    # Query for all names
    result = await client.call_tool(
        "rdf_query", {"query": "SELECT ?name WHERE { ?person <http://schema.org/name> ?name }"}
    )

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "SPARQL Person One" in result[0].text
    assert "SPARQL Person Two" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_ask(client: Client) -> None:
    """Test SPARQL ASK query."""
    # Add test data
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/test_ask",
                    "predicate": "http://schema.org/name",
                    "object": "Test Person",
                }
            ]
        },
    )

    # ASK if the person exists
    result = await client.call_tool(
        "rdf_query", {"query": "ASK { <http://example.org/person/test_ask> <http://schema.org/name> ?name }"}
    )

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "true" in result[0].text.lower()


@pytest.mark.asyncio
async def test_rdf_query_construct(client: Client) -> None:
    """Test SPARQL CONSTRUCT query."""
    # Add test data
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/construct_test",
                    "predicate": "http://schema.org/name",
                    "object": "Construct Test Person",
                }
            ]
        },
    )

    # CONSTRUCT new triples
    result = await client.call_tool(
        "rdf_query",
        {
            "query": """
        CONSTRUCT { ?person <http://example.org/hasName> ?name }
        WHERE { ?person <http://schema.org/name> ?name }
        """
        },
    )

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "hasName" in result[0].text
    assert "Construct Test Person" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_with_named_graph(client: Client, sample_graph_uri: str) -> None:
    """Test SPARQL query with named graph."""
    # Add data to named graph
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/graph_test",
                    "predicate": "http://schema.org/name",
                    "object": "Graph Test Person",
                    "graph_name": "conversation/test-123",
                }
            ]
        },
    )

    # Query specific graph
    result = await client.call_tool(
        "rdf_query",
        {"query": f"SELECT ?name FROM <{sample_graph_uri}> WHERE {{ ?person <http://schema.org/name> ?name }}"},
    )

    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Graph Test Person" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_invalid_syntax(client: Client) -> None:
    """Test that invalid SPARQL syntax raises an error."""
    with pytest.raises(ToolError):
        await client.call_tool("rdf_query", {"query": "INVALID SPARQL SYNTAX"})


@pytest.mark.asyncio
async def test_rdf_query_only_supports_read_operations(client: Client) -> None:
    """Test that rdf_query only supports read operations due to pyoxigraph query() API design.
    
    The pyoxigraph library separates read operations (query method) from write operations 
    (update method). The query() method only accepts SELECT, ASK, CONSTRUCT, DESCRIBE 
    and rejects modification operations with syntax errors.
    """
    # INSERT operations require the update() method, not query() method
    with pytest.raises(ToolError) as exc_info:
        await client.call_tool(
            "rdf_query", {"query": "INSERT DATA { <http://example.org/test> <http://example.org/prop> 'value' }"}
        )
    error_msg = str(exc_info.value).lower()
    assert "expected construct" in error_msg or "syntax" in error_msg or "invalid" in error_msg

    # DELETE operations also require the update() method, not query() method
    with pytest.raises(ToolError) as exc_info:
        await client.call_tool("rdf_query", {"query": "DELETE WHERE { ?s ?p ?o }"})
    error_msg = str(exc_info.value).lower()
    assert "expected construct" in error_msg or "syntax" in error_msg or "invalid" in error_msg


@pytest.mark.asyncio
async def test_rdf_query_empty_query(client: Client) -> None:
    """Test that empty SPARQL queries raise errors."""
    with pytest.raises(ToolError):
        await client.call_tool("rdf_query", {"query": ""})

    with pytest.raises(ToolError):
        await client.call_tool("rdf_query", {"query": "   "})


@pytest.mark.asyncio
async def test_rdf_query_completely_invalid_syntax(client: Client) -> None:
    """Test various completely invalid SPARQL syntax."""
    invalid_queries = [
        "INVALID SPARQL SYNTAX",
        "{ ?s ?p ?o",  # Missing closing brace
        "SELECT ?s WHERE",  # Incomplete WHERE clause
    ]

    for query in invalid_queries:
        with pytest.raises(ToolError):
            await client.call_tool("rdf_query", {"query": query})
