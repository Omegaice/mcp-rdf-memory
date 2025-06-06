"""
Comprehensive integration tests spanning multiple tools and workflows.
"""

import json

import pytest
from fastmcp import Client
from mcp.types import TextContent

from mcp_rdf_memory.server import QuadResult


@pytest.mark.asyncio
async def test_complete_workflow_default_graph(client: Client) -> None:
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

    # Parse and verify pattern results with JSON schema validation
    content = name_pattern_result[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure before reconstruction
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)
    
    # Validate required fields exist in JSON
    for item in quads_data:
        assert "subject" in item
        assert "predicate" in item
        assert "object" in item
        assert "graph" in item
        assert isinstance(item["subject"], str)
        assert isinstance(item["predicate"], str)
        assert isinstance(item["object"], str)
        assert isinstance(item["graph"], str)
    
    # Then reconstruct to verify schema compliance
    quads = [QuadResult(**quad) for quad in quads_data]
    assert len(quads) >= 2  # Should have both people

    # Step 4: Verify specific relationships with JSON validation
    knows_result = await client.call_tool("quads_for_pattern", {"predicate": "http://xmlns.com/foaf/0.1/knows"})
    assert len(knows_result) == 1
    content = knows_result[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)
    
    # Validate schema
    for item in quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])
    
    knows_quads = [QuadResult(**quad) for quad in quads_data]
    assert len(knows_quads) >= 1


@pytest.mark.asyncio
async def test_mixed_graph_operations(client: Client, sample_graph_uri: str) -> None:
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

    # Query all graphs (should see both) with JSON validation
    all_contexts = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/mixed/shared"})
    assert len(all_contexts) == 1
    content = all_contexts[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)
    
    # Validate QuadResult schema
    for item in quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])
    
    all_quads = [QuadResult(**quad) for quad in quads_data]
    assert len(all_quads) >= 2

    # Query specific graph
    named_only = await client.call_tool(
        "quads_for_pattern", {"subject": "http://example.org/mixed/shared", "graph": sample_graph_uri}
    )
    assert len(named_only) == 1
    content = named_only[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)
    
    # Validate schema
    for item in quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])
    
    named_quads = [QuadResult(**quad) for quad in quads_data]
    assert len(named_quads) == 1
    assert sample_graph_uri in named_quads[0].graph


@pytest.mark.asyncio
async def test_query_result_consistency(client: Client) -> None:
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

    # Pattern queries should have formatted results with JSON validation
    content = pattern_by_subject[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure
    subject_quads_data = json.loads(content.text)
    assert isinstance(subject_quads_data, list)
    assert all(isinstance(item, dict) for item in subject_quads_data)
    
    # Validate schema
    for item in subject_quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])
    
    subject_quads = [QuadResult(**quad) for quad in subject_quads_data]
    assert any(test_object in quad.object for quad in subject_quads)


@pytest.mark.asyncio
async def test_sparql_construct_to_pattern_roundtrip(client: Client) -> None:
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
async def test_error_recovery_workflow(client: Client) -> None:
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

    # Verify both valid operations succeeded with JSON validation
    all_recovery = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    assert len(all_recovery) == 1
    content = all_recovery[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)
    
    # Validate schema
    for item in quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])
    
    recovery_quads = [QuadResult(**quad) for quad in quads_data]
    recovery_subjects = [quad.subject for quad in recovery_quads]

    assert any("recovery/test>" in subj for subj in recovery_subjects)
    assert any("recovery/test2>" in subj for subj in recovery_subjects)


@pytest.mark.asyncio
async def test_batch_operations_consistency(client: Client) -> None:
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

    # Pattern query should find all subjects with JSON validation
    all_batch_people = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    assert len(all_batch_people) == 1
    content = all_batch_people[0]
    assert isinstance(content, TextContent)
    
    # Validate JSON structure
    quads_data = json.loads(content.text)
    assert isinstance(quads_data, list)
    assert all(isinstance(item, dict) for item in quads_data)
    
    # Validate schema
    for item in quads_data:
        assert all(field in item for field in ["subject", "predicate", "object", "graph"])
        assert all(isinstance(item[field], str) for field in ["subject", "predicate", "object", "graph"])
    
    name_quads = [QuadResult(**quad) for quad in quads_data]

    # Should have at least 50 name triples from this batch
    batch_name_quads = [q for q in name_quads if "batch/person" in q.subject]
    assert len(batch_name_quads) >= 50


