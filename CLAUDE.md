# MCP RDF Memory Server

## Project Overview
Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.

## Core Stack
- **FastMCP**: MCP server framework
- **Pyoxigraph**: RDF triple store with SPARQL 1.1
- **UV**: Package manager

## Essential Commands

```bash
# Development server
uv run fastmcp dev src/mcp_rdf_memory/server.py:mcp

# Run tests
uv run pytest

# Lint and fix code
uv run ruff check --fix

# Format code
uv run ruff format

# Install for Claude Desktop
uv run fastmcp install src/mcp_rdf_memory/server.py:mcp --name "RDF Memory"
```

## Key Patterns

### Named Graphs for Context
- Conversations: `<http://mcp.local/conversation/{id}>`
- Projects: `<http://mcp.local/project/{id}>`

### Error Handling
```python
from fastmcp import ToolError

# Always use ToolError for user-facing errors with proper exception chaining
try:
    results = store.query(query)
except ValueError as e:
    raise ToolError(f"Invalid SPARQL query syntax: {e}") from e
except Exception as e:
    raise ToolError(f"Failed to execute SPARQL query: {e}") from e

# Validate queries (read-only) using constants
for keyword in FORBIDDEN_SPARQL_KEYWORDS:
    if keyword in query.upper():
        raise ToolError(f"Modification queries not allowed. '{keyword}' operations are forbidden.")
```

### Code Quality & Type Safety

#### Use Specific Types, Avoid Any
```python
# Good: Specific union types
def format_rdf_object(obj: NamedNode | Literal | BlankNode | Triple) -> str:

# Bad: Generic Any type
def format_rdf_object(obj: Any) -> str:
```

#### Use isinstance() Instead of hasattr()
```python
# Good: Type-based checking
if isinstance(obj, NamedNode):
    return f"<{obj.value}>"
if isinstance(obj, Literal):
    return f'"{obj.value}"'

# Bad: Runtime attribute checking
if hasattr(obj, "value"):
    return f"<{obj.value}>"
```

#### Early Returns for Clarity
```python
# Good: Early returns, no unnecessary defaults
def format_predicate(predicate: NamedNode | BlankNode) -> str:
    if isinstance(predicate, NamedNode):
        return f"<{predicate.value}>"
    # BlankNode case - we know this is the only other type
    return f"_:{predicate.value}"

# Bad: Nested if-elif-else with unnecessary fallback
def format_predicate(predicate):
    if isinstance(predicate, NamedNode):
        return f"<{predicate.value}>"
    elif isinstance(predicate, BlankNode):
        return f"_:{predicate.value}"
    else:
        return str(predicate)  # Unnecessary when types are known
```

### RDF Node Handling

#### Helper Functions for Formatting
- `format_subject()` - Handles NamedNode, BlankNode, Triple subjects
- `format_predicate()` - Handles NamedNode, BlankNode predicates  
- `format_rdf_object()` - Handles NamedNode, Literal, BlankNode, Triple objects
- `format_triple()` - Combines all formatting with graph support

#### DefaultGraph vs Named Graphs
```python
# DefaultGraph has no .value attribute - handle explicitly
if quad.graph_name is None or isinstance(quad.graph_name, DefaultGraph):
    graph_name = "default graph"
else:
    graph_name = quad.graph_name.value
```

#### URI Validation
```python
# Use constants and helper functions
URI_SCHEMES = ("http://", "https://")

def validate_uri(uri: str, context: str = "URI") -> None:
    if not uri.startswith(URI_SCHEMES):
        raise ToolError(f"{context} must be a valid HTTP(S) URI")
```

### Constants
```python
# URI validation
URI_SCHEMES = ("http://", "https://")

# SPARQL security - modification operations not allowed
FORBIDDEN_SPARQL_KEYWORDS = ["INSERT", "DELETE", "DROP", "CLEAR", "CREATE", "LOAD", "COPY", "MOVE", "ADD"]
```

## Tool Development Guidelines

### Function Structure
```python
@mcp.tool()
def tool_name(params: TypedModel) -> str:
    """Clear docstring describing the tool's purpose."""
    try:
        # Main logic with proper error handling
        # Use helper functions for complex operations
        return "Success message with details"
    
    except ToolError:
        # Re-raise ToolErrors as-is to preserve context
        raise
    except SpecificError as e:
        raise ToolError(f"Specific error message: {e}") from e
    except Exception as e:
        raise ToolError(f"Unexpected error: {e}") from e
```

### Empty Input Handling
```python
# Don't validate against empty lists - handle gracefully
# ❌ Bad: if not items: raise ToolError("No items provided")
# ✅ Good: Let empty lists process normally and return appropriate success message
```

## Server Entry Point
`src/mcp_rdf_memory/server.py:mcp` - FastMCP server instance

## Testing Best Practices

### Core Testing Principles

**Test the Contract, Not Implementation**: MCP tools have JSON input/output contracts. Test that data survives the full pipeline correctly without making assumptions about internal representations.

**Use Native Python Data Structures**: Always test with raw `dict` objects, not Pydantic models. This ensures we're testing real-world usage patterns and input validation.

### Input Validation Testing

