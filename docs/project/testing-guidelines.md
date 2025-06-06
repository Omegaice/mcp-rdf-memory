# Testing Guidelines for MCP RDF Memory

## Quick Reference
- **MCP Contract Testing**: Only use native `dict` inputs, validate JSON output structure
- **RDF Data Integrity**: Test round-trip preservation of triples and semantic consistency
- **SPARQL Security**: Test both allowed queries and blocked modification attempts
- **Realism Check**: Can LLMs actually call this tool with this input in production?
- **Bug Rule**: NEVER modify tests to accommodate bugs

## Test Naming Patterns
- `test_add_triples_should_preserve_data_when_valid_input()` - Positive scenarios
- `test_sparql_query_should_reject_modification_when_insert_attempted()` - Security validation
- `test_add_triples_should_fail_validation_when_invalid_uri()` - Input validation
- `test_round_trip_should_preserve_unicode_when_special_characters()` - Data integrity

## Writing Realistic MCP Tool Tests

### Core Principle: Tests Must Reflect Real LLM Usage

### CRITICAL RULE: Never Modify Tests Just To Make Them Pass

**Tests should NEVER be updated to accommodate bugs in the application code.**

When a test fails, there are only two valid reasons to modify it:
1. **The test itself is incorrect** - it has wrong assumptions, unrealistic scenarios, or incorrect assertions
2. **Requirements have legitimately changed** - the expected behavior has actually changed

**NEVER modify a test because:**
- The application has a bug and the test correctly catches it
- The test is "inconvenient" because it reveals problems
- You want to make the build green quickly

**Process for failing tests:**
1. **Analyze the failure** - Is the test correctly written and realistic?
2. **Identify the root cause** - Is this a bug in the code or an issue with the test?
3. **If the test is correct** - Document that it catches a real bug, don't modify it
4. **If the test is wrong** - Explain why it's wrong and get confirmation before changing it

**Example:**
```python
# This test SHOULD fail if the application has a bug
@pytest.mark.asyncio
async def test_add_triples_should_preserve_unicode_data(client: Client) -> None:
    """Test should fail if Unicode handling is broken."""
    original_data = {
        "subject": "http://example.org/test",
        "predicate": "http://schema.org/name",
        "object": "Test with Unicode: 世界, Emoji: 🌍"
    }
    
    # If this fails, it means the application isn't preserving Unicode correctly
    # DO NOT change the test - FIX the application bug
    await client.call_tool("add_triples", {"triples": [original_data]})
    
    result = await client.call_tool("quads_for_pattern", {"subject": original_data["subject"]})
    # This assertion should fail if Unicode is corrupted
    assert original_data["object"] in json.loads(result[0].text)[0]["object"]
```

### Test the Right Abstraction Level for MCP Tools

**DO test MCP tool contracts and behavior:**
- "When I add triples, they should be queryable via SPARQL"
- "The tool should return valid JSON that reconstructs to proper objects"
- "SPARQL queries should be validated for security"
- "URI validation should reject invalid schemes"

**DON'T test pyoxigraph implementation details:**
- "The internal store should use specific indexing" (implementation detail)
- "This specific pyoxigraph method should be called" (internal detail)
- "The RDF object should be stored in this specific format" (internal detail)

### MCP Tool Contract Testing Strategy

#### Always Use Native Dict Inputs
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

#### Validate Complete JSON Pipeline
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

### RDF Data Integrity Testing

#### Round-Trip Data Preservation
```python
# ✅ CORRECT - Test complete data preservation cycle
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
    by_sparql = await client.call_tool("sparql_query", {"query": f"SELECT * WHERE {{ <{original_data['subject']}> ?p ?o }}"})
    
    # Verify data preservation in all retrieval methods
    for result in [by_subject, by_predicate]:
        content = result[0]
        assert isinstance(content, TextContent)
        retrieved_quad = json.loads(content.text)[0]
        
        # Unicode should be preserved exactly
        assert original_data["object"] in retrieved_quad["object"]
```