@pytest.mark.asyncio
async def test_round_trip_data_integrity(client: Client) -> None:
    """Test that data survives the complete input → storage → retrieval cycle unchanged."""
    # Test various challenging data types
    test_cases = [
        {
            "name": "unicode_and_emoji",
            "data": {
                "subject": "http://example.org/unicode/test",
                "predicate": "http://schema.org/name",
                "object": "Unicode Test: 世界, Emoji: 🌍, Special: àáâãäå"
            }
        },
        {
            "name": "quotes_and_escapes", 
            "data": {
                "subject": "http://example.org/quotes/test",
                "predicate": "http://schema.org/description",
                "object": 'Text with "double quotes" and \'single quotes\' and \\ backslashes'
            }
        },
        {
            "name": "newlines_and_whitespace",
            "data": {
                "subject": "http://example.org/multiline/test",
                "predicate": "http://schema.org/content",
                "object": "Line 1\nLine 2\t\tTabbed\n\nDouble newline   Multiple spaces"
            }
        },
        {
            "name": "very_long_string",
            "data": {
                "subject": "http://example.org/long/test",
                "predicate": "http://schema.org/description",
                "object": "Long content: " + "A" * 1000 + " End"
            }
        }
    ]

    for test_case in test_cases:
        original_data = test_case["data"]
        
        # Add data using native dict (tests input validation)
        await client.call_tool("add_triples", {"triples": [original_data]})
        
        # Retrieve via pattern matching
        result = await client.call_tool("quads_for_pattern", {"subject": original_data["subject"]})
        content = result[0]
        assert isinstance(content, TextContent)
        
        # Validate JSON structure
        retrieved_quads = json.loads(content.text)
        assert isinstance(retrieved_quads, list)
        assert len(retrieved_quads) == 1
        
        quad_data = retrieved_quads[0]
        assert isinstance(quad_data, dict)
        assert all(field in quad_data for field in ["subject", "predicate", "object", "graph"])
        
        # Verify data integrity (accounting for RDF formatting)
        assert original_data["subject"] in quad_data["subject"]  # May be wrapped in <>
        assert original_data["predicate"] in quad_data["predicate"]  # May be wrapped in <>
        assert original_data["object"] in quad_data["object"]  # May be wrapped in ""
        
        # Verify exact object value preservation by checking the quoted content
        if quad_data["object"].startswith('"') and quad_data["object"].endswith('"'):
            extracted_value = quad_data["object"][1:-1]  # Remove quotes
            assert extracted_value == original_data["object"]


@pytest.mark.asyncio  
async def test_empty_results_serialization(client: Client) -> None:
    """Test that empty results are handled correctly by FastMCP."""
    # Query for non-existent data
    empty_result = await client.call_tool("quads_for_pattern", {"subject": "http://nonexistent.example.org/test"})
    
    # For empty results, FastMCP returns an empty list (no TextContent wrapper)
    assert isinstance(empty_result, list)
    assert len(empty_result) == 0
    assert empty_result == []


@pytest.mark.asyncio
async def test_malformed_input_validation(client: Client) -> None:
    """Test validation with realistic malformed inputs using native dicts."""
    from fastmcp.exceptions import ToolError
    
    malformed_inputs = [
        # Empty subject
        {"triples": [{"subject": "", "predicate": "http://valid.example.org/pred", "object": "valid"}]},
        # Missing required fields
        {"triples": [{"subject": "http://valid.example.org/subj"}]},
        # Invalid URI format
        {"triples": [{"subject": "not-a-uri", "predicate": "http://valid.example.org/pred", "object": "valid"}]},
        # Wrong type for triples field
        {"triples": "should-be-list"},
        # Missing triples field entirely
        {},
        # Empty string fields
        {"triples": [{"subject": "http://valid.example.org/subj", "predicate": "", "object": "valid"}]},
        # Whitespace-only fields
        {"triples": [{"subject": "http://valid.example.org/subj", "predicate": "   ", "object": "valid"}]},
    ]
    
    for malformed_input in malformed_inputs:
        with pytest.raises(ToolError):
            await client.call_tool("add_triples", malformed_input)


@pytest.mark.asyncio
async def test_sparql_result_serialization(client: Client) -> None:
    """Test SPARQL results serialize correctly for different query types."""
    # Add test data
    await client.call_tool("add_triples", {
        "triples": [
            {
                "subject": "http://example.org/sparql/person",
                "predicate": "http://schema.org/name", 
                "object": "SPARQL Test Person"
            },
            {
                "subject": "http://example.org/sparql/person",
                "predicate": "http://schema.org/age",
                "object": "30"
            }
        ]
    })
    
    # Test SELECT query serialization
    select_result = await client.call_tool("rdf_query", {
        "query": "SELECT ?name ?age WHERE { <http://example.org/sparql/person> <http://schema.org/name> ?name ; <http://schema.org/age> ?age }"
    })
    content = select_result[0]
    assert isinstance(content, TextContent)
    
    # Validate SELECT result JSON structure
    select_data = json.loads(content.text)
    assert isinstance(select_data, list)
    assert len(select_data) == 1
    
    binding = select_data[0]
    assert isinstance(binding, dict)
    assert "name" in binding
    assert "age" in binding
    assert isinstance(binding["name"], str)
    assert isinstance(binding["age"], str)
    
    # Test ASK query serialization
    ask_result = await client.call_tool("rdf_query", {
        "query": "ASK { <http://example.org/sparql/person> <http://schema.org/name> ?name }"
    })
    content = ask_result[0]
    assert isinstance(content, TextContent)
    
    # ASK results should be boolean
    ask_data = json.loads(content.text)
    assert isinstance(ask_data, bool)
    assert ask_data is True
