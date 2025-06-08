# Input Validation Testing

## Core Input Validation Principles

Input validation testing ensures that tools properly handle realistic malformed inputs that LLMs might generate, while providing helpful error messages for debugging.

## Realistic Malformed Input Testing

Test validation with inputs LLMs might actually send:

```python
@pytest.mark.asyncio
async def test_add_triples_input_validation(client: Client) -> None:
    """Test validation with realistic malformed inputs."""
    
    # Test cases that LLMs might actually generate
    malformed_inputs = [
        # Missing required fields (LLM forgets predicate)
        {"triples": [{"subject": "http://example.org/test", "object": "value"}]},
        
        # Invalid URI schemes (LLM uses common but invalid schemes)
        {"triples": [{"subject": "ftp://example.org/test", "predicate": "http://schema.org/name", "object": "value"}]},
        {"triples": [{"subject": "example.org/test", "predicate": "http://schema.org/name", "object": "value"}]},  # Missing scheme
        
        # Empty strings (LLM sends empty values)
        {"triples": [{"subject": "", "predicate": "http://schema.org/name", "object": "value"}]},
        {"triples": [{"subject": "http://example.org/test", "predicate": "", "object": "value"}]},
        
        # Wrong data types (LLM sends string instead of list)
        {"triples": "not-a-list"},
        
        # Missing triples field entirely (LLM sends wrong structure)
        {"data": [{"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "value"}]},
        
        # Nested objects instead of flat structure (LLM overcomplicates)
        {"triples": [{"triple": {"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "value"}}]},
    ]
    
    for malformed_input in malformed_inputs:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("add_triples", malformed_input)
        
        # Verify error messages are helpful for debugging
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["invalid", "required", "missing", "uri"])
```

## URI Validation Testing

Test URI validation with realistic invalid patterns:

```python
@pytest.mark.asyncio
async def test_uri_validation_natural_errors(client: Client) -> None:
    """Test that URI validation naturally triggers appropriate errors."""
    
    # Don't artificially inject errors - let real validation run
    invalid_inputs = [
        {"subject": "not-a-uri", "predicate": "http://schema.org/name", "object": "value"},
        {"subject": "http://example.org/test", "predicate": "invalid-predicate", "object": "value"},
        {"subject": "mailto:test@example.com", "predicate": "http://schema.org/name", "object": "value"},  # Wrong scheme
        {"subject": "javascript:alert('xss')", "predicate": "http://schema.org/name", "object": "value"},  # Dangerous scheme
        {"subject": "file:///etc/passwd", "predicate": "http://schema.org/name", "object": "value"},  # Local file
        {"subject": "ftp://ftp.example.com/file", "predicate": "http://schema.org/name", "object": "value"},  # Unsupported scheme
        {"subject": "ldap://ldap.example.com/", "predicate": "http://schema.org/name", "object": "value"},  # Unsupported scheme
    ]
    
    for invalid_triple in invalid_inputs:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("add_triples", {"triples": [invalid_triple]})
        
        # Verify error provides actionable feedback
        assert "uri" in str(exc_info.value).lower()
```

## Comprehensive Malformed Input Matrix

Test systematic input validation across different tools:

```python
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
        
        # Null values (LLM sends null instead of omitting)
        {"triples": [{"subject": "http://valid.example.org/subj", "predicate": None, "object": "valid"}]},
        
        # Wrong nesting structure
        {"triples": [{"data": {"subject": "http://valid.example.org/subj", "predicate": "http://valid.example.org/pred", "object": "valid"}}]},
        
        # Array instead of object
        {"triples": [["http://valid.example.org/subj", "http://valid.example.org/pred", "valid"]]},
        
        # Mixed valid and invalid in batch
        {"triples": [
            {"subject": "http://valid.example.org/subj1", "predicate": "http://valid.example.org/pred", "object": "valid"},
            {"subject": "invalid-uri", "predicate": "http://valid.example.org/pred", "object": "valid"}
        ]},
    ]

    for malformed_input in malformed_inputs:
        with pytest.raises(ToolError):
            await client.call_tool("add_triples", malformed_input)
```

## Query Parameter Validation

Test validation for query tools with malformed parameters:

```python
@pytest.mark.asyncio
async def test_query_parameter_validation(client: Client) -> None:
    """Test validation of query parameters with realistic malformed inputs."""
    
    # Test quads_for_pattern with invalid parameters
    invalid_query_params = [
        # Empty parameters
        {},
        
        # Invalid URI in subject
        {"subject": "not-a-uri"},
        
        # Invalid URI in predicate
        {"predicate": "invalid-predicate"},
        
        # Wrong data types
        {"subject": 123},
        {"predicate": ["http://example.org/pred"]},
        {"object": {"value": "test"}},
        
        # Null values
        {"subject": None, "predicate": "http://schema.org/name"},
        
        # Empty strings where URIs expected
        {"subject": "", "predicate": "http://schema.org/name"},
        {"subject": "http://example.org/test", "predicate": ""},
        
        # Whitespace-only values
        {"subject": "   ", "predicate": "http://schema.org/name"},
        
        # Mixed valid and invalid
        {"subject": "http://valid.example.org/test", "predicate": "invalid-predicate"},
    ]
    
    for invalid_params in invalid_query_params:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("quads_for_pattern", invalid_params)
        
        # Error should mention validation issue
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["invalid", "uri", "required", "validation"])
```

