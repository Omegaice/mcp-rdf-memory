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

# Validate queries (read-only)
if "DELETE" in query.upper() or "INSERT" in query.upper():
    raise ToolError("Only SELECT/CONSTRUCT queries allowed")
```

## Server Entry Point
`src/mcp_rdf_memory/server.py:mcp` - FastMCP server instance