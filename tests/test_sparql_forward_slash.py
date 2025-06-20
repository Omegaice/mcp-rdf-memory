"""Tests for SPARQL 1.1 forward slash behavior in prefixed names.

According to SPARQL 1.1 specification (https://www.w3.org/TR/sparql11-query/):
- Forward slashes (/) are NOT allowed in the local part of prefixed names
- They must be escaped as \\/ to be valid (part of PLX escape sequences)
- Alternatively, use full IRIs in angle brackets

This test documents that pyoxigraph correctly follows the SPARQL 1.1 grammar.
"""

import json

import pytest
from fastmcp.client.client import Client
from fastmcp.exceptions import ToolError
from mcp.types import TextContent


def parse_sparql_result(result) -> list[dict[str, str]]:
    """Parse SPARQL query result with proper type checking."""
    __tracebackhide__ = True
    assert len(result) == 1, "Expected exactly one result"
    assert isinstance(result[0], TextContent), f"Expected TextContent but got {type(result[0])}"
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_sparql_forward_slash_invalid(client: Client):
    """Test that unescaped forward slashes in prefixed names are invalid per SPARQL 1.1."""
    # Define prefixes
    await client.call_tool("rdf_define_prefix", {"prefix": "file", "namespace_uri": "http://example.org/file/"})
    await client.call_tool("rdf_define_prefix", {"prefix": "deps", "namespace_uri": "http://example.org/deps/"})

    # Add data with forward slashes (stored as expanded IRIs)
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {"subject": "file:src/main.cpp", "predicate": "deps:includes", "object": "file:include/header.h"}
            ]
        },
    )

    # Try query with unescaped forward slashes - should fail
    query = """PREFIX file: <http://example.org/file/>
PREFIX deps: <http://example.org/deps/>
SELECT ?o WHERE {
  file:src/main.cpp deps:includes ?o .
}"""

    with pytest.raises(ToolError) as exc_info:
        await client.call_tool("rdf_sparql_query", {"query": query})

    # The error should be about invalid syntax at the forward slash position
    assert "error at" in str(exc_info.value)


@pytest.mark.asyncio
async def test_sparql_forward_slash_escaped(client: Client):
    """Test that escaped forward slashes in prefixed names are valid per SPARQL 1.1."""
    # Define prefixes
    await client.call_tool("rdf_define_prefix", {"prefix": "file", "namespace_uri": "http://example.org/file/"})
    await client.call_tool("rdf_define_prefix", {"prefix": "deps", "namespace_uri": "http://example.org/deps/"})

    # Add data with forward slashes (stored as expanded IRIs)
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {"subject": "file:src/main.cpp", "predicate": "deps:includes", "object": "file:include/header.h"}
            ]
        },
    )

    # Query with escaped forward slashes - should work
    query = """PREFIX file: <http://example.org/file/>
PREFIX deps: <http://example.org/deps/>
SELECT ?o WHERE {
  file:src\\/main.cpp deps:includes ?o .
}"""

    result = await client.call_tool("rdf_sparql_query", {"query": query})
    data = parse_sparql_result(result)

    assert len(data) == 1
    assert "http://example.org/file/include/header.h" in data[0]["o"]


@pytest.mark.asyncio
async def test_sparql_forward_slash_full_iri(client: Client):
    """Test that full IRIs with forward slashes work correctly."""
    # Define prefixes for data insertion
    await client.call_tool("rdf_define_prefix", {"prefix": "file", "namespace_uri": "http://example.org/file/"})
    await client.call_tool("rdf_define_prefix", {"prefix": "deps", "namespace_uri": "http://example.org/deps/"})

    # Add data with forward slashes
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {"subject": "file:src/main.cpp", "predicate": "deps:includes", "object": "file:include/header.h"}
            ]
        },
    )

    # Query with full IRIs - always works regardless of forward slashes
    query = """SELECT ?o WHERE {
  <http://example.org/file/src/main.cpp> <http://example.org/deps/includes> ?o .
}"""

    result = await client.call_tool("rdf_sparql_query", {"query": query})
    data = parse_sparql_result(result)

    assert len(data) == 1
    assert "http://example.org/file/include/header.h" in data[0]["o"]


@pytest.mark.asyncio
async def test_sparql_alternative_separators(client: Client):
    """Test using alternative separators instead of forward slashes."""
    # Define prefix
    await client.call_tool("rdf_define_prefix", {"prefix": "file", "namespace_uri": "http://example.org/file/"})

    # Add data with underscores as separators
    await client.call_tool(
        "rdf_add_triples",
        {
            "triples": [
                {"subject": "file:src_main_cpp", "predicate": "file:includes", "object": "file:include_header_h"}
            ]
        },
    )

    # Query works without any escaping needed
    query = """PREFIX file: <http://example.org/file/>
SELECT ?o WHERE {
  file:src_main_cpp file:includes ?o .
}"""

    result = await client.call_tool("rdf_sparql_query", {"query": query})
    data = parse_sparql_result(result)

    assert len(data) == 1
    assert "http://example.org/file/include_header_h" in data[0]["o"]
