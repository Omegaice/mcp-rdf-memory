# Core Testing Principles

## The Golden Rule: Never Modify Tests Just To Make Them Pass

**Tests should NEVER be updated to accommodate bugs in the application code.**

When a test fails, there are only two valid reasons to modify it:
1. **The test itself is incorrect** - it has wrong assumptions, unrealistic scenarios, or incorrect assertions
2. **Requirements have legitimately changed** - the expected behavior has actually changed

**NEVER modify a test because:**
- The application has a bug and the test correctly catches it
- The test is "inconvenient" because it reveals problems
- You want to make the build green quickly

### Process for Failing Tests

1. **Analyze the failure** - Is the test correctly written and realistic?
2. **Identify the root cause** - Is this a bug in the code or an issue with the test?
3. **If the test is correct** - Document that it catches a real bug, don't modify it
4. **If the test is wrong** - Explain why it's wrong and get confirmation before changing it

### Example: Proper Response to Test Failure

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

## Test the Right Abstraction Level

**DO test MCP tool contracts and behavior:**
- "When I add triples, they should be queryable via SPARQL"
- "The tool should return valid JSON that reconstructs to proper objects"
- "SPARQL queries should be validated for security"
- "URI validation should reject invalid schemes"

**DON'T test pyoxigraph implementation details:**
- "The internal store should use specific indexing" (implementation detail)
- "This specific pyoxigraph method should be called" (internal detail)
- "The RDF object should be stored in this specific format" (internal detail)

### Focus on Contracts, Not Implementation

Test the abstraction level that LLMs interact with - the MCP tool contracts. Don't test how the underlying frameworks (FastMCP, pyoxigraph) implement their functionality.

## LLM-Centric Testing Philosophy

### The Realism Check

Every test must pass this fundamental question:
**"Can LLMs actually call this tool with this input in production?"**

This means:
- Use native dict inputs that MCP actually sends
- Test malformed inputs LLMs might generate
- Validate complete input/output pipelines
- Focus on scenarios that happen in real conversations

### Test Realistic Scenarios, Not Perfect Ones

```python
# ✅ CORRECT - Test realistic LLM input patterns
malformed_inputs = [
    {"triples": "should-be-list"},  # LLM sends wrong type
    {"triples": [{"subject": "example.org/missing-scheme", ...}]},  # LLM forgets protocol
    {"data": [...]},  # LLM uses wrong field name
]

# ❌ WRONG - Artificial perfect scenarios
perfect_input = {"subject": "perfect-uri", "predicate": "perfect-predicate", ...}
```

## When Bug Fixes Break Tests (This is Normal!)

When you fix bugs in application code, tests may break. This is **expected and appropriate** when:

1. **The test was checking behavior that was buggy**
2. **New validation is added** and stricter checking is needed
3. **Error message formats change** and assertions need updating

**This is DIFFERENT from accommodating bugs.**

### Examples

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

## Universal Anti-Patterns to Avoid

### Don't Bypass Validation
```python
# ❌ Wrong - Bypasses MCP input validation
test_input = TripleModel(...)  # Use dict instead

# ✅ Correct - Tests real MCP input validation
await client.call_tool("add_triples", {"triples": [{"subject": "...", ...}]})
```

### Don't Skip JSON Structure Validation
```python
# ❌ Wrong - Skips JSON validation
quads = [QuadResult(**item) for item in json.loads(content.text)]

# ✅ Correct - Validate JSON structure first
raw_data = json.loads(content.text)
assert isinstance(raw_data, list)
assert all(isinstance(item, dict) for item in raw_data)
quads = [QuadResult(**quad) for quad in raw_data]
```

### Don't Test with Unrealistic Inputs
```python
# ❌ Wrong - Too perfect to be realistic
{"subject": "perfect-uri", "predicate": "perfect-predicate", "object": "perfect-object"}

# ✅ Correct - Realistic inputs LLMs might generate
{"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "Real Value"}
```

### Don't Assume Response Types
```python
# ❌ Wrong - Assumes TextContent without checking
result_text = result[0].text

# ✅ Correct - Validate response type first
content = result[0]
assert isinstance(content, TextContent)
result_text = content.text
```

## Quality Gates

**BEFORE committing any test changes:**
1. Run realism analysis on all modified tests
2. Verify tests use native dict inputs, not Pydantic models
3. Confirm tests reflect realistic LLM usage patterns
4. Validate that error conditions are triggered naturally
5. Ensure the test catches real bugs and isn't accommodating them

**Remember**: The goal is tests that catch actual bugs and reflect real LLM interactions, not artificial scenarios that pass by luck.