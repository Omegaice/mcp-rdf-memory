# Testing Strategy and Hierarchy

## The Core Philosophy: Test Your Logic, Not the Language

The fundamental principle that guides all testing decisions: **Test the logic YOU wrote, not the behavior of the language, frameworks, or libraries.**

## The Testing Pyramid for MCP RDF Memory

### **End-to-End Tests** (Top of Pyramid)
**Purpose**: Guarantee complete LLM workflows work as intended
**When to write**: Multi-step scenarios that LLMs actually perform

```python
async def test_complete_conversation_workflow():
    """LLM adds knowledge, queries it, builds on it across multiple turns."""
    # Turn 1: LLM learns about a person
    await client.call_tool("add_triples", {...})
    
    # Turn 2: LLM queries to recall information
    result = await client.call_tool("rdf_query", {...})
    
    # Turn 3: LLM adds related information to same graph
    await client.call_tool("add_triples", {"graph_name": "conversation-123", ...})
    
    # Turn 4: LLM performs complex analysis with SPARQL
    analysis = await client.call_tool("rdf_query", {complex_analytical_query})
    
    # Verify: Complete semantic consistency across the workflow
```

### **Integration Tests** (Middle of Pyramid)
**Purpose**: Ensure MCP tools + business logic work together correctly
**When to write**: Tool contracts, component interactions, cross-tool data flow

```python
async def test_cross_tool_data_consistency():
    """Test that data added via one tool is accessible via others."""
    # Add via add_triples
    await client.call_tool("add_triples", test_data)
    
    # Query via quads_for_pattern
    pattern_result = await client.call_tool("quads_for_pattern", {...})
    
    # Query via SPARQL
    sparql_result = await client.call_tool("rdf_query", {...})
    
    # All should find the same data
```

### **Unit Tests** (Base of Pyramid)
**Purpose**: Ensure individual functions handle edge cases correctly
**When to write**: Only for complex logic YOU wrote

## When to Write Unit Tests vs When NOT To

### ✅ **Write Unit Tests For**

**Complex business logic with multiple paths**:
```python
def test_create_graph_uri_edge_cases():
    """Test graph URI creation with edge cases."""
    # Edge case: whitespace-only should error
    with pytest.raises(ToolError, match="empty"):
        create_graph_uri("   ")
    
    # Edge case: leading/trailing whitespace should be stripped
    result = create_graph_uri("  test-graph  ")
    assert result.value == "http://mcp.local/test-graph"
```

**Security-critical logic**:
```python
def test_sparql_comment_removal():
    """Test SPARQL security parsing with tricky inputs."""
    query = "SELECT * WHERE { # INSERT comment\n ?s ?p ?o }"
    cleaned = _remove_sparql_comments_and_strings(query)
    assert "INSERT" not in cleaned
```

**Validation functions with edge cases**:
```python
def test_validate_rdf_node_boundary_conditions():
    """Test validation edge cases that could break."""
    # Empty strings
    with pytest.raises(ValueError):
        validate_rdf_node("")
        
    # Whitespace only
    with pytest.raises(ValueError):
        validate_rdf_node("   ")
```

### ❌ **DON'T Write Unit Tests For**

**Type system guarantees**:
```python
# ❌ MEANINGLESS - Testing type annotation
def test_create_rdf_identifier_returns_named_node():
    result = create_rdf_identifier("http://example.org/test")
    assert isinstance(result, NamedNode)  # Type system guarantees this
```

**Library behavior**:
```python
# ❌ MEANINGLESS - Testing pyoxigraph behavior
def test_named_node_value_preservation():
    node = NamedNode("http://example.org/test")
    assert node.value == "http://example.org/test"  # Testing the library, not our code
```

**One-line wrappers with no logic**:
```python
# ❌ MEANINGLESS - No logic to test
def create_rdf_identifier(value: str) -> NamedNode:
    return NamedNode(value)  # One line, no branching, input already validated
```

**Implementation details**:
```python
# ❌ MEANINGLESS - Testing internal details
def test_store_uses_specific_indexing():
    # This tests pyoxigraph internals, not our logic
```

## The Meaningful vs Meaningless Test Framework

### Decision Tree

```
Is this function one line with no branching?
├─ YES → DON'T unit test (integration tests will catch issues)
└─ NO → Continue

Does this function have complex logic I wrote?
├─ YES → Continue  
└─ NO → DON'T unit test

Does this test implementation details vs behavior?
├─ Implementation → DON'T unit test
└─ Behavior → Continue

Would this test catch a bug that integration tests miss?
├─ YES → Write unit test
└─ NO → DON'T unit test
```

