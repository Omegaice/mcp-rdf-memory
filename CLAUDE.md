# MCP RDF Memory Server

## Context Management Strategy

**This file is ALWAYS in Claude's context** - every token matters for efficiency.

**Inline Here (High-frequency decisions):**
- Essential commands and patterns used constantly  
- Core error handling and validation patterns
- LLM-centric design principles (unique to this project)
- Critical analysis and framework behavior reminders

**External Documentation (Detailed guidance):**
- Comprehensive testing patterns → `docs/project/testing-guidelines.md`
- Framework-specific details → Use context7 for FastMCP/pyoxigraph/pydantic docs

**Context Efficiency Principle**: Optimize for rapid decision-making, not comprehensive learning.

## Project Overview
Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.

**Core Stack**: FastMCP server framework, Pyoxigraph RDF triple store with SPARQL 1.1, UV package manager

## CRITICAL: File Inclusion Behavior

`@filename` is a **CLAUDE.md-specific feature** that automatically includes file content in context:

**Where it works**: ONLY in CLAUDE.md and CLAUDE.local.md files  
**Where it does NOT work**: Responses, other files, commit messages, anywhere else  
**Behavior**: Recursively includes content (if `@file1` contains `@file2`, both are included)  
**Risk**: Massive context bloat - each inclusion can cascade exponentially

**Usage Rule**: Use `@filename` ONLY when you absolutely need the file content in context. Otherwise, reference by path only (`docs/file.md`).

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

## UV Project Management (Essential)

**Never use pip commands - always use UV equivalents:**
- `uv add package-name` (not `pip install`)
- `uv add package --dev` (not `pip install` for dev deps)
- `uv remove package` (not `pip uninstall`)
- `uv sync` (not `pip install -r requirements.txt`)
- `uv lock --upgrade` (to update dependencies)
- `uv run command` (no manual venv activation needed)

**After pulling changes**: Always run `uv sync`
**Lock file**: `uv.lock` is source of truth, not requirements.txt

## Key Patterns

### Error Handling (Core Pattern)
```python
from fastmcp import ToolError

# Always use ToolError with proper exception chaining
try:
    results = store.query(query)
except ValueError as e:
    raise ToolError(f"Invalid SPARQL query syntax: {e}") from e
except Exception as e:
    raise ToolError(f"Failed to execute SPARQL query: {e}") from e
```

### Named Graphs for Context
- Conversations: `<http://mcp.local/conversation/{id}>`
- Projects: `<http://mcp.local/project/{id}>`

### Constants (Reference Values)
```python
# URI validation
URI_SCHEMES = ("http://", "https://")

# SPARQL Security Model
# - query() method: read operations only (SELECT, ASK, CONSTRUCT, DESCRIBE)
# - update() method: modification operations (INSERT, DELETE, etc.) - not exposed as MCP tool
# - Natural separation provides security without keyword validation
```

### Type Safety Principles
- Use specific union types: `NamedNode | Literal | BlankNode`
- Use `isinstance()` over `hasattr()` for type checking
- Use early returns for clarity, avoid unnecessary fallbacks

### RDF Node Handling
**DefaultGraph Handling**: `DefaultGraph` has no `.value` attribute - handle explicitly.

## MCP Client Real-World Constraints

**CRITICAL: Desktop client limitations fundamentally impact tool design.**

### Client Limitations
- **No tool namespacing** - name collisions between MCP servers are common
- **Tool count limits** - every tool slot is precious resource
- **Performance constraints** - clients may limit concurrent tool usage

### Tool Architecture Impact
- **Naming Rule**: Always use `rdf_` prefix to prevent conflicts
- **Tool count optimization**: Justify each tool's existence vs consolidation
- **Future planning**: Design tool suite as cohesive, prefixed family

## LLM-Centric Knowledge Graph Design

### Core Principles for RDF LLM APIs
- **Leverage LLM's RDF Knowledge**: Use semantic terminology, don't abstract it away
- **Knowledge Graph Mental Model**: Encourage subjects, predicates, objects thinking
- **Context Efficiency is Critical**: Every token in tool schemas counts
- **Self-Documenting Parameter Names**: `graph_name` vs `graph` immediately suggests string input
- **Examples > Descriptions**: `Field(examples=["chat-123"])` teaches usage more efficiently than paragraphs
- **Simplicity > Technical Purity**: `"chat-123"` → `"http://mcp.local/chat-123"` internally vs requiring LLMs to construct URIs

### RDF Naming Strategy
**Principle**: Use RDF terminology that LLMs understand, not generic abstractions
- ✅ `rdf_find_triples` - leverages LLM's RDF knowledge
- ❌ `recall` or `search` - loses semantic context
- ✅ Explicit parameter names: `subject`, `predicate`, `object`
- ❌ Generic names: `query`, `value`, `data`

### Pydantic Type Strategy
**Decision Framework**: Use Annotated types when validation complexity is justified by preventing common input errors or supporting multiple input formats. Otherwise use simple types with helper validation.

### Field() Optimization
Use `examples=["chat-123", "project/myapp"]` instead of verbose descriptions to save context tokens.

### Graph Naming Convention
Simple string names get auto-namespaced: `"conversation/chat-123"` → `"http://mcp.local/conversation/chat-123"`

**Benefits**: No URI syntax errors, natural folder-like organization, reduced cognitive load for LLMs.

## Architecture Decision Record

### Stateless vs Stateful Tool Design (CONFIRMED)
**Decision**: Explicit `graph_name` parameters on every call > stateful `set_current_graph` approach

