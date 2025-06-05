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
async def test_add_triples_tool_available():
    """Test that add_triples tool is available."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "add_triples" in tool_names


@pytest.mark.asyncio
async def test_add_simple_triple():
    """Test adding a basic RDF triple."""
    async with Client(mcp) as client:
        # Add a simple person-name triple
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
async def test_add_triple_with_named_graph():
    """Test adding a triple to a specific named graph context."""
    async with Client(mcp) as client:
        # Add triple to conversation context
        conversation_id = "conv-123"
        graph_uri = f"http://mcp.local/conversation/{conversation_id}"
        
        result = await client.call_tool("add_triples", {
            "triples": [{
                "subject": "http://example.org/person/alice",
                "predicate": "http://schema.org/name",
                "object": "Alice Smith",
                "graph": graph_uri
            }]
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "success" in result[0].text.lower()


@pytest.mark.asyncio
async def test_add_triple_with_uri_object():
    """Test adding a triple where the object is also a URI."""
    async with Client(mcp) as client:
        # Add a relationship between two people
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
async def test_add_multiple_triples():
    """Test adding multiple triples in a single call."""
    async with Client(mcp) as client:
        # Add multiple triples at once
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
async def test_add_triple_validation_error():
    """Test that invalid URIs are properly validated."""
    async with Client(mcp) as client:
        # Try to add triple with invalid subject URI
        with pytest.raises(ToolError):  # Should raise ToolError via FastMCP
            await client.call_tool("add_triples", {
                "triples": [{
                    "subject": "not-a-valid-uri",
                    "predicate": "http://schema.org/name", 
                    "object": "John Doe"
                }]
            })


@pytest.mark.asyncio
async def test_quads_for_pattern_tool_available():
    """Test that quads_for_pattern tool is available."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "quads_for_pattern" in tool_names


@pytest.mark.asyncio
async def test_quads_for_pattern_find_by_subject():
    """Test finding quads by subject pattern."""
    async with Client(mcp) as client:
        # First add a triple
        await client.call_tool("add_triples", {
            "triples": [{
                "subject": "http://example.org/person/bob",
                "predicate": "http://schema.org/name",
                "object": "Bob Smith"
            }]
        })
        
        # Find quads with specific subject
        result = await client.call_tool("quads_for_pattern", {
            "subject": "http://example.org/person/bob"
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Bob Smith" in result[0].text
        assert "http://schema.org/name" in result[0].text


@pytest.mark.asyncio
async def test_quads_for_pattern_find_by_predicate():
    """Test finding quads by predicate pattern."""
    async with Client(mcp) as client:
        # Add multiple triples with same predicate
        await client.call_tool("add_triples", {
            "triples": [
                {
                    "subject": "http://example.org/person/charlie",
                    "predicate": "http://schema.org/email",
                    "object": "charlie@example.com"
                },
                {
                    "subject": "http://example.org/person/diana",
                    "predicate": "http://schema.org/email", 
                    "object": "diana@example.com"
                }
            ]
        })
        
        # Find all email triples
        result = await client.call_tool("quads_for_pattern", {
            "predicate": "http://schema.org/email"
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "charlie@example.com" in result[0].text
        assert "diana@example.com" in result[0].text


@pytest.mark.asyncio
async def test_quads_for_pattern_with_named_graph():
    """Test finding quads in a specific named graph."""
    async with Client(mcp) as client:
        # Add triple to specific graph
        graph_uri = "http://mcp.local/conversation/test-123"
        await client.call_tool("add_triples", {
            "triples": [{
                "subject": "http://example.org/person/eve",
                "predicate": "http://schema.org/name",
                "object": "Eve Johnson",
                "graph": graph_uri
            }]
        })
        
        # Find quads in specific graph
        result = await client.call_tool("quads_for_pattern", {
            "graph": graph_uri
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Eve Johnson" in result[0].text
        assert graph_uri in result[0].text


@pytest.mark.asyncio
async def test_quads_for_pattern_wildcard_search():
    """Test finding all quads with wildcard pattern."""
    async with Client(mcp) as client:
        # Add a test triple
        await client.call_tool("add_triples", {
            "triples": [{
                "subject": "http://example.org/person/frank",
                "predicate": "http://schema.org/age",
                "object": "30"
            }]
        })
        
        # Find all quads (no pattern specified)
        result = await client.call_tool("quads_for_pattern", {})
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        # Should contain multiple results from previous tests
        assert "frank" in result[0].text.lower()


@pytest.mark.asyncio
async def test_quads_for_pattern_no_matches():
    """Test pattern that matches no quads."""
    async with Client(mcp) as client:
        # Search for non-existent subject
        result = await client.call_tool("quads_for_pattern", {
            "subject": "http://example.org/person/nonexistent"
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "no quads found" in result[0].text.lower() or result[0].text.strip() == ""


@pytest.mark.asyncio
async def test_rdf_query_tool_available():
    """Test that rdf_query tool is available."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]
        assert "rdf_query" in tool_names


@pytest.mark.asyncio
async def test_rdf_query_select():
    """Test SPARQL SELECT query."""
    async with Client(mcp) as client:
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
async def test_rdf_query_ask():
    """Test SPARQL ASK query."""
    async with Client(mcp) as client:
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
async def test_rdf_query_construct():
    """Test SPARQL CONSTRUCT query."""
    async with Client(mcp) as client:
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
async def test_rdf_query_with_named_graph():
    """Test SPARQL query with named graph."""
    async with Client(mcp) as client:
        # Add data to named graph
        graph_uri = "http://mcp.local/conversation/sparql-test"
        await client.call_tool("add_triples", {
            "triples": [{
                "subject": "http://example.org/person/graph_test",
                "predicate": "http://schema.org/name",
                "object": "Graph Test Person",
                "graph": graph_uri
            }]
        })
        
        # Query specific graph
        result = await client.call_tool("rdf_query", {
            "query": f"SELECT ?name FROM <{graph_uri}> WHERE {{ ?person <http://schema.org/name> ?name }}"
        })
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Graph Test Person" in result[0].text


@pytest.mark.asyncio
async def test_rdf_query_invalid_syntax():
    """Test that invalid SPARQL syntax raises an error."""
    async with Client(mcp) as client:
        # Try invalid SPARQL
        with pytest.raises(ToolError):
            await client.call_tool("rdf_query", {
                "query": "INVALID SPARQL SYNTAX"
            })


@pytest.mark.asyncio
async def test_rdf_query_modification_blocked():
    """Test that modification queries (INSERT/DELETE) are blocked."""
    async with Client(mcp) as client:
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