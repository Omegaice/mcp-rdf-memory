"""
Shared test fixtures and utilities for MCP RDF Memory server tests.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastmcp import Client

from mcp_rdf_memory.server import mcp


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[Client, None]:
    """Provide a FastMCP client for testing."""
    async with Client(mcp) as client:
        yield client


@pytest.fixture
def sample_triple() -> dict[str, str]:
    """Provide a sample RDF triple for testing."""
    return {"subject": "http://example.org/person/test", "predicate": "http://schema.org/name", "object": "Test Person"}


@pytest.fixture
def sample_graph_uri() -> str:
    """Provide a sample named graph URI for testing."""
    return "http://mcp.local/conversation/test-123"