## SPARQL Query Validation

Test SPARQL query validation with realistic malformed queries:

```python
@pytest.mark.asyncio
async def test_sparql_query_validation(client: Client) -> None:
    """Test SPARQL query validation with realistic syntax errors."""
    
    # Add some test data first for context
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/test",
            "predicate": "http://schema.org/name",
            "object": "Test Value"
        }]
    })
    
    malformed_sparql_queries = [
        # Empty query
        "",
        
        # Whitespace only
        "   ",
        
        # Incomplete syntax (LLM cuts off)
        "SELECT ?name WHERE {",
        
        # Missing WHERE clause
        "SELECT ?name { ?s <http://schema.org/name> ?name }",
        
        # Invalid syntax (missing brackets)
        "SELECT ?name WHERE ?s <http://schema.org/name> ?name",
        
        # Unmatched quotes
        "SELECT ?name WHERE { ?s <http://schema.org/name> \"unclosed quote }",
        
        # Invalid URI syntax
        "SELECT ?name WHERE { ?s <invalid-uri> ?name }",
        
        # Missing required elements
        "WHERE { ?s <http://schema.org/name> ?name }",
        
        # Typos in keywords (LLM makes mistakes)
        "SELCT ?name WHERE { ?s <http://schema.org/name> ?name }",
        "SELECT ?name WHRE { ?s <http://schema.org/name> ?name }",
        
        # Wrong case for required keywords
        "select ?name where { ?s <http://schema.org/name> ?name }",  # Some SPARQL parsers are case-sensitive
        
        # Invalid variable names
        "SELECT ?123invalid WHERE { ?123invalid <http://schema.org/name> ?name }",
        
        # Missing prefixes for namespace
        "SELECT ?name WHERE { ?s schema:name ?name }",  # Missing PREFIX declaration
    ]
    
    for malformed_query in malformed_sparql_queries:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("rdf_query", {"query": malformed_query})
        
        # Should provide helpful syntax error
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["syntax", "invalid", "query", "sparql", "parse"])
```

## Graph Name Validation

Test graph name validation with realistic patterns:

```python
@pytest.mark.asyncio
async def test_graph_name_validation(client: Client) -> None:
    """Test graph name validation with realistic edge cases."""
    
    base_triple = {
        "subject": "http://example.org/test",
        "predicate": "http://schema.org/name",
        "object": "Test Value"
    }
    
    # Invalid graph names that might be sent by LLMs
    invalid_graph_names = [
        "",  # Empty string
        "   ",  # Whitespace only
        "\n\t",  # Control characters
        None,  # Null value (though this might be valid for default graph)
        123,  # Wrong type
        [],  # Wrong type
        {"name": "test"},  # Wrong type
    ]
    
    for invalid_graph_name in invalid_graph_names:
        if invalid_graph_name is None:
            # None might be valid for default graph - test separately
            continue
            
        triple_with_invalid_graph = {**base_triple, "graph_name": invalid_graph_name}
        
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("add_triples", {"triples": [triple_with_invalid_graph]})
        
        # Should mention graph name validation
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["graph", "name", "invalid", "empty"])
```

## Batch Operation Validation

Test validation in batch operations where some items are valid and others invalid:

```python
@pytest.mark.asyncio
async def test_batch_validation_behavior(client: Client) -> None:
    """Test how validation behaves with mixed valid/invalid batches."""
    
    # Test mixed batch with valid and invalid triples
    mixed_batch = {
        "triples": [
            # Valid triple
            {
                "subject": "http://example.org/valid1",
                "predicate": "http://schema.org/name",
                "object": "Valid Person 1"
            },
            # Invalid triple (bad URI)
            {
                "subject": "not-a-uri",
                "predicate": "http://schema.org/name",
                "object": "Invalid Person"
            },
            # Another valid triple
            {
                "subject": "http://example.org/valid2",
                "predicate": "http://schema.org/name",
                "object": "Valid Person 2"
            }
        ]
    }
    
    # Entire batch should fail due to one invalid item
    with pytest.raises(ToolError) as exc_info:
        await client.call_tool("add_triples", mixed_batch)
    
    # Should mention validation failure
    error_msg = str(exc_info.value).lower()
    assert any(keyword in error_msg for keyword in ["invalid", "uri", "validation"])
    
    # Verify no partial data was added (atomic operation)
    result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    
    # Should be empty since entire batch failed
    if isinstance(result, list):
        assert len(result) == 0
    else:
        # If there's existing data, ensure our test data wasn't added
        content = result[0]
        assert isinstance(content, TextContent)
        existing_quads = json.loads(content.text)
        
        # None of our test subjects should be present
        test_subjects = ["http://example.org/valid1", "http://example.org/valid2"]
        for quad in existing_quads:
            assert not any(subj in quad["subject"] for subj in test_subjects)
```

