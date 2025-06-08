# Testing Documentation Hub

## Quick Reference

- **CRITICAL RULE**: Never modify tests to accommodate bugs - only when test logic is incorrect or requirements changed
- **Input Pattern**: Always use native `dict` inputs in tests, never Pydantic models
- **Validation Pipeline**: Test complete JSON serialization: Input → Validation → Processing → JSON Output
- **Realism Check**: "Can LLMs actually call this tool with this input in production?"

## Essential Test Naming Patterns

- `test_add_triples_should_preserve_data_when_valid_input()` - Positive scenarios
- `test_sparql_query_should_reject_modification_when_insert_attempted()` - Security validation
- `test_add_triples_should_fail_validation_when_invalid_uri()` - Input validation
- `test_round_trip_should_preserve_unicode_when_special_characters()` - Data integrity

## Navigation by Testing Concern

### 🏗️ Foundation
- **[Testing Strategy](./testing-strategy.md)** - Test hierarchy and when to write unit vs integration tests
  - Test your logic, not the language/libraries
  - Testing pyramid: End-to-end → Integration → Unit
  - When unit tests are meaningful vs meaningless
- **[Core Principles](./core-principles.md)** - Testing philosophy and fundamental rules
  - The golden rule: Never accommodate bugs
  - Test abstraction levels and realism checks
  - When bug fixes should break tests

### 🔌 MCP Framework
- **[MCP Contract Testing](./mcp-contract-testing.md)** - MCP tool contract validation
  - Native dict input requirements
  - JSON pipeline validation
  - Tool response patterns and error handling

### 📊 RDF & Semantic Data
- **[RDF Data Integrity](./rdf-data-integrity.md)** - RDF semantic preservation
  - Round-trip data preservation
  - Graph context handling
  - Cross-query consistency testing

### 🔐 Security
- **[SPARQL Security](./sparql-security.md)** - SPARQL injection prevention
  - Forbidden operation blocking
  - Case sensitivity and injection patterns
  - Legitimate query validation

### ✅ Input Validation
- **[Input Validation](./input-validation.md)** - Realistic malformed input testing
  - LLM-realistic malformed inputs
  - URI validation patterns
  - Error message quality testing

### 🎯 Edge Cases
- **[Edge Cases](./edge-cases.md)** - Unicode, special characters, and boundaries
  - Unicode and special character handling
  - Long string and performance testing
  - JSON serialization edge cases

### 📋 Quality Framework
- **[Realism Analysis](./realism-analysis.md)** - Test quality validation
  - Systematic realism validation
  - Analysis templates and quality gates
  - LLM usage possibility framework

## Quick Navigation by Scenario

### "Should I write a unit test for this function?"
→ [Testing Strategy](./testing-strategy.md) - Decision framework for test level selection

### "I need to test a new MCP tool"
→ Start with [Testing Strategy](./testing-strategy.md), then [MCP Contract Testing](./mcp-contract-testing.md)

### "I need to test SPARQL functionality"
→ [SPARQL Security](./sparql-security.md) + [RDF Data Integrity](./rdf-data-integrity.md)

### "I need to test error handling"
→ [Input Validation](./input-validation.md) + [Core Principles](./core-principles.md)

### "I need to test with special data"
→ [Edge Cases](./edge-cases.md) + [RDF Data Integrity](./rdf-data-integrity.md)

### "My test failed - should I modify it?"
→ [Core Principles](./core-principles.md) - The Golden Rule section

### "How do I know if my test is realistic?"
→ [Realism Analysis](./realism-analysis.md)

## Essential Commands

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_integration.py

# Run tests with specific pattern
uv run pytest -k "test_add_triples"

# Lint and fix code
uv run ruff check --fix

# Format code
uv run ruff format
```

## Testing Workflow Checklist

### Before Writing Tests
- [ ] Read [Core Principles](./core-principles.md) if new to the project
- [ ] Identify testing concern: MCP contract, RDF integrity, security, validation, edge cases
- [ ] Review relevant specialized guide
- [ ] Check [Realism Analysis](./realism-analysis.md) for validation criteria

### Writing Tests
- [ ] Use native `dict` inputs (not Pydantic models)
- [ ] Test complete JSON pipeline: input → validation → processing → output
- [ ] Include realistic malformed input scenarios
- [ ] Validate error messages are helpful
- [ ] Test data integrity with round-trip verification

### After Writing Tests
- [ ] Run tests: `uv run pytest`
- [ ] Apply realism analysis from [Realism Analysis](./realism-analysis.md)
- [ ] Verify tests catch actual bugs, not just pass
- [ ] Lint code: `uv run ruff check --fix`

### When Tests Fail
- [ ] **DO NOT modify tests to make them pass**
- [ ] Analyze: Is the test logic correct?
- [ ] Identify: Is this a bug in the code or an issue with the test?
- [ ] If test is correct: Fix the application code
- [ ] If test is wrong: Document why and get confirmation before changing

## Integration with CLAUDE.md

For context-efficient reference in CLAUDE.md, include specific files:

```markdown
# Quick testing reference
@docs/project/testing/core-principles.md

# For specific testing concerns
Reference docs/project/testing/[specific-file].md
```

## Common Anti-Patterns Summary

**Input Patterns**:
- ❌ Using `TripleModel(...)` in tests
- ✅ Using `{"subject": "...", "predicate": "...", "object": "..."}`

**Validation Patterns**:
- ❌ Skipping JSON structure validation
- ✅ Testing complete JSON pipeline

**Error Handling**:
- ❌ Modifying tests when they fail due to bugs
- ✅ Fixing application code when tests correctly catch bugs

**Realism Patterns**:
- ❌ Testing with artificial perfect inputs
- ✅ Testing with realistic LLM-generated inputs

## Contributing to Testing Documentation

When adding new testing patterns:

1. **Identify the concern area**: Which file should contain the new pattern?
2. **Follow existing structure**: Use similar examples and explanations
3. **Include anti-patterns**: Show what NOT to do alongside correct patterns
4. **Test your examples**: Ensure code examples actually work
5. **Update this README**: Add navigation links for new major patterns

## Framework-Specific Testing Notes

- **FastMCP**: Returns `[]` for empty results, `TextContent` for non-empty
- **Pyoxigraph**: Internal RDF serialization may add quotes or escaping
- **Pydantic**: Input validation happens before tool execution
- **SPARQL**: Case-sensitive keyword detection for security
- **JSON**: All tool outputs must be valid JSON for MCP compatibility

This documentation structure ensures focused guidance while maintaining comprehensive coverage of all testing scenarios in the MCP RDF Memory project.