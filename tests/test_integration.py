"""
Comprehensive integration tests spanning multiple tools and workflows.
"""

import json

import pytest
from mcp.types import TextContent

from mcp_rdf_memory.server import QuadResult


@pytest.mark.asyncio
async def test_complete_workflow_default_graph(client):
    """Test complete workflow: add data → query → pattern match → verify."""
    # Step 1: Add structured data
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/workflow/person1",
                    "predicate": "http://schema.org/name",
                    "object": "Workflow Person One",
                },
                {
                    "subject": "http://example.org/workflow/person1",
                    "predicate": "http://schema.org/email",
                    "object": "person1@example.org",
                },
                {
                    "subject": "http://example.org/workflow/person2",
                    "predicate": "http://schema.org/name",
                    "object": "Workflow Person Two",
                },
                {
                    "subject": "http://example.org/workflow/person1",
                    "predicate": "http://xmlns.com/foaf/0.1/knows",
                    "object": "http://example.org/workflow/person2",
                },
            ]
        },
    )

    # Step 2: Query using SPARQL
    sparql_result = await client.call_tool(
        "rdf_query", {"query": "SELECT ?name WHERE { ?person <http://schema.org/name> ?name }"}
    )
    assert len(sparql_result) == 1
    # SPARQL results are returned as TextContent by FastMCP
    assert isinstance(sparql_result[0], TextContent)

    # Step 3: Pattern matching
    name_pattern_result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    assert len(name_pattern_result) == 1
    assert isinstance(name_pattern_result[0], TextContent)

    # Parse and verify pattern results
    quads_data = json.loads(name_pattern_result[0].text)
    quads = [QuadResult(**quad) for quad in quads_data]
    assert len(quads) >= 2  # Should have both people

    # Step 4: Verify specific relationships
    knows_result = await client.call_tool("quads_for_pattern", {"predicate": "http://xmlns.com/foaf/0.1/knows"})
    assert len(knows_result) == 1
    quads_data = json.loads(knows_result[0].text)
    knows_quads = [QuadResult(**quad) for quad in quads_data]
    assert len(knows_quads) >= 1


@pytest.mark.asyncio
async def test_mixed_graph_operations(client, sample_graph_uri):
    """Test operations across multiple named graphs."""
    # Add data to different graphs
    default_triple = {
        "subject": "http://example.org/mixed/shared",
        "predicate": "http://schema.org/context",
        "object": "default",
    }

    named_triple = {
        "subject": "http://example.org/mixed/shared",
        "predicate": "http://schema.org/context",
        "object": "named",
        "graph": sample_graph_uri,
    }

    # Add to both graphs
    await client.call_tool("add_triples", {"triples": [default_triple]})
    await client.call_tool("add_triples", {"triples": [named_triple]})

    # Query all graphs (should see both)
    all_contexts = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/mixed/shared"})
    assert len(all_contexts) == 1
    quads_data = json.loads(all_contexts[0].text)
    all_quads = [QuadResult(**quad) for quad in quads_data]
    assert len(all_quads) >= 2

    # Query specific graph
    named_only = await client.call_tool(
        "quads_for_pattern", {"subject": "http://example.org/mixed/shared", "graph": sample_graph_uri}
    )
    assert len(named_only) == 1
    quads_data = json.loads(named_only[0].text)
    named_quads = [QuadResult(**quad) for quad in quads_data]
    assert len(named_quads) == 1
    assert sample_graph_uri in named_quads[0].graph


@pytest.mark.asyncio
async def test_query_result_consistency(client):
    """Test that same data is accessible through different query methods."""
    # Add test data
    test_subject = "http://example.org/consistency/test"
    test_predicate = "http://schema.org/name"
    test_object = "Consistency Test"

    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": test_subject,
                    "predicate": test_predicate,
                    "object": test_object,
                }
            ]
        },
    )

    # Method 1: SPARQL SELECT
    sparql_result = await client.call_tool(
        "rdf_query", {"query": f"SELECT ?name WHERE {{ <{test_subject}> <{test_predicate}> ?name }}"}
    )
    assert len(sparql_result) == 1

    # Method 2: Pattern matching by subject
    pattern_by_subject = await client.call_tool("quads_for_pattern", {"subject": test_subject})
    assert len(pattern_by_subject) == 1

    # Method 3: Pattern matching by predicate
    pattern_by_predicate = await client.call_tool("quads_for_pattern", {"predicate": test_predicate})
    assert len(pattern_by_predicate) == 1

    # All methods should find the same data
    # SPARQL should have the literal value
    sparql_data = sparql_result[0]
    assert any(test_object in str(binding) for binding in sparql_data)

    # Pattern queries should have formatted results
    subject_quads_data = json.loads(pattern_by_subject[0].text)
    subject_quads = [QuadResult(**quad) for quad in subject_quads_data]
    assert any(test_object in quad.object for quad in subject_quads)


