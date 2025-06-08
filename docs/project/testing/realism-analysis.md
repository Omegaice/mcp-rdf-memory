# Test Realism Analysis Framework

## Core Realism Principle

**Every test must pass this fundamental question**: "Can LLMs actually call this tool with this input in production?"

This framework provides systematic validation to ensure tests reflect real LLM interactions rather than artificial scenarios.

## CRITICAL MANDATE: Validate EVERY Test for Realism

When working on tests, you MUST systematically analyze each test to ensure it represents scenarios that can actually occur with LLM usage.

## Systematic Test Realism Validation Process

For each test, systematically ask these questions:

### A. LLM Usage Possibility
- Would Claude or another LLM actually call this tool with this input?
- Does the test use input patterns that LLMs naturally generate?
- Are we testing edge cases that could happen in real conversations?

### B. MCP Contract Accuracy
- Does the test use the exact JSON structure that MCP would send?
- Are we validating the complete tool input/output pipeline?
- Do we test serialization of complex RDF data correctly?

### C. RDF Semantic Consistency
- Does the test preserve RDF semantics throughout operations?
- Are we testing realistic URI patterns and graph structures?
- Do SPARQL queries match patterns LLMs would generate?

### D. Security Coverage
- Are we testing SPARQL injection attempts that could realistically occur?
- Do we verify that modification queries are properly blocked?
- Are edge cases in security validation covered?

## Test Analysis Template

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

## Detailed Realism Validation Criteria

### LLM Input Pattern Analysis

**✅ Realistic LLM Patterns**:
```python
# LLMs commonly make these mistakes
malformed_inputs = [
    {"triples": "should-be-list"},  # Wrong type
    {"triples": [{"subject": "missing-scheme.com", "predicate": "http://valid", "object": "value"}]},  # Forgets protocol
    {"data": [...]},  # Wrong field name
    {"triples": [{"subject": "http://valid", "object": "missing-predicate"}]},  # Forgets required field
]
```

**❌ Unrealistic Patterns**:
```python
# LLMs don't typically make these mistakes
artificial_inputs = [
    {"triples": [{"subject": "\x00\x01\x02", "predicate": "http://valid", "object": "value"}]},  # Binary data
    {"subject": "perfectly-formed-uri", "predicate": "perfectly-formed-predicate"},  # Too perfect
]
```

### MCP Contract Validation

**✅ Realistic MCP Usage**:
```python
# Test exactly what MCP sends
result = await client.call_tool("add_triples", {
    "triples": [{"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "value"}]
})

# Validate complete response pipeline
content = result[0]
assert isinstance(content, TextContent)
raw_json = json.loads(content.text)
assert isinstance(raw_json, list)
validated_objects = [QuadResult(**item) for item in raw_json]
```

**❌ Unrealistic MCP Usage**:
```python
# Bypasses MCP input validation
model = TripleModel(subject="...", predicate="...", object="...")
result = await client.call_tool("add_triples", {"triples": [model]})
```

### SPARQL Query Realism

**✅ Realistic LLM SPARQL**:
```python
# Queries LLMs actually generate
realistic_queries = [
    "SELECT ?name WHERE { ?person <http://schema.org/name> ?name }",  # Simple selection
    "ASK { <http://example.org/test> <http://schema.org/name> ?name }",  # Existence check
    "SELECT * WHERE { ?s ?p ?o } LIMIT 10",  # Exploration query
]
```

**❌ Unrealistic SPARQL**:
```python
# Queries LLMs are unlikely to generate
artificial_queries = [
    "SELECT ?x WHERE { ?x <http://perfect.ontology/property> ?y . FILTER(REGEX(?y, '^[A-Z]{3}$')) }",  # Too complex
]
```

### Error Scenario Realism

**✅ Realistic Error Scenarios**:
```python
# Errors that actually occur in practice
realistic_errors = [
    # LLM sends wrong data type
    {"triples": "not-a-list"},
    
    # LLM forgets URI scheme
    {"triples": [{"subject": "example.org/test", "predicate": "http://valid", "object": "value"}]},
    
    # LLM mixes up field names
    {"data": [{"subject": "http://test", "predicate": "http://valid", "object": "value"}]},
]
```

**❌ Artificial Error Scenarios**:
```python
# Errors that don't occur naturally
artificial_errors = [
    {"triples": [{"subject": 12345, "predicate": ["array"], "object": {"nested": "object"}}]},  # Too random
]
```

## Production Risk Assessment

### Critical Priority Issues
- Security vulnerabilities (SPARQL injection)
- Data corruption scenarios (Unicode handling)
- Input validation bypasses
- MCP contract violations