## Error Message Quality Testing

Ensure validation errors provide helpful debugging information:

```python
@pytest.mark.asyncio
async def test_validation_error_message_quality(client: Client) -> None:
    """Test that validation error messages provide helpful information."""
    
    test_cases = [
        {
            "input": {"triples": [{"subject": "not-a-uri", "predicate": "http://schema.org/name", "object": "value"}]},
            "expected_keywords": ["uri", "invalid", "subject"],
            "description": "Invalid URI in subject"
        },
        {
            "input": {"triples": [{"subject": "http://example.org/test", "object": "value"}]},
            "expected_keywords": ["predicate", "required", "missing"],
            "description": "Missing required predicate field"
        },
        {
            "input": {"triples": "should-be-list"},
            "expected_keywords": ["triples", "list", "array", "type"],
            "description": "Wrong type for triples field"
        },
        {
            "input": {},
            "expected_keywords": ["triples", "required", "missing"],
            "description": "Missing triples field entirely"
        },
        {
            "input": {"triples": [{"subject": "", "predicate": "http://schema.org/name", "object": "value"}]},
            "expected_keywords": ["subject", "empty", "uri"],
            "description": "Empty subject field"
        },
    ]
    
    for test_case in test_cases:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("add_triples", test_case["input"])
        
        error_message = str(exc_info.value).lower()
        
        # Should contain at least 2 of the expected keywords
        found_keywords = [kw for kw in test_case["expected_keywords"] if kw in error_message]
        assert len(found_keywords) >= 2, f"Error for {test_case['description']} missing keywords. Got: {error_message}"
        
        # Should not expose internal implementation details
        internal_details = ["pydantic", "fastmcp", "pyoxigraph", "validation_error", "traceback"]
        exposed_details = [detail for detail in internal_details if detail in error_message]
        assert len(exposed_details) == 0, f"Error message exposed internal details: {exposed_details}"
        
        # Should be reasonably concise (not a huge stack trace)
        assert len(error_message) < 500, f"Error message too verbose: {len(error_message)} chars"
```

## Natural Error Triggering Philosophy

The key principle is to let validation naturally trigger errors rather than artificially creating them:

```python
# ✅ CORRECT - Let validation naturally trigger errors
@pytest.mark.asyncio
async def test_natural_validation_errors(client: Client) -> None:
    """Test that validation naturally triggers appropriate errors."""
    
    # Don't artificially inject errors - let real validation run
    invalid_inputs = [
        {"subject": "not-a-uri", "predicate": "http://schema.org/name", "object": "value"},
        {"subject": "http://example.org/test", "predicate": "invalid-predicate", "object": "value"},
        {"subject": "mailto:test@example.com", "predicate": "http://schema.org/name", "object": "value"},
    ]
    
    for invalid_triple in invalid_inputs:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("add_triples", {"triples": [invalid_triple]})
        
        # Verify error provides actionable feedback
        assert "uri" in str(exc_info.value).lower()

# ❌ WRONG - Artificial error injection
# Don't manually create ToolError objects in tests
def test_artificial_errors():
    # This doesn't test real validation behavior
    raise ToolError("Artificial error for testing")
```

## Common Input Validation Anti-Patterns

**Don't test with perfect inputs only**:
```python
# ❌ Wrong - Only testing happy paths
{"subject": "http://perfect.example.org/uri", "predicate": "http://perfect.example.org/predicate", "object": "perfect value"}

# ✅ Correct - Testing realistic malformed inputs
{"subject": "example.org/missing-scheme", "predicate": "http://schema.org/name", "object": "realistic mistake"}
```

**Don't bypass input validation in tests**:
```python
# ❌ Wrong - Using pre-validated objects
triple = TripleModel(subject="http://example.org/test", predicate="http://schema.org/name", object="value")

# ✅ Correct - Using raw dict that goes through validation
triple_dict = {"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "value"}
```

**Don't test with artificial edge cases**:
```python
# ❌ Wrong - Artificial edge case that won't occur
{"subject": "urn:malformed:::invalid", "predicate": "http://schema.org/name", "object": "value"}

# ✅ Correct - Realistic mistake LLMs make
{"subject": "http://example.org/test", "predicate": "schema:name", "object": "value"}  # Missing namespace prefix
```

**Don't ignore error message quality**:
```python
# ❌ Wrong - Only testing that errors occur
with pytest.raises(ToolError):
    await client.call_tool("add_triples", invalid_input)

# ✅ Correct - Testing error message usefulness
with pytest.raises(ToolError) as exc_info:
    await client.call_tool("add_triples", invalid_input)
assert "helpful keyword" in str(exc_info.value).lower()
```