```python
# ✅ Good: Test with native dict - tests real MCP input
await client.call_tool("add_triples", {
    "triples": [
        {
            "subject": "http://example.org/test",
            "predicate": "http://schema.org/name", 
            "object": "Test Value"
        }
    ]
})

# ❌ Bad: Testing with Pydantic models bypasses input validation
triple = TripleModel(subject="...", predicate="...", object="...")
await client.call_tool("add_triples", {"triples": [triple]})
```

### Output Serialization Validation

**Always validate the actual JSON structure**, not just reconstructed objects:

```python
# ✅ Good: Validate actual JSON structure before reconstruction
result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
content = result[0]
assert isinstance(content, TextContent)

# Parse and validate JSON structure
raw_data = json.loads(content.text)
assert isinstance(raw_data, list)
assert all(isinstance(item, dict) for item in raw_data)

# Validate required fields exist in JSON
for item in raw_data:
    assert "subject" in item
    assert "predicate" in item  
    assert "object" in item
    assert "graph" in item

# Then reconstruct to verify schema compliance
quads = [QuadResult(**quad) for quad in raw_data]

# ❌ Bad: Only testing reconstruction, not actual JSON output
raw_data = json.loads(content.text)
quads = [QuadResult(**quad) for quad in raw_data]  # Skips JSON validation
```

### Round-Trip Data Integrity Testing

Test that data survives the complete cycle unchanged:

```python
# ✅ Good: Round-trip integrity test
original_data = {
    "subject": "http://example.org/test",
    "predicate": "http://schema.org/name",
    "object": "Test Name with Unicode 🌍"
}

# Add data
await client.call_tool("add_triples", {"triples": [original_data]})

# Retrieve via pattern matching
result = await client.call_tool("quads_for_pattern", {"subject": original_data["subject"]})
content = result[0]
assert isinstance(content, TextContent)

retrieved_quads = json.loads(content.text)
assert len(retrieved_quads) == 1

quad = retrieved_quads[0]
# Verify exact data preservation (accounting for formatting)
assert original_data["subject"] in quad["subject"]  # May be wrapped in <>
assert original_data["predicate"] in quad["predicate"]
assert original_data["object"] in quad["object"]  # May be wrapped in ""
```

### Edge Case Testing

**Test serialization of problematic data**:

```python
# Unicode and special characters
unicode_test = {
    "subject": "http://example.org/unicode",
    "predicate": "http://schema.org/name", 
    "object": "Test with Unicode: 世界, Emoji: 🌍, Quotes: \"test\""
}

# Very long strings
long_string_test = {
    "subject": "http://example.org/long",
    "predicate": "http://schema.org/description",
    "object": "A" * 10000  # Test large data serialization
}

# Empty results
empty_result = await client.call_tool("quads_for_pattern", {"subject": "http://nonexistent"})
content = empty_result[0]
assert isinstance(content, TextContent)
assert json.loads(content.text) == []  # Verify empty list serializes correctly
```

### Malformed Input Testing

**Test validation with realistic malformed inputs**:

```python
# ✅ Good: Test actual malformed dict inputs
malformed_inputs = [
    {"triples": [{"subject": "", "predicate": "valid", "object": "valid"}]},  # Empty subject
    {"triples": [{"subject": "valid"}]},  # Missing required fields
    {"triples": [{"subject": "invalid-uri", "predicate": "valid", "object": "valid"}]},  # Invalid URI
    {"triples": "not-a-list"},  # Wrong type for triples
    {},  # Missing triples field
]

for malformed_input in malformed_inputs:
    with pytest.raises(ToolError):
        await client.call_tool("add_triples", malformed_input)
```

### Test Structure Pattern

```python
@pytest.mark.asyncio
async def test_tool_comprehensive(client: Client) -> None:
    """Comprehensive test following best practices."""
    
    # 1. Test with native dict input
    input_data = {"field": "value"}  # Raw dict, not Pydantic model
    
    # 2. Execute tool
    result = await client.call_tool("tool_name", input_data)
    
    # 3. Validate result structure
    assert len(result) == 1
    content = result[0] 
    assert isinstance(content, TextContent)
    
    # 4. Validate JSON serialization
    raw_json = json.loads(content.text)
    assert isinstance(raw_json, (list, dict))  # Expected JSON type
    
    # 5. Validate JSON schema
    # ... check required fields exist and have correct types
    
    # 6. Test reconstruction works
    validated_objects = [ModelClass(**item) for item in raw_json]
    
    # 7. Verify data integrity
    # ... assert original data values are preserved correctly
```

### Common Anti-Patterns to Avoid

```python
# ❌ Don't assume TextContent without checking
result_text = result[0].text  # Could fail if result[0] is ImageContent

# ❌ Don't skip JSON validation  
objects = [QuadResult(**item) for item in json.loads(content.text)]  # Skips structure validation

# ❌ Don't use hardcoded models in tests
test_input = TripleModel(...)  # Bypasses input validation

# ❌ Don't ignore empty result testing
# Always test tools with inputs that produce empty results

# ❌ Don't test only happy path
# Always include malformed input and edge case testing
```

## Debugging
- Use IDE diagnostics to identify and troubleshoot issues
- Run `uv run pytest -v` to test all functionality
- Use `uv run ruff check` for linting issues
- Check type annotations with IDE (Pylance) for type safety