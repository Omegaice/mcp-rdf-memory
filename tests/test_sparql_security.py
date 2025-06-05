"""
Tests for SPARQL security and keyword bypass attempts.
"""

import pytest
from fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_sparql_case_insensitive_keywords(client):
    """Test that forbidden keywords are blocked regardless of case."""
    case_variations = [
        "insert data { <http://example.org/test> <http://example.org/prop> 'value' }",
        "INSERT data { <http://example.org/test> <http://example.org/prop> 'value' }",
        "Insert DATA { <http://example.org/test> <http://example.org/prop> 'value' }",
        "delete where { ?s ?p ?o }",
        "DELETE where { ?s ?p ?o }",
        "Delete WHERE { ?s ?p ?o }",
        "drop graph <http://example.org/graph>",
        "DROP graph <http://example.org/graph>",
        "Drop GRAPH <http://example.org/graph>",
        "clear graph <http://example.org/graph>",
        "CLEAR graph <http://example.org/graph>",
        "Clear GRAPH <http://example.org/graph>",
    ]

    for query in case_variations:
        with pytest.raises(ToolError):
            await client.call_tool("rdf_query", {"query": query})


@pytest.mark.asyncio
async def test_sparql_keywords_in_comments(client):
    """Test that keywords in comments should NOT be blocked."""
    # These should work - keywords are in comments, not actual operations
    comment_queries = [
        "# This INSERT is just a comment\nSELECT ?s WHERE { ?s ?p ?o }",
        "SELECT ?s WHERE { ?s ?p ?o } # DELETE comment here",
        "# DROP, CLEAR, CREATE are forbidden\nASK { ?s ?p ?o }",
    ]

    for query in comment_queries:
        # These should NOT raise ToolError about forbidden keywords
        result = await client.call_tool("rdf_query", {"query": query})
        # Should return valid results (empty or otherwise)
        assert isinstance(result, list | bool)


@pytest.mark.asyncio
async def test_sparql_keywords_in_string_literals(client):
    """Test that keywords in string literals should NOT be blocked."""
    # Add test data first
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/message/1",
                    "predicate": "http://schema.org/text",
                    "object": "INSERT failed",
                },
                {
                    "subject": "http://example.org/message/2",
                    "predicate": "http://schema.org/text",
                    "object": "The DELETE operation was not allowed",
                },
            ]
        },
    )

    # These queries contain keywords in string literals - should work
    literal_queries = [
        "SELECT ?msg WHERE { ?x <http://schema.org/text> 'INSERT failed' }",
        "SELECT ?msg WHERE { ?x <http://schema.org/text> 'DELETE operation' }",
        "ASK { ?x <http://schema.org/text> 'CLEAR the cache' }",
    ]

    for query in literal_queries:
        # Should NOT raise ToolError about forbidden keywords
        result = await client.call_tool("rdf_query", {"query": query})
        # Should return valid results
        assert isinstance(result, list | bool)


@pytest.mark.asyncio
async def test_sparql_keywords_as_substrings(client):
    """Test that keywords as substrings in valid operations should work."""
    # These contain forbidden keywords as substrings but are valid read operations
    substring_queries = [
        "SELECT ?description WHERE { ?x <http://schema.org/description> ?description }",  # Contains DELETE
        "SELECT ?insertion WHERE { ?x <http://example.org/insertion> ?insertion }",  # Contains INSERT
        "ASK { ?x <http://example.org/dropped> ?value }",  # Contains DROP
        "SELECT ?cleared WHERE { ?x <http://example.org/cleared> ?cleared }",  # Contains CLEAR
    ]

    for query in substring_queries:
        # Should NOT raise ToolError about forbidden keywords
        result = await client.call_tool("rdf_query", {"query": query})
        assert isinstance(result, list | bool)


@pytest.mark.asyncio
async def test_sparql_all_forbidden_keywords(client):
    """Test that all forbidden keywords from FORBIDDEN_SPARQL_KEYWORDS are blocked."""
    forbidden_operations = [
        "INSERT DATA { <http://example.org/test> <http://example.org/prop> 'value' }",
        "DELETE WHERE { ?s ?p ?o }",
        "DROP GRAPH <http://example.org/graph>",
        "CLEAR GRAPH <http://example.org/graph>",
        "CREATE GRAPH <http://example.org/graph>",
        "LOAD <http://example.org/data.rdf>",
        "COPY <http://example.org/source> TO <http://example.org/target>",
        "MOVE <http://example.org/source> TO <http://example.org/target>",
        "ADD <http://example.org/source> TO <http://example.org/target>",
    ]

    for operation in forbidden_operations:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("rdf_query", {"query": operation})

        # Error message should mention that modifications are not allowed
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["forbidden", "not allowed", "modification"])


@pytest.mark.asyncio
async def test_sparql_complex_valid_queries(client):
    """Test complex but valid read-only SPARQL queries."""
    # Add test data
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/complex1",
                    "predicate": "http://schema.org/name",
                    "object": "Complex Person One",
                },
                {
                    "subject": "http://example.org/person/complex1",
                    "predicate": "http://schema.org/age",
                    "object": "25",
                },
                {
                    "subject": "http://example.org/person/complex2",
                    "predicate": "http://schema.org/name",
                    "object": "Complex Person Two",
                },
            ]
        },
    )

    complex_queries = [
        # Query with PREFIX
        """
        PREFIX schema: <http://schema.org/>
        SELECT ?name WHERE { ?person schema:name ?name }
        """,
        # Query with FILTER
        "SELECT ?name WHERE { ?person <http://schema.org/name> ?name . FILTER(STRLEN(?name) > 10) }",
        # Query with OPTIONAL
        """
        SELECT ?name ?age WHERE { 
            ?person <http://schema.org/name> ?name .
            OPTIONAL { ?person <http://schema.org/age> ?age }
        }
        """,
        # Query with UNION
        """
        SELECT ?value WHERE {
            { ?x <http://schema.org/name> ?value }
            UNION
            { ?x <http://schema.org/age> ?value }
        }
        """,
    ]

    for query in complex_queries:
        result = await client.call_tool("rdf_query", {"query": query})
        assert isinstance(result, list)
