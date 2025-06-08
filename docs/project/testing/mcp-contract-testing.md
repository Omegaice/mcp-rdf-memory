# MCP Tool Contract Testing

## Core MCP Testing Strategy

MCP tools must handle the complete pipeline: Raw JSON Input → Validation → Processing → JSON Output

Test each stage and the complete pipeline to ensure LLMs can reliably interact with your tools.

## Always Use Native Dict Inputs

**The fundamental rule**: Test with the exact input format that MCP actually sends.

```python
# ✅ CORRECT - Tests real MCP input validation
await client.call_tool("add_triples", {
    "triples": [
        {
            "subject": "http://example.org/test",
            "predicate": "http://schema.org/name", 
            "object": "Test Value"
        }
    ]
})

# ❌ WRONG - Bypasses MCP input validation
triple = TripleModel(subject="...", predicate="...", object="...")
await client.call_tool("add_triples", {"triples": [triple]})
```

**Why this matters**: LLMs send raw JSON dictionaries, not pre-validated Pydantic models. Your tests must validate the same input path.

## Validate Complete JSON Pipeline

Every MCP tool test should verify the complete JSON serialization pipeline:

```python
# ✅ CORRECT - Test complete JSON serialization pipeline
result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
content = result[0]
assert isinstance(content, TextContent)

# 1. Validate raw JSON structure
raw_data = json.loads(content.text)
assert isinstance(raw_data, list)
assert all(isinstance(item, dict) for item in raw_data)

# 2. Validate required fields exist
for item in raw_data:
    assert "subject" in item
    assert "predicate" in item
    assert "object" in item
    assert "graph" in item

# 3. Verify reconstruction works
quads = [QuadResult(**quad) for quad in raw_data]

# ❌ WRONG - Skips JSON validation
raw_data = json.loads(content.text)
quads = [QuadResult(**quad) for quad in raw_data]  # Assumes JSON is valid
```

## Standard MCP Tool Test Pattern

Use this template for comprehensive MCP tool testing:

```python
@pytest.mark.asyncio
async def test_mcp_tool_comprehensive_pattern(client: Client) -> None:
    """Comprehensive MCP tool test following best practices."""
    
    # 1. Use realistic native dict input (what LLMs actually send)
    input_data = {
        "triples": [
            {
                "subject": "http://example.org/realistic-test",
                "predicate": "http://schema.org/name",
                "object": "Test with realistic data"
            }
        ]
    }
    
    # 2. Execute MCP tool
    result = await client.call_tool("add_triples", input_data)
    
    # 3. Validate MCP response structure
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, TextContent)
    
    # 4. Validate that operation succeeded (for add operations)
    assert "successfully" in content.text.lower() or "added" in content.text.lower()
    
    # 5. Verify data integrity via query
    query_result = await client.call_tool("quads_for_pattern", {"subject": input_data["triples"][0]["subject"]})
    query_content = query_result[0]
    assert isinstance(query_content, TextContent)
    
    # 6. Validate JSON serialization from query
    raw_json = json.loads(query_content.text)
    assert isinstance(raw_json, list)
    assert len(raw_json) == 1
    
    # 7. Validate JSON schema compliance
    quad_data = raw_json[0]
    required_fields = ["subject", "predicate", "object", "graph"]
    for field in required_fields:
        assert field in quad_data, f"Missing required field: {field}"
    
    # 8. Test reconstruction works
    validated_quad = QuadResult(**quad_data)
    
    # 9. Verify data integrity preservation
    assert input_data["triples"][0]["subject"] in quad_data["subject"]
    assert input_data["triples"][0]["predicate"] in quad_data["predicate"]
    assert input_data["triples"][0]["object"] in quad_data["object"]
```

## Tool Response Validation

### Standard Response Patterns

Different tools return different response formats - test the appropriate pattern:

**Add Operations** (like `add_triples`):
```python
result = await client.call_tool("add_triples", input_data)
content = result[0]
assert isinstance(content, TextContent)
assert "successfully" in content.text.lower() or "added" in content.text.lower()
```

**Query Operations** (like `quads_for_pattern`):
```python
result = await client.call_tool("quads_for_pattern", query_params)

# Empty results - FastMCP returns empty list directly
if isinstance(result, list) and len(result) == 0:
    assert result == []
    return

# Non-empty results - FastMCP wraps in TextContent
content = result[0]
assert isinstance(content, TextContent)
raw_data = json.loads(content.text)
assert isinstance(raw_data, list)
```

**SPARQL Query Operations**:
```python
result = await client.call_tool("rdf_query", {"query": sparql_query})
content = result[0]
assert isinstance(content, TextContent)

# Validate based on query type
data = json.loads(content.text)
if "ASK" in sparql_query.upper():
    assert isinstance(data, bool)
elif "SELECT" in sparql_query.upper():
    assert isinstance(data, list)
    # Validate variable bindings structure
    for binding in data:
        assert isinstance(binding, dict)
```

