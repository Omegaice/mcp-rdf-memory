"""Tests for RDF prefix management functionality."""

import json

import pytest
from fastmcp.client.client import Client
from mcp.types import TextContent, TextResourceContents


def assert_tool_returns_empty(result) -> None:
    """Assert that tool call result is empty (tool returned None)."""
    __tracebackhide__ = True
    assert len(result) == 0


def parse_sparql_result(result) -> list[dict[str, str]]:
    """Parse SPARQL query result with proper type checking."""
    __tracebackhide__ = True
    assert len(result) == 1, "Expected exactly one result"
    assert isinstance(result[0], TextContent), f"Expected TextContent but got {type(result[0])}"
    return json.loads(result[0].text)


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
async def test_standard_prefix_resources(client: Client):
    """Test that standard RDF namespaces are pre-populated."""
    # Read global prefixes (should contain standard namespaces)
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/prefix")

    # Verify standard namespaces are present
    assert "rdf" in prefixes
    assert prefixes["rdf"] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert "rdfs" in prefixes
    assert prefixes["rdfs"] == "http://www.w3.org/2000/01/rdf-schema#"
    assert "foaf" in prefixes
    assert prefixes["foaf"] == "http://xmlns.com/foaf/0.1/"
    assert "schema" in prefixes
    assert prefixes["schema"] == "http://schema.org/"

    # Read graph-specific prefixes (should include global prefixes)
    prefixes = await get_prefixes_from_resource(client, "rdf://graph/nonexistent/prefix")
    assert "rdf" in prefixes  # Global prefixes are included


@pytest.mark.asyncio
async def test_curie_expansion_stores_expanded_iris(client: Client):
    """Test that CURIEs are expanded to full IRIs when storing triples."""
    # Define prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "ex", "namespace_uri": "http://example.org/"})

    # Add triple using CURIE notation
    await client.call_tool(
        "rdf_add_triples", {"triples": [{"subject": "ex:alice", "predicate": "ex:knows", "object": "ex:bob"}]}
    )

    # Query to check what's actually stored
    result = await client.call_tool("rdf_sparql_query", {"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"})
    
    raw_data = parse_sparql_result(result)
    assert len(raw_data) == 1, "Expected exactly one triple"

    # Verify the stored values are expanded IRIs (may include angle brackets)
    triple = raw_data[0]
    assert "http://example.org/alice" in triple["s"]
    assert "http://example.org/knows" in triple["p"]
    assert "http://example.org/bob" in triple["o"]


@pytest.mark.asyncio
async def test_expanded_curies_match_sparql_prefix_queries(client: Client):
    """Test that expanded CURIEs can be found by SPARQL queries using prefixes."""
    # Define prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "ex", "namespace_uri": "http://example.org/"})

    # Add triple using CURIE notation
    await client.call_tool(
        "rdf_add_triples", {"triples": [{"subject": "ex:alice", "predicate": "ex:knows", "object": "ex:bob"}]}
    )

    # Query using SPARQL with prefix expansion
    sparql_query = """
    PREFIX ex: <http://example.org/>
    SELECT ?friend WHERE {
        ex:alice ex:knows ?friend .
    }
    """

    result = await client.call_tool("rdf_sparql_query", {"query": sparql_query})
    
    query_data = parse_sparql_result(result)
    assert len(query_data) == 1, "Expected to find the friend"

    # Verify we got the correct result
    friend = query_data[0]["friend"]
    assert "http://example.org/bob" in friend


@pytest.mark.asyncio
async def test_curie_expansion_with_literal_objects(client: Client):
    """Test that CURIE expansion works correctly when objects are literals."""
    # Define prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "ex", "namespace_uri": "http://example.org/"})

    # Add triple with CURIE subject/predicate but literal object
    await client.call_tool(
        "rdf_add_triples",
        {"triples": [{"subject": "ex:person", "predicate": "ex:name", "object": "Alice Smith"}]},
    )

    # Query to verify expansion
    result = await client.call_tool("rdf_sparql_query", {"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"})
    
    data = parse_sparql_result(result)
    assert len(data) == 1

    # Subject and predicate should be expanded, object should remain literal
    assert "http://example.org/person" in data[0]["s"]
    assert "http://example.org/name" in data[0]["p"]
    assert data[0]["o"] == '"Alice Smith"'  # Literal with quotes


