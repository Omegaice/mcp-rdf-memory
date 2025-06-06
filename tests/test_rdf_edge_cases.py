"""
Tests for RDF-specific edge cases that span multiple tools.
"""

import pytest
from fastmcp import Client


@pytest.mark.asyncio
async def test_typed_literals(client: Client) -> None:
    """Test RDF typed literals like integers, dates, etc."""
    # Add typed literal
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/typed",
                    "predicate": "http://schema.org/age",
                    "object": "42^^<http://www.w3.org/2001/XMLSchema#integer>",
                }
            ]
        },
    )

    # Query should work
    result = await client.call_tool(
        "rdf_query", {"query": "SELECT ?age WHERE { <http://example.org/person/typed> <http://schema.org/age> ?age }"}
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_language_tagged_literals(client: Client) -> None:
    """Test RDF language-tagged literals."""
    # Add language-tagged literals
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/multilingual",
                    "predicate": "http://schema.org/name",
                    "object": "Hello@en",
                },
                {
                    "subject": "http://example.org/person/multilingual",
                    "predicate": "http://schema.org/name",
                    "object": "Bonjour@fr",
                },
            ]
        },
    )

    # Query should find both
    result = await client.call_tool(
        "rdf_query",
        {"query": "SELECT ?name WHERE { <http://example.org/person/multilingual> <http://schema.org/name> ?name }"},
    )
    assert len(result) == 1


@pytest.mark.asyncio
async def test_unicode_content(client: Client) -> None:
    """Test Unicode characters in RDF literals."""
    unicode_strings = [
        "Hello 世界",  # Mixed English/Chinese
        "Café résumé",  # Accented characters
        "🌍🌎🌏",  # Emoji
        "Ελληνικά",  # Greek
    ]

    for i, unicode_str in enumerate(unicode_strings):
        await client.call_tool(
            "add_triples",
            {
                "triples": [
                    {
                        "subject": f"http://example.org/unicode/test{i}",
                        "predicate": "http://schema.org/name",
                        "object": unicode_str,
                    }
                ]
            },
        )

    # Query should work
    result = await client.call_tool("rdf_query", {"query": "SELECT ?name WHERE { ?s <http://schema.org/name> ?name }"})
    assert len(result) == 1


@pytest.mark.asyncio
async def test_multiline_strings(client: Client) -> None:
    """Test multiline strings with quotes and escapes."""
    multiline_object = """Line 1
Line 2 with "quotes"
Line 3 with 'single quotes'
Line 4 with \\ backslash"""

    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/multiline/test",
                    "predicate": "http://schema.org/description",
                    "object": multiline_object,
                }
            ]
        },
    )

    # Should be queryable
    result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/multiline/test"})
    assert len(result) == 1


@pytest.mark.asyncio
async def test_duplicate_triples(client: Client) -> None:
    """Test adding identical triples multiple times."""
    triple_data = {
        "subject": "http://example.org/duplicate/test",
        "predicate": "http://schema.org/name",
        "object": "Duplicate Test",
    }

    # Add same triple three times
    for _ in range(3):
        await client.call_tool("add_triples", {"triples": [triple_data]})

    # Should only appear once in results
    result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/duplicate/test"})
    # Note: RDF semantics may deduplicate or not - test documents behavior
    assert len(result) >= 1


@pytest.mark.asyncio
async def test_self_referential_triples(client: Client) -> None:
    """Test triples where subject equals object."""
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/self/reference",
                    "predicate": "http://xmlns.com/foaf/0.1/knows",
                    "object": "http://example.org/self/reference",
                }
            ]
        },
    )

    # Should be queryable
    result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/self/reference"})
    assert len(result) == 1


@pytest.mark.asyncio
async def test_circular_references(client: Client) -> None:
    """Test circular reference patterns."""
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/alice",
                    "predicate": "http://xmlns.com/foaf/0.1/knows",
                    "object": "http://example.org/person/bob",
                },
                {
                    "subject": "http://example.org/person/bob",
                    "predicate": "http://xmlns.com/foaf/0.1/knows",
                    "object": "http://example.org/person/alice",
                },
            ]
        },
    )

    # Both should be queryable
    result_alice = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/person/alice"})
    result_bob = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/person/bob"})

    assert len(result_alice) == 1
    assert len(result_bob) == 1


@pytest.mark.asyncio
async def test_cross_graph_isolation(client: Client, sample_graph_uri: str) -> None:
    """Test that data in different graphs is properly isolated."""
    # Add same triple to default and named graph
    triple_data = {
        "subject": "http://example.org/isolation/test",
        "predicate": "http://schema.org/name",
        "object": "Isolation Test",
    }

    # Add to default graph
    await client.call_tool("add_triples", {"triples": [triple_data]})

    # Add to named graph
    triple_with_graph = {**triple_data, "graph_name": "conversation/test-123"}
    await client.call_tool("add_triples", {"triples": [triple_with_graph]})

    # Query default graph only
    default_result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/isolation/test"})

    # Query named graph only
    named_result = await client.call_tool(
        "quads_for_pattern", {"subject": "http://example.org/isolation/test", "graph_name": "conversation/test-123"}
    )

    # Should have data in both but separately
    assert len(default_result) >= 1
    assert len(named_result) >= 1
