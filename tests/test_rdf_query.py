"""
Tests for the rdf_query tool.
"""

import pytest
from fastmcp.exceptions import ToolError
from mcp.types import TextContent


@pytest.mark.asyncio
async def test_rdf_query_tool_available(client):
    """Test that rdf_query tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "rdf_query" in tool_names


@pytest.mark.asyncio
async def test_rdf_query_select(client):
    """Test SPARQL SELECT query."""
    # First add some test data
    await client.call_tool("add_triples", {
        "triples": [
            {
                "subject": "http://example.org/person/sparql1",
                "predicate": "http://schema.org/name",
                "object": "SPARQL Person One"
            },
            {
                "subject": "http://example.org/person/sparql2", 
                "predicate": "http://schema.org/name",
                "object": "SPARQL Person Two"
            }
        ]
    })
    
    # Query for all names
    result = await client.call_tool("rdf_query", {
        "query": "SELECT ?name WHERE { ?person <http://schema.org/name> ?name }"
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "SPARQL Person One" in result[0].text
    assert "SPARQL Person Two" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_ask(client):
    """Test SPARQL ASK query."""
    # Add test data
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/test_ask",
            "predicate": "http://schema.org/name",
            "object": "Test Person"
        }]
    })
    
    # ASK if the person exists
    result = await client.call_tool("rdf_query", {
        "query": "ASK { <http://example.org/person/test_ask> <http://schema.org/name> ?name }"
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "true" in result[0].text.lower()


@pytest.mark.asyncio
async def test_rdf_query_construct(client):
    """Test SPARQL CONSTRUCT query."""
    # Add test data
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/construct_test",
            "predicate": "http://schema.org/name",
            "object": "Construct Test Person"
        }]
    })
    
    # CONSTRUCT new triples
    result = await client.call_tool("rdf_query", {
        "query": """
        CONSTRUCT { ?person <http://example.org/hasName> ?name }
        WHERE { ?person <http://schema.org/name> ?name }
        """
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "hasName" in result[0].text
    assert "Construct Test Person" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_with_named_graph(client, sample_graph_uri):
    """Test SPARQL query with named graph."""
    # Add data to named graph
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/graph_test",
            "predicate": "http://schema.org/name",
            "object": "Graph Test Person",
            "graph": sample_graph_uri
        }]
    })
    
    # Query specific graph
    result = await client.call_tool("rdf_query", {
        "query": f"SELECT ?name FROM <{sample_graph_uri}> WHERE {{ ?person <http://schema.org/name> ?name }}"
    })
    
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Graph Test Person" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_invalid_syntax(client):
    """Test that invalid SPARQL syntax raises an error."""
    with pytest.raises(ToolError):
        await client.call_tool("rdf_query", {
            "query": "INVALID SPARQL SYNTAX"
        })


@pytest.mark.asyncio
async def test_rdf_query_modification_blocked(client):
    """Test that modification queries (INSERT/DELETE) are blocked."""
    # Try INSERT query
    with pytest.raises(ToolError):
        await client.call_tool("rdf_query", {
            "query": "INSERT DATA { <http://example.org/test> <http://example.org/prop> 'value' }"
        })
    
    # Try DELETE query
    with pytest.raises(ToolError):
        await client.call_tool("rdf_query", {
            "query": "DELETE WHERE { ?s ?p ?o }"
        })