### Medium Priority Issues
- Error message quality
- Edge case handling
- Performance with realistic loads

### Low Priority Issues
- Extremely rare edge cases
- Perfect-world scenarios
- Academic completeness

## Quality Gates for Test Changes

**BEFORE committing any test changes:**

1. **Run realism analysis** on all modified tests
2. **Verify tests use native dict inputs**, not Pydantic models
3. **Confirm SPARQL security testing** covers realistic attack patterns
4. **Validate that error conditions** are triggered naturally
5. **Ensure round-trip data integrity testing** is comprehensive

## Systematic File-by-File Analysis

### Analysis Workflow

1. **Open test file**
2. **For each test function**:
   - Apply LLM usage possibility check
   - Verify MCP contract accuracy
   - Assess RDF semantic consistency
   - Evaluate security coverage
3. **Document findings** using analysis template
4. **Prioritize issues** by production risk
5. **Create action plan** for critical issues

### Common Realism Issues Found

**Input Validation Tests**:
- ✅ Good: Testing malformed JSON that LLMs send
- ❌ Issue: Testing binary data that LLMs never send

**Security Tests**:
- ✅ Good: Testing case variations of SPARQL keywords
- ❌ Issue: Testing theoretical injection patterns

**Data Integrity Tests**:
- ✅ Good: Testing Unicode from real languages
- ❌ Issue: Testing artificial character sequences

**MCP Contract Tests**:
- ✅ Good: Using native dict inputs
- ❌ Issue: Using pre-validated Pydantic models

## Realism Validation Examples

### High Realism Test Example

```python
@pytest.mark.asyncio
async def test_realistic_llm_workflow(client: Client) -> None:
    """Test realistic LLM conversation workflow."""
    
    # LLM adds initial knowledge
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/alice",
            "predicate": "http://schema.org/name", 
            "object": "Alice Smith",
            "graph_name": "conversation-123"
        }]
    })
    
    # LLM queries to recall information
    result = await client.call_tool("rdf_query", {
        "query": "SELECT ?name WHERE { ?person <http://schema.org/name> ?name }"
    })
    
    # LLM adds related information
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/person/alice",
            "predicate": "http://schema.org/age",
            "object": "30",
            "graph_name": "conversation-123"
        }]
    })
    
    # Verify complete workflow worked
    all_alice_data = await client.call_tool("quads_for_pattern", {
        "subject": "http://example.org/person/alice",
        "graph_name": "conversation-123"
    })
    
    content = all_alice_data[0]
    assert isinstance(content, TextContent)
    quads = [QuadResult(**quad) for quad in json.loads(content.text)]
    assert len(quads) >= 2  # Name and age
```

**Realism Score: HIGH** - This tests exactly how LLMs use the system in real conversations.

### Low Realism Test Example

```python
@pytest.mark.asyncio
async def test_artificial_scenario(client: Client) -> None:
    """Test artificial scenario unlikely to occur."""
    
    # Artificial perfect data
    perfect_triple = TripleModel(
        subject="http://perfectly.formed.uri/with/ideal/structure",
        predicate="http://perfectly.formed.predicate/with/ideal/structure", 
        object="Perfectly formed object with no edge cases"
    )
    
    # Using pre-validated model (bypasses MCP validation)
    result = await client.call_tool("add_triples", {"triples": [perfect_triple]})
    
    # Only testing happy path
    assert "success" in result[0].text.lower()
```

**Realism Score: LOW** - Uses artificial perfect inputs and bypasses MCP validation.

## Continuous Realism Monitoring

### During Development
- Apply realism check to every new test
- Question artificial perfection in test inputs
- Verify edge cases could happen in practice

### During Code Review
- Use analysis template for test review
- Flag unrealistic test patterns
- Ensure security tests cover real attack vectors

### During Maintenance
- Re-evaluate test realism as LLM usage patterns evolve
- Update tests based on actual production issues
- Remove tests that no longer reflect realistic usage

## Integration with Development Workflow

### Pre-commit Checklist
- [ ] All tests pass realism analysis
- [ ] No artificial perfect inputs
- [ ] MCP contract validation included
- [ ] Security tests cover realistic scenarios
- [ ] Error messages tested for usefulness

### Code Review Focus
- Does this test reflect real LLM usage?
- Would this scenario actually occur in production?
- Are we testing the right abstraction level?
- Do error cases match realistic failure modes?

**Remember**: The goal is tests that catch actual bugs and reflect real LLM interactions with the MCP RDF Memory server, not artificial scenarios that pass by luck.