@pytest.mark.asyncio
async def test_prefix_expansion_with_undefined_prefix(client: Client):
    """Test that CURIEs with undefined prefixes are stored as-is."""
    # Add triple using CURIE notation WITHOUT defining the prefix first
    await client.call_tool(
        "rdf_add_triples",
        {"triples": [{"subject": "undefined:alice", "predicate": "undefined:knows", "object": "undefined:bob"}]},
    )

    # Query to see what was stored
    result = await client.call_tool("rdf_sparql_query", {"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"})
    
    raw_data = parse_sparql_result(result)
    assert len(raw_data) > 0

    # Should be stored as-is since prefix is undefined
    triple = raw_data[0]
    assert "undefined:alice" in triple["s"]
    assert "undefined:knows" in triple["p"]
    assert "undefined:bob" in triple["o"]


@pytest.mark.asyncio
async def test_prefix_expansion_with_standard_namespaces(client: Client):
    """Test that standard RDF namespaces are pre-populated and work correctly."""
    # Add triple using standard namespace CURIEs (no need to define them)
    await client.call_tool(
        "rdf_add_triples",
        {"triples": [{"subject": "http://example.org/person/john", "predicate": "rdf:type", "object": "foaf:Person"}]},
    )

    # Query with SPARQL that uses the standard prefixes
    sparql_query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT ?person WHERE {
        ?person rdf:type foaf:Person .
    }
    """

    result = await client.call_tool("rdf_sparql_query", {"query": sparql_query})
    
    query_data = parse_sparql_result(result)
    assert len(query_data) == 1
    assert "http://example.org/person/john" in query_data[0]["person"]


@pytest.mark.asyncio
async def test_graph_specific_prefix_overrides_global_during_expansion(client: Client):
    """Test that graph-specific prefixes override global prefixes during CURIE expansion."""
    # Define global prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://global.org/"})

    # Define graph-specific prefix with same name
    await client.call_tool(
        "rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://local.org/", "graph_name": "special-graph"}
    )

    # Add triple to special graph using CURIE
    await client.call_tool(
        "rdf_add_triples",
        {"triples": [{"subject": "test:item", "predicate": "test:property", "object": "test:value", "graph_name": "special-graph"}]},
    )

    # Query the special graph to verify correct expansion
    result = await client.call_tool(
        "rdf_sparql_query", {"query": "SELECT ?s ?p ?o FROM <http://mcp.local/special-graph> WHERE { ?s ?p ?o . }"}
    )
    
    data = parse_sparql_result(result)
    assert len(data) == 1

    # Should use graph-specific prefix, not global
    assert "http://local.org/item" in data[0]["s"]
    assert "http://local.org/property" in data[0]["p"]
    assert "http://local.org/value" in data[0]["o"]


@pytest.mark.asyncio
async def test_global_prefix_used_in_default_graph(client: Client):
    """Test that global prefixes are used for default graph expansion."""
    # Define global prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "test", "namespace_uri": "http://global.org/"})

    # Add triple to default graph using CURIE
    await client.call_tool(
        "rdf_add_triples",
        {"triples": [{"subject": "test:item", "predicate": "test:property", "object": "test:value"}]},
    )

    # Query to verify correct expansion
    result = await client.call_tool("rdf_sparql_query", {"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o . }"})
    
    data = parse_sparql_result(result)
    assert len(data) == 1

    # Should use global prefix
    assert "http://global.org/item" in data[0]["s"]
    assert "http://global.org/property" in data[0]["p"]
    assert "http://global.org/value" in data[0]["o"]