#### Graph Context Preservation
```python
# ✅ CORRECT - Test graph context handling
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

### SPARQL Security Testing

#### Modification Query Blocking
```python
# ✅ CORRECT - Test security validation for each forbidden operation
@pytest.mark.parametrize("forbidden_keyword", [
    "INSERT", "DELETE", "DROP", "CLEAR", "CREATE", "LOAD", "COPY", "MOVE", "ADD"
])
@pytest.mark.asyncio
async def test_sparql_query_should_reject_modification_operations(client: Client, forbidden_keyword: str) -> None:
    """Test that modification queries are properly blocked."""
    malicious_query = f"{forbidden_keyword} DATA {{ <http://example.org/test> <http://schema.org/name> \"hacked\" }}"
    
    with pytest.raises(ToolError) as exc_info:
        await client.call_tool("sparql_query", {"query": malicious_query})
    
    # Verify error message mentions the forbidden operation
    assert forbidden_keyword.lower() in str(exc_info.value).lower()
    assert "forbidden" in str(exc_info.value).lower()
```

#### Case Sensitivity Security
```python
# ✅ CORRECT - Test case variations of forbidden operations
@pytest.mark.asyncio
async def test_sparql_query_should_reject_case_variations(client: Client) -> None:
    """Test that case variations of forbidden operations are blocked."""
    case_variations = [
        "insert data { <http://test> <http://test> \"test\" }",
        "Insert Data { <http://test> <http://test> \"test\" }",
        "INSERT data { <http://test> <http://test> \"test\" }",
        "iNsErT dAtA { <http://test> <http://test> \"test\" }"
    ]
    
    for query in case_variations:
        with pytest.raises(ToolError):
            await client.call_tool("sparql_query", {"query": query})
```

### Input Validation Testing

#### Realistic Malformed Input Testing
```python
# ✅ CORRECT - Test validation with inputs LLMs might actually send
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

### Tool Error Validation Testing

#### Natural Error Triggering
```python
# ✅ CORRECT - Let validation naturally trigger errors
@pytest.mark.asyncio
async def test_uri_validation_natural_errors(client: Client) -> None:
    """Test that URI validation naturally triggers appropriate errors."""
    
    # Don't artificially inject errors - let real validation run
    invalid_inputs = [
        {"subject": "not-a-uri", "predicate": "http://schema.org/name", "object": "value"},
        {"subject": "http://example.org/test", "predicate": "invalid-predicate", "object": "value"},
        {"subject": "mailto:test@example.com", "predicate": "http://schema.org/name", "object": "value"},  # Wrong scheme
    ]
    
    for invalid_triple in invalid_inputs:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("add_triples", {"triples": [invalid_triple]})
        
        # Verify error provides actionable feedback
        assert "uri" in str(exc_info.value).lower()

# ❌ WRONG - Artificial error injection
# Don't manually create ToolError objects in tests
```

### Edge Case Testing for RDF Data

#### Unicode and Special Character Handling
```python
# ✅ CORRECT - Test realistic problematic data
@pytest.mark.asyncio
async def test_special_character_handling(client: Client) -> None:
    """Test handling of Unicode, quotes, and special characters."""
    
    edge_cases = [
        # Unicode from different languages
        {"subject": "http://example.org/unicode", "predicate": "http://schema.org/name", "object": "测试 Test тест"},
        
        # Emoji and symbols
        {"subject": "http://example.org/emoji", "predicate": "http://schema.org/description", "object": "Test with emoji: 🌍🔥💯"},
        
        # Quotes and escaping
        {"subject": "http://example.org/quotes", "predicate": "http://schema.org/note", "object": "Text with \"quotes\" and 'apostrophes'"},
        
        # Long strings (test serialization limits)
        {"subject": "http://example.org/long", "predicate": "http://schema.org/content", "object": "A" * 10000},
        
        # Special RDF characters
        {"subject": "http://example.org/special", "predicate": "http://schema.org/value", "object": "Text with <brackets> and & ampersands"},
        
        # Newlines and whitespace
        {"subject": "http://example.org/whitespace", "predicate": "http://schema.org/text", "object": "Text with\nnewlines\tand\ttabs"},
    ]
    
    for test_case in edge_cases:
        # Should not raise errors for valid Unicode
        await client.call_tool("add_triples", {"triples": [test_case]})
        
        # Verify round-trip preservation
        result = await client.call_tool("quads_for_pattern", {"subject": test_case["subject"]})
        content = result[0]
        assert isinstance(content, TextContent)
        
        retrieved_quad = json.loads(content.text)[0]
        # Original data should be preserved (accounting for RDF serialization)
        assert test_case["object"] in retrieved_quad["object"] or test_case["object"] == retrieved_quad["object"].strip('"')
```