**Rationale**:
- **LLM Clarity**: No hidden state confusion
- **Multi-graph Workflows**: Common pattern of comparing data across graphs
- **SPARQL Compatibility**: Complex queries naturally specify graphs
- **FastMCP Alignment**: Self-contained, debuggable tool calls
- **Token Efficiency**: Stateful requires more total tool calls

### Tool Suite Design (CONFIRMED)
**Current Tools**:
- `rdf_add_triples` - simple batch operations
- `rdf_find_triples` - pattern matching (formerly `quads_for_pattern`)
- `rdf_sparql_query` - complex read operations (formerly `rdf_query`)

**Future Tools**:
- `rdf_sparql_update` - complex write operations (INSERT, DELETE, etc.)

**Benefits**: Collision-resistant naming, clear operation separation, future-scalable

## Tool Development Guidelines

### FastMCP List Serialization Pattern
**CRITICAL**: When returning lists from tools, use Pydantic RootModel to ensure consistent JSON array serialization

```python
from pydantic import RootModel

# Define a RootModel for list returns
FindTriplesResult = RootModel[list[QuadResult]]

@mcp.tool()
def rdf_find_triples(...) -> FindTriplesResult:
    results = [...]  # Build list of QuadResult objects
    return FindTriplesResult(results)  # Wrap in RootModel
```

**Problem**: FastMCP serializes single-item lists as objects instead of arrays without RootModel
**Solution**: Always use `RootModel[list[T]]` for list return types

### Tool Naming Pattern
**Required**: All tools MUST use `rdf_` prefix to prevent client conflicts

```python
@mcp.tool()
def rdf_add_triples(...):
    """Add RDF triples to the knowledge graph for simple batch operations.
    Use rdf_sparql_query for complex insertions."""

@mcp.tool()
def rdf_find_triples(...):
    """Find RDF triples matching the pattern. Use None for wildcards.
    Use rdf_sparql_query for complex queries."""

@mcp.tool()
def rdf_sparql_query(...):
    """Execute read-only SPARQL queries for complex knowledge graph operations."""
```

### Function Structure Pattern
```python
@mcp.tool()
def tool_name(params: TypedModel) -> str:
    """Clear docstring describing the tool's purpose."""
    try:
        # Main logic with proper error handling
        return "Success message with details"
    except ToolError:
        raise  # Re-raise ToolErrors as-is
    except SpecificError as e:
        raise ToolError(f"Specific error message: {e}") from e
    except Exception as e:
        raise ToolError(f"Unexpected error: {e}") from e
```

### Empty Input Handling
Don't validate against empty lists - handle gracefully and return appropriate success messages.

## Server Entry Point
`src/mcp_rdf_memory/server.py:mcp` - FastMCP server instance

## Testing Principles

**🚨 MANDATORY: Read testing docs before modifying any test files.**

### Critical Rules
- **NEVER modify tests to accommodate bugs** - only when test is incorrect or requirements changed
- **Test realism check**: "Can LLMs actually call this tool with this input in production?"
- **Use native dict inputs** - test with raw `dict` objects, never Pydantic models
- **Validate JSON structure first** - before reconstructing objects
- **Test round-trip data integrity** - ensure data survives complete cycles unchanged
- **Include malformed input testing** - test realistic error scenarios

### Essential Test Pattern
```python
# 1. Native dict input, 2. Validate result structure, 3. Validate JSON, 4. Test reconstruction
result = await client.call_tool("tool_name", {"field": "value"})  # Raw dict
content = result[0]; assert isinstance(content, TextContent)
raw_json = json.loads(content.text); assert isinstance(raw_json, list)
validated_objects = [ModelClass(**item) for item in raw_json]
```

### Pattern Matching Tool Testing
**CRITICAL**: Pattern tools require comprehensive parameter combination testing

**Required Test Coverage**:
- **Single parameters**: `subject` only, `predicate` only, `object` only
- **Parameter pairs**: `subject+object`, `subject+predicate`, `predicate+object`
- **With graph_name**: All above combinations + `graph_name`
- **Wildcard scenarios**: All None, empty dict input
- **Edge cases**: Invalid identifiers, Unicode data, no matches

**Rationale**: LLMs use diverse query patterns for knowledge graph exploration. Missing combinations indicate untested real-world usage patterns.

**Testing Documentation**: `docs/project/testing/` - Start with README.md for navigation and quick reference

## Analysis and Validation Principles

**CRITICAL: Always validate assumptions against actual behavior before making changes.**

### Before Analyzing or Modifying Code
- Run existing tests: `uv run pytest`
- Use context7 for framework docs when making assumptions
- Validate against actual implementation - don't rely on assumptions
- Look for what's working before trying to fix what's broken

### Common Analysis Pitfalls to Avoid
- ❌ Assuming test failures mean tests are wrong (failing tests often catch real bugs)
- ❌ Declaring framework behavior without validation (FastMCP/pyoxigraph have specific behaviors)
- ❌ Over-engineering solutions (existing patterns may be correct)
- ❌ Testing implementation details (focus on contracts and realistic usage)

### Framework Behavior Validation
- Use context7 to get actual documentation before making assumptions
- Test actual behavior rather than assuming how frameworks should work
- Key validation areas: tool return value handling, input validation patterns, error handling

## Debugging
- Use IDE diagnostics to identify and troubleshoot issues
- Run `uv run pytest` to test all functionality (add `-v` for verbose output)
- Use `uv run ruff check` for linting issues
- Check type annotations with IDE (Pylance) for type safety