### Examples Applied to Our Codebase

**✅ `create_graph_uri()` - NEEDS UNIT TESTS**
```python
def create_graph_uri(graph_name: str | None) -> NamedNode | None:
    if graph_name is None:
        return None
    if not graph_name.strip():  # ← Complex logic we wrote
        raise ToolError("Graph name cannot be empty")  # ← Business rule we wrote
    return NamedNode(f"http://mcp.local/{graph_name.strip()}")  # ← URI construction logic we wrote
```
**Why test**: Multiple branches, error conditions, string manipulation logic.

**❌ `create_rdf_identifier()` - DON'T UNIT TEST**
```python
def create_rdf_identifier(value: str) -> NamedNode:
    return NamedNode(value)  # ← One line, no logic, input pre-validated
```
**Why not test**: No logic to break, integration tests catch any issues.

**✅ `_remove_sparql_comments_and_strings()` - NEEDS UNIT TESTS**
```python
def _remove_sparql_comments_and_strings(query: str) -> str:
    # Complex regex logic for security
    query = re.sub(r"#.*?$", " ", query, flags=re.MULTILINE)  # ← Complex logic we wrote
    query = re.sub(r"'[^']*'", " ", query)  # ← Multiple patterns
    # ... more complex regex patterns
    return query
```
**Why test**: Security-critical, complex regex logic, many edge cases.

**❌ `validate_rdf_identifier()` - QUESTIONABLE UNIT TESTS**
```python
def validate_rdf_identifier(value) -> str:
    # ... validation logic
    try:
        NamedNode(value)  # ← Testing pyoxigraph validation
        return value
    except ValueError as e:
        raise ValueError(f"Invalid RDF identifier: {e}") from e
```
**Why questionable**: Mostly testing pyoxigraph behavior. Integration tests cover this.

## Current Unit Test Gaps

Based on the analysis, we need unit tests for:

1. **`create_graph_uri()`** - Graph name transformation logic
2. **`_remove_sparql_comments_and_strings()`** - SPARQL security parsing
3. **Graph naming edge cases** - Whitespace handling, empty strings
4. **URI construction logic** - Namespace prefix handling

We DON'T need unit tests for:
- `create_rdf_identifier()` - One line wrapper
- `create_rdf_node()` - Mostly library behavior
- Type system guarantees - Already tested by type checker

## Integration with Testing Hierarchy

### Test Level Selection Guide

**End-to-End**: 
- Multi-tool workflows
- Complete conversation scenarios
- Cross-graph operations
- Performance at scale

**Integration**:
- MCP tool contracts
- JSON serialization pipelines
- Tool response validation
- Security boundaries

**Unit**:
- Complex helper functions
- Business logic with branches
- Security-critical parsing
- Edge case handling

## Common Anti-Patterns in Test Level Selection

**Testing at wrong level**:
```python
# ❌ Wrong level - This should be integration test
def test_add_triples_mcp_contract():
    model = TripleModel(...)  # Unit testing with pre-validated model
    
# ✅ Correct level - Integration test
async def test_add_triples_mcp_contract():
    await client.call_tool("add_triples", {...})  # Test real MCP contract
```

**Over-testing implementation details**:
```python
# ❌ Wrong focus - Testing framework internals
def test_pyoxigraph_storage_format():
    # Testing how pyoxigraph stores data internally
    
# ✅ Correct focus - Testing our business logic
def test_graph_uri_construction():
    # Testing our URI construction logic
```

**Under-testing complex logic**:
```python
# ❌ Missing tests for complex function
def complex_validation_logic(data):
    # 50 lines of complex validation
    # No unit tests = integration tests have to cover all edge cases
    
# ✅ Unit test complex logic
def test_complex_validation_edge_cases():
    # Test all the branches and edge cases
```

## Strategy Evolution

### As Project Grows
- **Start with integration tests** for new features
- **Add unit tests** only for complex logic
- **Add end-to-end tests** for major workflows
- **Remove meaningless tests** that don't catch bugs

### Red Flags for Over-Testing
- Tests that never fail when code changes
- Tests that test type system behavior
- Tests that duplicate integration test coverage
- Tests that test framework/library behavior

### Green Flags for Right-Level Testing
- Tests fail when business logic breaks
- Tests catch edge cases integration tests miss
- Tests document complex function behavior
- Tests prevent regressions in critical logic

This hierarchy ensures we test at the right level while avoiding the trap of meaningless unit tests that waste time without catching real bugs.