### Graph Name Testing

#### Realistic Graph Naming Patterns
```python
# ✅ CORRECT - Test graph names LLMs would actually use
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

### Test Structure Pattern for MCP Tools

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

### When Bug Fixes Break Tests (This is Normal!)

When you fix bugs in application code, tests may break. This is **expected and appropriate** when:

1. **The test was checking behavior that was buggy**
2. **New validation is added** and stricter checking is needed
3. **Error message formats change** and assertions need updating

**This is DIFFERENT from accommodating bugs. Examples:**

✅ **Legitimate test updates after bug fixes:**
```python
# Before fix: App accepted invalid URIs silently
# After fix: App properly validates URIs - test needs to expect validation error

# CORRECT update after fixing validation bug:
with pytest.raises(ToolError) as exc_info:
    await client.call_tool("add_triples", {"triples": [{"subject": "invalid-uri", "predicate": "http://valid", "object": "valid"}]})
assert "uri" in str(exc_info.value).lower()
```

❌ **Accommodating bugs (DON'T do this):**
```python
# Wrong: Changing expected behavior to match buggy code
retrieved_data = json.loads(result[0].text)
assert retrieved_data == []  # Expecting bug that loses data!
```

### Common Anti-Patterns to Avoid

```python
# ❌ Don't bypass MCP input validation
test_input = TripleModel(...)  # Use dict instead

# ❌ Don't skip JSON structure validation
quads = [QuadResult(**item) for item in json.loads(content.text)]  # Validate JSON first

# ❌ Don't test with unrealistic inputs
{"subject": "perfect-uri", "predicate": "perfect-predicate", "object": "perfect-object"}  # Too perfect

# ❌ Don't ignore SPARQL security testing
# Always test that modification queries are properly blocked

# ❌ Don't test only happy paths
# Include edge cases, malformed inputs, and error conditions

# ❌ Don't assume TextContent without checking
result_text = result[0].text  # Check isinstance(result[0], TextContent) first
```

## Systematic Test Realism Analysis

### CRITICAL MANDATE: Validate EVERY Test for Realism

When working on tests, you MUST systematically analyze each test to ensure it represents scenarios that can actually occur with LLM usage.

### 1. **Test Realism Validation Process**

For each test, systematically ask:

**A. LLM Usage Possibility**
- Would Claude or another LLM actually call this tool with this input?
- Does the test use input patterns that LLMs naturally generate?
- Are we testing edge cases that could happen in real conversations?

**B. MCP Contract Accuracy**
- Does the test use the exact JSON structure that MCP would send?
- Are we validating the complete tool input/output pipeline?
- Do we test serialization of complex RDF data correctly?

**C. RDF Semantic Consistency**
- Does the test preserve RDF semantics throughout operations?
- Are we testing realistic URI patterns and graph structures?
- Do SPARQL queries match patterns LLMs would generate?

**D. Security Coverage**
- Are we testing SPARQL injection attempts that could realistically occur?
- Do we verify that modification queries are properly blocked?
- Are edge cases in security validation covered?

### 2. **Test Analysis Template**

Use this template when analyzing test files:

```
## Test File: [FileName]
### Realism Analysis:

**LLM Usage Realism**: [Would LLMs actually use these patterns?]
**MCP Contract Accuracy**: [Does input/output match real MCP usage?]  
**RDF Semantic Preservation**: [Are RDF semantics maintained correctly?]
**Security Coverage**: [Are realistic attack vectors tested?]
**Data Integrity**: [Is round-trip preservation verified?]

**Issues Found**: [List specific anti-patterns discovered]
**Recommended Fixes**: [Specific changes needed for realism]
**Priority**: [Critical/Medium/Low based on production risk]
```

### 3. **Quality Gates for Test Changes**

**BEFORE committing any test changes:**
1. Run realism analysis on all modified tests
2. Verify tests use native dict inputs, not Pydantic models
3. Confirm SPARQL security testing covers realistic attack patterns
4. Validate that error conditions are triggered naturally
5. Ensure round-trip data integrity testing is comprehensive

**Remember**: The goal is tests that catch actual bugs and reflect real LLM interactions with the MCP RDF Memory server, not artificial scenarios that pass by luck.