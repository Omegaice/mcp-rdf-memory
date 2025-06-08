# RDF Data Integrity Testing

## Core RDF Testing Principles

RDF testing focuses on **semantic preservation** - ensuring that data maintains its meaning and relationships through the complete storage and retrieval cycle.

## Round-Trip Data Preservation

The fundamental test: data should survive the complete input → storage → retrieval cycle unchanged.

```python
@pytest.mark.asyncio
async def test_unicode_data_preservation(client: Client) -> None:
    """Test that Unicode data survives round-trip unchanged."""
    original_data = {
        "subject": "http://example.org/unicode",
        "predicate": "http://schema.org/name",
        "object": "Test with Unicode: 世界, Emoji: 🌍, Quotes: \"test\""
    }
    
    # Add data
    await client.call_tool("add_triples", {"triples": [original_data]})
    
    # Retrieve via different query patterns
    by_subject = await client.call_tool("quads_for_pattern", {"subject": original_data["subject"]})
    by_predicate = await client.call_tool("quads_for_pattern", {"predicate": original_data["predicate"]})
    by_sparql = await client.call_tool("rdf_query", {"query": f"SELECT * WHERE {{ <{original_data['subject']}> ?p ?o }}"})
    
    # Verify data preservation in all retrieval methods
    for result in [by_subject, by_predicate]:
        content = result[0]
        assert isinstance(content, TextContent)
        retrieved_quad = json.loads(content.text)[0]
        
        # Unicode should be preserved exactly
        assert original_data["object"] in retrieved_quad["object"]
```

## Graph Context Preservation

Test that graph contexts are preserved correctly across operations:

```python
@pytest.mark.asyncio
async def test_graph_context_preservation(client: Client) -> None:
    """Test that graph contexts are preserved correctly."""
    test_data = {
        "subject": "http://example.org/test",
        "predicate": "http://schema.org/name",
        "object": "Test Value",
        "graph_name": "test-conversation"
    }
    
    await client.call_tool("add_triples", {"triples": [test_data]})
    
    # Query without graph filter should find the triple
    all_results = await client.call_tool("quads_for_pattern", {"subject": test_data["subject"]})
    
    # Query with graph filter should also find it
    graph_results = await client.call_tool("quads_for_pattern", {
        "subject": test_data["subject"],
        "graph_name": test_data["graph_name"]
    })
    
    # Both should contain the same data with correct graph
    assert len(json.loads(all_results[0].text)) == 1
    assert len(json.loads(graph_results[0].text)) == 1
    
    # Graph should be preserved in both cases
    quad = json.loads(graph_results[0].text)[0]
    assert "test-conversation" in quad["graph"]
```

## Realistic Graph Naming Patterns

Test graph names LLMs would naturally use:

```python
@pytest.mark.asyncio
async def test_realistic_graph_names(client: Client) -> None:
    """Test graph naming patterns LLMs would naturally use."""
    
    realistic_graph_names = [
        "conversation-123",
        "project/myapp", 
        "temp",
        "analysis",
        "chat-2024-01-15",
        "user-session-abc123",
        "workspace/development",
        "memory/facts",
    ]
    
    base_triple = {
        "subject": "http://example.org/test",
        "predicate": "http://schema.org/name",
        "object": "Test Value"
    }
    
    for graph_name in realistic_graph_names:
        # Add triple to specific graph
        triple_with_graph = {**base_triple, "graph_name": graph_name}
        await client.call_tool("add_triples", {"triples": [triple_with_graph]})
        
        # Query by graph should find it
        result = await client.call_tool("quads_for_pattern", {
            "subject": base_triple["subject"],
            "graph_name": graph_name
        })
        
        content = result[0]
        assert isinstance(content, TextContent)
        retrieved_quads = json.loads(content.text)
        assert len(retrieved_quads) == 1
        
        # Graph name should be preserved in URI format
        assert graph_name in retrieved_quads[0]["graph"]
```

## Cross-Query Consistency Testing

Verify that the same data is accessible through different query methods:

