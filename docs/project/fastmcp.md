# FastMCP Framework Comprehensive Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Installation & Setup](#installation--setup)
4. [Components](#components)
5. [Development Patterns](#development-patterns)
6. [Advanced Features](#advanced-features)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Security](#security)
10. [Best Practices](#best-practices)
11. [Examples](#examples)
12. [Resources](#resources)

## Overview

FastMCP is a high-level Python framework for building Model Context Protocol (MCP) servers and clients. It provides the simplest path to production for MCP implementations while maintaining full protocol compliance.

### Philosophy
- **Fast**: Minimal overhead and optimized performance
- **Simple**: Pythonic interfaces with minimal boilerplate
- **Pythonic**: Leverages Python's strengths (decorators, type hints, async)
- **Complete**: Full MCP ecosystem support

### Key Benefits
- High-level abstraction over MCP protocol
- Automatic schema generation from type annotations
- Built-in testing framework
- Multiple transport protocols
- Server composition and modularity
- OpenAPI integration
- Authentication support

## Core Concepts

### Model Context Protocol (MCP)
MCP is a standardized protocol for providing context and tools to Large Language Models (LLMs). It enables:
- Structured data exchange between LLMs and external systems
- Tool execution capabilities
- Resource access for read-only data
- Prompt templates for guided interactions

### FastMCP Components
1. **Server**: Main container for application components
2. **Tools**: Executable functions LLMs can invoke
3. **Resources**: Read-only data sources
4. **Resource Templates**: Parameterized data generators
5. **Prompts**: Reusable message templates

## Installation & Setup

### Basic Installation
```bash
pip install fastmcp
# or
uv add fastmcp
```

### Dependencies for RDF/SPARQL Projects
```bash
uv add fastmcp oxigraph pydantic
```

### Basic Server Setup
```python
from fastmcp import FastMCP

# Create server instance
mcp = FastMCP("My MCP Server")

# Basic tool
@mcp.tool()
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

# Run server
if __name__ == "__main__":
    mcp.run()
```

## Components

### Tools

Tools transform Python functions into capabilities that LLMs can invoke during conversations.

#### Basic Tool Definition
```python
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b
```

#### Advanced Tool Features
```python
from typing import Literal, Optional
from pydantic import Field

@mcp.tool()
def process_data(
    data: str,
    format: Literal["json", "xml", "csv"] = "json",
    options: Optional[dict] = None,
    validate: bool = Field(True, description="Whether to validate the data")
) -> dict:
    """Process data in various formats with validation."""
    # Implementation here
    return {"status": "processed", "format": format}
```

#### Async Tools
```python
@mcp.tool()
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

#### Error Handling
```python
from fastmcp import ToolError

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    if b == 0:
        raise ToolError("Cannot divide by zero")
    return a / b
```

### Resources

Resources provide read-only access to data for LLM or client applications.

#### Static Resources
```python
@mcp.resource("file://config.json")
def get_config() -> dict:
    """Get application configuration."""
    return {"version": "1.0", "debug": False}
```

#### Dynamic Resources
```python
@mcp.resource("file://logs/{date}.txt")
def get_logs(date: str) -> str:
    """Get logs for a specific date."""
    # Read log file for the given date
    with open(f"/var/log/app-{date}.log") as f:
        return f.read()
```

#### File Resources
```python
from fastmcp.resources import FileResource

# Expose local files
mcp.add_resource(FileResource("file://data.csv", "/path/to/data.csv"))
```

#### HTTP Resources
```python
from fastmcp.resources import HttpResource

# Expose remote data
mcp.add_resource(HttpResource("http://api.example.com/data", "https://api.example.com/data"))
```

### Resource Templates

Enable dynamic resource generation with URI parameters.

```python
@mcp.resource("data://user/{user_id}/profile")
def get_user_profile(user_id: str) -> dict:
    """Get user profile by ID."""
    # Fetch user data
    return {"user_id": user_id, "name": "John Doe"}

@mcp.resource("data://search/{query}")
def search_results(query: str, limit: int = 10) -> list:
    """Search with optional limit parameter."""
    # Perform search
    return [{"result": f"Result for {query}"}]
```

### Prompts

Provide parameterized message templates for LLMs.

```python
@mcp.prompt()
def code_review_prompt(code: str, language: str = "python") -> str:
    """Generate a code review prompt."""
    return f"""
    Please review this {language} code:
    
    ```{language}
    {code}
    ```
    
    Focus on:
    - Code quality and style
    - Potential bugs
    - Performance improvements
    - Best practices
    """

@mcp.prompt()
async def dynamic_prompt(topic: str) -> list:
    """Generate dynamic prompt with multiple messages."""
    # Fetch relevant context
    context = await fetch_context(topic)
    
    return [
        {"role": "system", "content": f"You are an expert on {topic}"},
        {"role": "user", "content": f"Context: {context}"}
    ]
```

## Development Patterns

### Server Structure
```python
from fastmcp import FastMCP
from typing import List, Optional
import asyncio

class MyMCPServer:
    def __init__(self):
        self.mcp = FastMCP("My Application Server")
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
    
    def _setup_tools(self):
        @self.mcp.tool()
        def tool1(param: str) -> str:
            return f"Processed: {param}"
    
    def _setup_resources(self):
        @self.mcp.resource("data://info")
        def get_info() -> dict:
            return {"status": "active"}
    
    def _setup_prompts(self):
        @self.mcp.prompt()
        def help_prompt() -> str:
            return "How can I help you today?"
    
    def run(self):
        self.mcp.run()

if __name__ == "__main__":
    server = MyMCPServer()
    server.run()
```

### Modular Architecture
```python
# tools.py
from fastmcp import FastMCP

def setup_calculation_tools(mcp: FastMCP):
    @mcp.tool()
    def add(a: float, b: float) -> float:
        return a + b
    
    @mcp.tool()
    def multiply(a: float, b: float) -> float:
        return a * b

# resources.py
def setup_data_resources(mcp: FastMCP):
    @mcp.resource("data://stats")
    def get_stats() -> dict:
        return {"calculations": 100}

# main.py
from fastmcp import FastMCP
from tools import setup_calculation_tools
from resources import setup_data_resources

mcp = FastMCP("Calculator Server")
setup_calculation_tools(mcp)
setup_data_resources(mcp)
```

### Type Safety
```python
from typing import Union, List, Dict, Any
from pydantic import BaseModel, Field

class UserData(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')

@mcp.tool()
def create_user(user: UserData) -> dict:
    """Create a new user with validated data."""
    return {"id": 123, "created": True, "user": user.dict()}

@mcp.tool()
def process_items(items: List[str], metadata: Dict[str, Any]) -> dict:
    """Process a list of items with metadata."""
    return {"processed": len(items), "metadata": metadata}
```

## Advanced Features

### Server Composition

#### Importing (Static Composition)
```python
# Create separate servers
auth_server = FastMCP("Auth Server")
data_server = FastMCP("Data Server")

# Main server imports components
main_server = FastMCP("Main Server")
main_server.import_server("auth", auth_server)
main_server.import_server("data", data_server)
```

#### Mounting (Dynamic Composition)
```python
# Dynamic mounting for live updates
main_server.mount("dynamic", data_server)
# Changes to data_server are immediately reflected
```

### Authentication

#### Bearer Token Authentication
```python
from fastmcp.auth import BearerAuthProvider

# JWT-based authentication
auth_provider = BearerAuthProvider(
    public_key="-----BEGIN PUBLIC KEY-----\n...",
    issuer="your-auth-server",
    audience="your-app"
)

mcp = FastMCP("Secure Server", auth_provider=auth_provider)

@mcp.tool(required_scopes=["read", "write"])
def secure_operation() -> str:
    """This tool requires specific scopes."""
    return "Authorized operation completed"
```

### OpenAPI Integration

#### From OpenAPI Spec
```python
from fastmcp.integrations import create_server_from_openapi

# Generate MCP server from OpenAPI spec
mcp = create_server_from_openapi("https://api.example.com/openapi.json")
```

#### From FastAPI App
```python
from fastapi import FastAPI
from fastmcp.integrations import create_server_from_fastapi

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}

# Convert FastAPI to MCP
mcp = create_server_from_fastapi(app)
```

### HTTP Request Handling
```python
from fastmcp.dependencies import get_http_request, get_http_headers

@mcp.tool()
def authenticated_tool(data: str) -> str:
    """Tool that uses HTTP request context."""
    headers = get_http_headers()
    auth = headers.get("authorization", "")
    
    if not auth.startswith("Bearer "):
        raise ToolError("Authentication required")
    
    return f"Processed: {data}"
```

### Custom Routes
```python
from fastapi import Request

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Custom health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

## Testing

### In-Memory Testing
```python
import pytest
from fastmcp import FastMCP
from fastmcp.testing import Client

@pytest.fixture
def mcp_server():
    mcp = FastMCP("Test Server")
    
    @mcp.tool()
    def test_tool(value: str) -> str:
        return f"Processed: {value}"
    
    return mcp

@pytest.mark.asyncio
async def test_tool_functionality(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool("test_tool", {"value": "test"})
        assert result[0].text == "Processed: test"
```

### Mock Dependencies
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_async_tool():
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": "test"}
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Test async tool
        result = await fetch_data("http://example.com")
        assert result == {"data": "test"}
```

### Integration Testing
```python
@pytest.mark.asyncio
async def test_full_workflow(mcp_server):
    async with Client(mcp_server) as client:
        # Test multiple operations
        tools = await client.list_tools()
        assert len(tools) > 0
        
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        # Test actual tool call
        result = await client.call_tool("greet", {"name": "World"})
        assert "Hello, World" in result[0].text
```

## Deployment

### Running Servers

#### Development Mode
```python
# Direct execution
if __name__ == "__main__":
    mcp.run()

# With FastMCP CLI
# fastmcp run server.py:mcp
```

#### Production Mode
```python
# Streamable HTTP (recommended)
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

# ASGI integration
from fastmcp.server import create_asgi_app

app = create_asgi_app(mcp)
# Deploy with uvicorn, gunicorn, etc.
```

### Transport Options

#### STDIO (Default)
```python
# Best for Claude Desktop integration
mcp.run(transport="stdio")
```

#### Streamable HTTP
```python
# Modern web-based deployment
mcp.run(
    transport="streamable-http",
    host="127.0.0.1",
    port=8000,
    path="/mcp"
)
```

### Claude Desktop Integration
```bash
# Install server for Claude Desktop
fastmcp install server.py:mcp --name "My Server"

# With dependencies
fastmcp install server.py:mcp --with httpx --with pydantic
```

### Environment Configuration
```python
import os

mcp = FastMCP(
    name=os.getenv("MCP_SERVER_NAME", "Default Server"),
    version=os.getenv("VERSION", "1.0.0")
)

# Environment-specific behavior
if os.getenv("ENVIRONMENT") == "production":
    mcp.run(transport="streamable-http", host="0.0.0.0")
else:
    mcp.run(transport="stdio")
```

## Security

### Input Validation
```python
from pydantic import Field, validator

@mcp.tool()
def secure_query(
    query: str = Field(max_length=1000, description="SPARQL query"),
    limit: int = Field(default=100, ge=1, le=1000)
) -> dict:
    """Execute a validated SPARQL query."""
    # Validate query syntax
    if "DELETE" in query.upper() or "INSERT" in query.upper():
        raise ToolError("Modification queries not allowed")
    
    # Execute query with limit
    return execute_sparql(query, limit)
```

### Authentication Context
```python
from fastmcp.dependencies import get_auth_context

@mcp.tool()
def protected_operation() -> str:
    """Access authenticated user context."""
    auth = get_auth_context()
    user_id = auth.claims.get("client_id")
    scopes = auth.scopes
    
    if "admin" not in scopes:
        raise ToolError("Admin access required")
    
    return f"Operation performed by user: {user_id}"
```

### SPARQL Injection Prevention
```python
from urllib.parse import quote

@mcp.tool()
def safe_sparql_query(subject_uri: str, predicate: str) -> dict:
    """Execute a safe SPARQL query with parameterization."""
    # Validate and escape URIs
    if not subject_uri.startswith(("http://", "https://")):
        raise ToolError("Invalid URI format")
    
    # Use parameterized query
    query = f"""
    SELECT ?object WHERE {{
        <{quote(subject_uri)}> <{quote(predicate)}> ?object .
    }}
    """
    
    return execute_sparql(query)
```

## Best Practices

### Error Handling
```python
import logging
from fastmcp import ToolError

logger = logging.getLogger(__name__)

@mcp.tool()
def robust_operation(data: str) -> dict:
    """Operation with comprehensive error handling."""
    try:
        # Validate input
        if not data.strip():
            raise ToolError("Input data cannot be empty")
        
        # Process data
        result = process_data(data)
        
        # Log success
        logger.info(f"Successfully processed data: {len(data)} characters")
        
        return {"status": "success", "result": result}
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise ToolError(f"Invalid input: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ToolError("Internal processing error")
```

### Performance Optimization
```python
from functools import lru_cache
import asyncio

# Cache expensive operations
@lru_cache(maxsize=128)
def expensive_computation(data: str) -> dict:
    """Cached expensive operation."""
    # Heavy computation here
    return {"result": "computed"}

@mcp.tool()
async def optimized_tool(query: str) -> dict:
    """Tool with performance optimizations."""
    # Use cached computation
    base_result = expensive_computation(query)
    
    # Batch async operations
    async def fetch_additional_data():
        # Async operation
        return {"additional": "data"}
    
    additional = await fetch_additional_data()
    
    return {**base_result, **additional}
```

### Logging and Monitoring
```python
import logging
from fastmcp.dependencies import get_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@mcp.tool()
def monitored_operation(data: str) -> dict:
    """Operation with monitoring and logging."""
    context = get_context()
    
    # Log operation start
    logger.info(f"Starting operation for {len(data)} bytes of data")
    
    try:
        # Report progress
        context.report_progress(0.5, "Processing data...")
        
        result = process_data(data)
        
        # Log success metrics
        logger.info(f"Operation completed successfully: {len(result)} items")
        
        return result
        
    except Exception as e:
        # Log error with context
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
```

### Resource Management
```python
import asyncio
from contextlib import asynccontextmanager

class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        # Initialize connection pool
        self.pool = await create_connection_pool()
    
    async def cleanup(self):
        if self.pool:
            await self.pool.close()

# Global resource manager
db_manager = DatabaseManager()

@mcp.tool()
async def database_query(query: str) -> dict:
    """Query database with proper resource management."""
    if not db_manager.pool:
        await db_manager.initialize()
    
    async with db_manager.pool.acquire() as conn:
        result = await conn.execute(query)
        return {"rows": result.fetchall()}

# Cleanup on server shutdown
async def cleanup():
    await db_manager.cleanup()

# Register cleanup handler
mcp.add_shutdown_handler(cleanup)
```

## Examples

### RDF Triple Store Server
```python
from fastmcp import FastMCP
from oxigraph import Store
from typing import List, Optional

class RDFServer:
    def __init__(self):
        self.mcp = FastMCP("RDF Memory Server")
        self.store = Store()
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        @self.mcp.tool()
        def add_triple(subject: str, predicate: str, object_value: str, graph: Optional[str] = None) -> dict:
            """Add an RDF triple to the store."""
            try:
                triple = f"<{subject}> <{predicate}> \"{object_value}\" ."
                if graph:
                    self.store.load(f"GRAPH <{graph}> {{ {triple} }}", "application/sparql-update")
                else:
                    self.store.load(triple, "text/turtle")
                
                return {"status": "success", "triple_added": True}
            except Exception as e:
                raise ToolError(f"Failed to add triple: {e}")
        
        @self.mcp.tool()
        def sparql_query(query: str, format: str = "json") -> dict:
            """Execute a SPARQL query."""
            try:
                # Validate query is safe (read-only)
                if any(keyword in query.upper() for keyword in ["INSERT", "DELETE", "DROP", "CLEAR"]):
                    raise ToolError("Only SELECT and CONSTRUCT queries allowed")
                
                results = self.store.query(query)
                
                if format == "json":
                    return {"results": [str(result) for result in results]}
                else:
                    return {"results": str(results)}
                    
            except Exception as e:
                raise ToolError(f"Query failed: {e}")
        
        @self.mcp.tool()
        def clear_graph(graph: Optional[str] = None) -> dict:
            """Clear all triples from a graph."""
            try:
                if graph:
                    self.store.update(f"CLEAR GRAPH <{graph}>")
                else:
                    self.store.update("CLEAR DEFAULT")
                
                return {"status": "success", "graph_cleared": True}
            except Exception as e:
                raise ToolError(f"Failed to clear graph: {e}")
    
    def _setup_resources(self):
        @self.mcp.resource("rdf://graphs")
        def list_graphs() -> dict:
            """List all named graphs in the store."""
            query = "SELECT DISTINCT ?graph WHERE { GRAPH ?graph { ?s ?p ?o } }"
            results = self.store.query(query)
            graphs = [str(result[0]) for result in results]
            return {"graphs": graphs, "count": len(graphs)}
        
        @self.mcp.resource("rdf://stats")
        def get_statistics() -> dict:
            """Get store statistics."""
            count_query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
            results = list(self.store.query(count_query))
            triple_count = int(results[0][0]) if results else 0
            
            return {
                "total_triples": triple_count,
                "store_type": "oxigraph",
                "supported_formats": ["turtle", "rdf+xml", "n-triples"]
            }
    
    def run(self):
        self.mcp.run()

if __name__ == "__main__":
    server = RDFServer()
    server.run()
```

### Multi-Service Composition Example
```python
# auth_server.py
from fastmcp import FastMCP

auth_mcp = FastMCP("Auth Service")

@auth_mcp.tool()
def authenticate_user(username: str, password: str) -> dict:
    """Authenticate a user."""
    # Authentication logic
    return {"authenticated": True, "user_id": "123"}

# data_server.py  
data_mcp = FastMCP("Data Service")

@data_mcp.tool()
def get_user_data(user_id: str) -> dict:
    """Get user data."""
    return {"user_id": user_id, "name": "John Doe"}

# main_server.py
from fastmcp import FastMCP
from auth_server import auth_mcp
from data_server import data_mcp

# Compose services
main_mcp = FastMCP("Main Application")
main_mcp.import_server("auth", auth_mcp)
main_mcp.mount("data", data_mcp)

@main_mcp.tool()
def secure_user_operation(username: str, password: str) -> dict:
    """Perform authenticated user operation."""
    # This would typically use the composed services
    return {"status": "operation completed"}

if __name__ == "__main__":
    main_mcp.run()
```

## Resources

### Official Documentation
- [FastMCP Documentation](https://gofastmcp.com/)
- [GitHub Repository](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [LLM-Focused Documentation](https://gofastmcp.com/llms-full.txt) - Complete documentation optimized for LLM consumption

### Key Documentation Pages
- [Getting Started](https://gofastmcp.com/getting-started/welcome)
- [Server Components](https://gofastmcp.com/servers/fastmcp)
- [Tools Documentation](https://gofastmcp.com/servers/tools)
- [Resources & Templates](https://gofastmcp.com/servers/resources)
- [Testing Guide](https://gofastmcp.com/patterns/testing)
- [Deployment Guide](https://gofastmcp.com/deployment/running-server)

### Integration Guides
- [Claude Desktop Integration](https://gofastmcp.com/integrations/claude-desktop)
- [OpenAI Integration](https://gofastmcp.com/integrations/openai)
- [Anthropic Integration](https://gofastmcp.com/integrations/anthropic)

### Community
- [FastMCP GitHub Issues](https://github.com/jlowin/fastmcp/issues)
- [Discussions](https://github.com/jlowin/fastmcp/discussions)

This comprehensive guide provides everything needed to build robust MCP servers with FastMCP, from basic concepts to advanced patterns and production deployment strategies.