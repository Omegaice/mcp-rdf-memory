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

## Debugging
- Use IDE diagnostics to identify and troubleshoot issues
- Run `uv run pytest -v` to test all functionality
- Use `uv run ruff check` for linting issues
- Check type annotations with IDE (Pylance) for type safety