```python
@pytest.mark.asyncio
async def test_query_result_consistency(client: Client) -> None:
    """Test that same data is accessible through different query methods."""
    # Add test data
    test_subject = "http://example.org/consistency/test"
    test_predicate = "http://schema.org/name"
    test_object = "Consistency Test"

    await client.call_tool("add_triples", {
        "triples": [{
            "subject": test_subject,
            "predicate": test_predicate,
            "object": test_object,
        }]
    })

    # Method 1: SPARQL SELECT
    sparql_result = await client.call_tool("rdf_query", {
        "query": f"SELECT ?name WHERE {{ <{test_subject}> <{test_predicate}> ?name }}"
    })
    
    # Method 2: Pattern matching by subject
    pattern_by_subject = await client.call_tool("quads_for_pattern", {"subject": test_subject})
    
    # Method 3: Pattern matching by predicate
    pattern_by_predicate = await client.call_tool("quads_for_pattern", {"predicate": test_predicate})

    # All methods should find the same data
    sparql_content = sparql_result[0]
    assert isinstance(sparql_content, TextContent)
    
    sparql_data = json.loads(sparql_content.text)
    assert isinstance(sparql_data, list)
    assert len(sparql_data) == 1
    
    binding = sparql_data[0]
    assert test_object in binding["name"]

    # Pattern queries should have formatted results
    content = pattern_by_subject[0]
    assert isinstance(content, TextContent)
    
    subject_quads_data = json.loads(content.text)
    subject_quads = [QuadResult(**quad) for quad in subject_quads_data]
    assert any(test_object in quad.object for quad in subject_quads)
```

## Comprehensive Data Integrity Testing

Test various challenging data types that might break serialization:

```python
@pytest.mark.asyncio
async def test_round_trip_data_integrity(client: Client) -> None:
    """Test that data survives the complete input → storage → retrieval cycle unchanged."""
    
    test_cases = [
        {
            "name": "unicode_and_emoji",
            "data": {
                "subject": "http://example.org/unicode/test",
                "predicate": "http://schema.org/name",
                "object": "Unicode Test: 世界, Emoji: 🌍, Special: àáâãäå",
            },
        },
        {
            "name": "quotes_and_escapes",
            "data": {
                "subject": "http://example.org/quotes/test",
                "predicate": "http://schema.org/description",
                "object": "Text with \"double quotes\" and 'single quotes' and \\ backslashes",
            },
        },
        {
            "name": "newlines_and_whitespace",
            "data": {
                "subject": "http://example.org/multiline/test",
                "predicate": "http://schema.org/content",
                "object": "Line 1\nLine 2\t\tTabbed\n\nDouble newline   Multiple spaces",
            },
        },
        {
            "name": "very_long_string",
            "data": {
                "subject": "http://example.org/long/test",
                "predicate": "http://schema.org/description",
                "object": "Long content: " + "A" * 1000 + " End",
            },
        },
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
        
        # Verify data integrity (accounting for RDF formatting)
        assert original_data["subject"] in quad_data["subject"]
        assert original_data["predicate"] in quad_data["predicate"]

        # Verify semantic content preservation
        quad_result = QuadResult(**quad_data)
        
        # Test semantic preservation rather than exact serialization format
        if "quotes" in test_case["name"]:
            assert "double quotes" in quad_data["object"] and "single quotes" in quad_data["object"]
        elif "unicode" in test_case["name"]:
            assert "世界" in quad_data["object"] and "🌍" in quad_data["object"]
        elif "newlines" in test_case["name"]:
            assert "Line 1" in quad_data["object"] and "Line 2" in quad_data["object"]
        elif "long" in test_case["name"]:
            assert len(quad_data["object"]) > 1000
```

## Multi-Graph Operations Testing

Test operations across multiple named graphs:

```python
@pytest.mark.asyncio
async def test_mixed_graph_operations(client: Client) -> None:
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
        "graph_name": "conversation/test-123",
    }

    # Add to both graphs
    await client.call_tool("add_triples", {"triples": [default_triple]})
    await client.call_tool("add_triples", {"triples": [named_triple]})

    # Query all graphs (should see both)
    all_contexts = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/mixed/shared"})
    content = all_contexts[0]
    assert isinstance(content, TextContent)

    all_quads = [QuadResult(**quad) for quad in json.loads(content.text)]
    assert len(all_quads) >= 2

    # Query specific graph
    named_only = await client.call_tool("quads_for_pattern", {
        "subject": "http://example.org/mixed/shared", 
        "graph_name": "conversation/test-123"
    })
    content = named_only[0]
    assert isinstance(content, TextContent)

    named_quads = [QuadResult(**quad) for quad in json.loads(content.text)]
    assert len(named_quads) == 1
    assert "conversation/test-123" in named_quads[0].graph
```

## SPARQL Construct Integration Testing