## Error Response Validation

Test that errors are properly handled and provide useful feedback:

```python
# ✅ CORRECT - Let validation naturally trigger errors
from fastmcp.exceptions import ToolError

with pytest.raises(ToolError) as exc_info:
    await client.call_tool("add_triples", malformed_input)

# Verify error message is helpful
error_msg = str(exc_info.value).lower()
assert any(keyword in error_msg for keyword in ["invalid", "required", "missing", "uri"])

# ❌ WRONG - Artificial error injection
# Don't manually create ToolError objects in tests
```

## Testing Framework-Specific Behaviors

### FastMCP Response Patterns

**Empty Results**:
```python
# When tools return None or empty lists, FastMCP behavior varies
empty_result = await client.call_tool("quads_for_pattern", {"subject": "http://nonexistent.example.org/test"})

# Empty results return as empty list directly (no TextContent wrapper)
assert isinstance(empty_result, list)
assert len(empty_result) == 0
assert empty_result == []
```

**List Results**:
```python
# Non-empty results get JSON serialized in TextContent
result = await client.call_tool("quads_for_pattern", valid_query)
content = result[0]
assert isinstance(content, TextContent)

# Always validate JSON structure before using
raw_data = json.loads(content.text)
assert isinstance(raw_data, list)
```

## Cross-Tool Data Consistency

Test that data added via one tool is accessible via other tools:

```python
@pytest.mark.asyncio
async def test_cross_tool_data_consistency(client: Client) -> None:
    """Test that data is consistent across different tool queries."""
    
    # Add data via add_triples
    test_subject = "http://example.org/consistency/test"
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": test_subject,
            "predicate": "http://schema.org/name",
            "object": "Consistency Test"
        }]
    })
    
    # Query via quads_for_pattern
    pattern_result = await client.call_tool("quads_for_pattern", {"subject": test_subject})
    
    # Query via SPARQL
    sparql_result = await client.call_tool("rdf_query", {
        "query": f"SELECT ?name WHERE {{ <{test_subject}> <http://schema.org/name> ?name }}"
    })
    
    # Both should find the same data
    assert len(pattern_result) == 1
    assert len(sparql_result) == 1
    
    # Validate data consistency
    pattern_data = json.loads(pattern_result[0].text)[0]
    sparql_data = json.loads(sparql_result[0].text)[0]
    
    assert "Consistency Test" in pattern_data["object"]
    assert "Consistency Test" in sparql_data["name"]
```

## Test Naming Conventions

Use descriptive names that indicate the scenario and expected outcome:

- `test_add_triples_should_preserve_data_when_valid_input()` - Positive scenarios
- `test_quads_for_pattern_should_return_empty_when_no_matches()` - Boundary conditions
- `test_add_triples_should_fail_validation_when_invalid_uri()` - Input validation
- `test_rdf_query_should_reject_modification_when_insert_attempted()` - Security validation

## Performance and Scale Testing

Test realistic data volumes and concurrent operations:

```python
@pytest.mark.asyncio
async def test_batch_operations_performance(client: Client) -> None:
    """Test tool performance with realistic batch sizes."""
    
    # Test with batch sizes LLMs might actually send
    batch_sizes = [1, 5, 20, 50]
    
    for batch_size in batch_sizes:
        batch_triples = []
        for i in range(batch_size):
            batch_triples.append({
                "subject": f"http://example.org/batch/item{i}",
                "predicate": "http://schema.org/name",
                "object": f"Batch Item {i}"
            })
        
        # Should handle batches without timing out
        result = await client.call_tool("add_triples", {"triples": batch_triples})
        assert isinstance(result[0], TextContent)
        
        # Verify all data was added
        query_result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
        if isinstance(query_result, list):
            continue  # Empty results
            
        content = query_result[0]
        assert isinstance(content, TextContent)
        retrieved_quads = json.loads(content.text)
        batch_items = [q for q in retrieved_quads if "batch/item" in q["subject"]]
        assert len(batch_items) >= batch_size
```

## Common MCP Testing Anti-Patterns

**Don't bypass MCP input validation**:
```python
# ❌ Wrong
test_input = TripleModel(...)

# ✅ Correct  
test_input = {"subject": "...", "predicate": "...", "object": "..."}
```

**Don't skip JSON structure validation**:
```python
# ❌ Wrong
quads = [QuadResult(**item) for item in json.loads(content.text)]

# ✅ Correct
raw_data = json.loads(content.text)
assert isinstance(raw_data, list)
quads = [QuadResult(**quad) for quad in raw_data]
```

**Don't assume response types**:
```python
# ❌ Wrong
result_text = result[0].text

# ✅ Correct
content = result[0]
assert isinstance(content, TextContent)
result_text = content.text
```