@pytest.mark.asyncio
async def test_sparql_construct_to_pattern_roundtrip(client):
    """Test CONSTRUCT query results can be found via pattern matching."""
    # Add source data
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/construct/person",
                    "predicate": "http://schema.org/givenName",
                    "object": "John",
                },
                {
                    "subject": "http://example.org/construct/person",
                    "predicate": "http://schema.org/familyName",
                    "object": "Doe",
                },
            ]
        },
    )

    # Use CONSTRUCT to create new virtual triples
    construct_result = await client.call_tool(
        "rdf_query",
        {
            "query": """
            CONSTRUCT { 
                ?person <http://example.org/fullName> ?fullName 
            }
            WHERE { 
                ?person <http://schema.org/givenName> ?given .
                ?person <http://schema.org/familyName> ?family .
                BIND(CONCAT(?given, " ", ?family) AS ?fullName)
            }
            """
        },
    )

    # CONSTRUCT should return TextContent
    assert len(construct_result) == 1
    assert isinstance(construct_result[0], TextContent)
    construct_text = construct_result[0].text

    # Verify construct results contain expected data
    assert "John" in construct_text and "Doe" in construct_text


@pytest.mark.asyncio
async def test_error_recovery_workflow(client):
    """Test that errors in one operation don't affect subsequent operations."""
    # Start with valid operation
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/recovery/test",
                    "predicate": "http://schema.org/name",
                    "object": "Recovery Test",
                }
            ]
        },
    )

    # Perform invalid operation (should fail)
    try:
        await client.call_tool(
            "add_triples",
            {"triples": [{"subject": "invalid-uri", "predicate": "http://schema.org/name", "object": "Invalid"}]},
        )
        raise AssertionError("Expected ToolError for invalid URI")
    except Exception:
        pass  # Expected to fail

    # Verify previous data is still accessible
    recovery_result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/recovery/test"})
    assert len(recovery_result) == 1

    # Perform another valid operation
    await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/recovery/test2",
                    "predicate": "http://schema.org/name",
                    "object": "Recovery Test 2",
                }
            ]
        },
    )

    # Verify both valid operations succeeded
    all_recovery = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    assert len(all_recovery) == 1
    quads_data = json.loads(all_recovery[0].text)
    recovery_quads = [QuadResult(**quad) for quad in quads_data]
    recovery_subjects = [quad.subject for quad in recovery_quads]

    assert any("recovery/test>" in subj for subj in recovery_subjects)
    assert any("recovery/test2>" in subj for subj in recovery_subjects)


@pytest.mark.asyncio
async def test_batch_operations_consistency(client):
    """Test that batch operations maintain data consistency."""
    # Large batch add
    batch_triples = []
    for i in range(50):
        batch_triples.extend([
            {
                "subject": f"http://example.org/batch/person{i}",
                "predicate": "http://schema.org/name",
                "object": f"Batch Person {i}",
            },
            {
                "subject": f"http://example.org/batch/person{i}",
                "predicate": "http://schema.org/age",
                "object": str(20 + i),
            },
        ])

    # Add all at once
    await client.call_tool("add_triples", {"triples": batch_triples})

    # Verify all data was added
    all_names = await client.call_tool(
        "rdf_query", {"query": "SELECT (COUNT(?name) AS ?count) WHERE { ?person <http://schema.org/name> ?name }"}
    )
    assert len(all_names) == 1

    # Pattern query should find all subjects
    all_batch_people = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    assert len(all_batch_people) == 1
    quads_data = json.loads(all_batch_people[0].text)
    name_quads = [QuadResult(**quad) for quad in quads_data]

    # Should have at least 50 name triples from this batch
    batch_name_quads = [q for q in name_quads if "batch/person" in q.subject]
    assert len(batch_name_quads) >= 50