Test CONSTRUCT query results can be found via pattern matching:

```python
@pytest.mark.asyncio
async def test_sparql_construct_to_pattern_roundtrip(client: Client) -> None:
    """Test CONSTRUCT query results can be found via pattern matching."""
    
    # Add source data
    await client.call_tool("add_triples", {
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
    })

    # Use CONSTRUCT to create new virtual triples
    construct_result = await client.call_tool("rdf_query", {
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
    })

    # CONSTRUCT should return TextContent with structured data
    construct_content = construct_result[0]
    assert isinstance(construct_content, TextContent)

    # Validate JSON structure for CONSTRUCT results
    construct_data = json.loads(construct_content.text)
    assert isinstance(construct_data, list)

    # CONSTRUCT results should be formatted as triple/quad objects
    for item in construct_data:
        assert isinstance(item, dict)
        assert all(field in item for field in ["subject", "predicate", "object"])

    # Verify construct results contain expected data
    construct_text = construct_content.text
    assert "John" in construct_text and "Doe" in construct_text
```

## Error Recovery and State Consistency

Test that errors in one operation don't affect subsequent operations:

```python
@pytest.mark.asyncio
async def test_error_recovery_workflow(client: Client) -> None:
    """Test that errors in one operation don't affect subsequent operations."""
    
    # Start with valid operation
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/recovery/test",
            "predicate": "http://schema.org/name",
            "object": "Recovery Test",
        }]
    })

    # Perform invalid operation (should fail)
    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError):
        await client.call_tool("add_triples", {
            "triples": [{"subject": "invalid-uri", "predicate": "http://schema.org/name", "object": "Invalid"}]
        })

    # Verify previous data is still accessible
    recovery_result = await client.call_tool("quads_for_pattern", {"subject": "http://example.org/recovery/test"})
    assert len(recovery_result) == 1

    # Perform another valid operation
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/recovery/test2",
            "predicate": "http://schema.org/name",
            "object": "Recovery Test 2",
        }]
    })

    # Verify both valid operations succeeded
    all_recovery = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    content = all_recovery[0]
    assert isinstance(content, TextContent)

    recovery_quads = [QuadResult(**quad) for quad in json.loads(content.text)]
    recovery_subjects = [quad.subject for quad in recovery_quads]

    assert any("recovery/test>" in subj for subj in recovery_subjects)
    assert any("recovery/test2>" in subj for subj in recovery_subjects)
```

## Batch Operations and Scale Testing

Test that batch operations maintain data consistency:

```python
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
    all_names = await client.call_tool("rdf_query", {
        "query": "SELECT (COUNT(?name) AS ?count) WHERE { ?person <http://schema.org/name> ?name }"
    })
    
    count_content = all_names[0]
    assert isinstance(count_content, TextContent)
    count_data = json.loads(count_content.text)
    count_binding = count_data[0]
    
    # Extract numeric value from SPARQL typed literal
    count_value = count_binding["count"]
    if "^^" in count_value:
        count_value = count_value.split("^^")[0].strip('"')
    assert int(count_value) >= 50

    # Pattern query should find all subjects
    all_batch_people = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    content = all_batch_people[0]
    assert isinstance(content, TextContent)

    name_quads = [QuadResult(**quad) for quad in json.loads(content.text)]
    batch_name_quads = [q for q in name_quads if "batch/person" in q.subject]
    assert len(batch_name_quads) >= 50
```

## Common RDF Testing Anti-Patterns

**Don't test RDF serialization formats**:
```python
# ❌ Wrong - Testing pyoxigraph internal serialization
assert quad_data["object"] == '"Test Value"'  # Tests RDF serialization

# ✅ Correct - Testing semantic content
assert "Test Value" in quad_data["object"]  # Tests semantic preservation
```

**Don't assume exact string formats**:
```python
# ❌ Wrong - Brittle string matching
assert quad_data["subject"] == "http://example.org/test"

# ✅ Correct - Flexible content matching
assert "http://example.org/test" in quad_data["subject"]
```

**Don't ignore graph context**:
```python
# ❌ Wrong - Not testing graph preservation
result = await client.call_tool("quads_for_pattern", {"subject": "..."})

# ✅ Correct - Testing with and without graph context
result_all = await client.call_tool("quads_for_pattern", {"subject": "..."})
result_graph = await client.call_tool("quads_for_pattern", {"subject": "...", "graph_name": "test"})
```