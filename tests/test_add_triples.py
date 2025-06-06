"""
Tests for the add_triples tool.
"""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError


@pytest.mark.asyncio
async def test_add_triples_tool_available(client: Client) -> None:
    """Test that add_triples tool is available."""
    tools = await client.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "add_triples" in tool_names


@pytest.mark.asyncio
async def test_add_simple_triple(client: Client) -> None:
    """Test adding a basic RDF triple."""
    result = await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/john",
                    "predicate": "http://schema.org/name",
                    "object": "John Doe",
                }
            ]
        },
    )

    # Success is indicated by no exception and empty result
    assert len(result) == 0


@pytest.mark.asyncio
async def test_add_triple_with_named_graph(client: Client, sample_graph_uri: str) -> None:
    """Test adding a triple to a specific named graph context."""
    result = await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/alice",
                    "predicate": "http://schema.org/name",
                    "object": "Alice Smith",
                    "graph_name": "conversation/test-123",
                }
            ]
        },
    )

    # Success is indicated by no exception and empty result
    assert len(result) == 0


@pytest.mark.asyncio
async def test_add_triple_with_uri_object(client: Client) -> None:
    """Test adding a triple where the object is also a URI."""
    result = await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/john",
                    "predicate": "http://xmlns.com/foaf/0.1/knows",
                    "object": "http://example.org/person/alice",
                }
            ]
        },
    )

    # Success is indicated by no exception and empty result
    assert len(result) == 0


@pytest.mark.asyncio
async def test_add_multiple_triples(client: Client) -> None:
    """Test adding multiple triples in a single call."""
    result = await client.call_tool(
        "add_triples",
        {
            "triples": [
                {
                    "subject": "http://example.org/person/multi1",
                    "predicate": "http://schema.org/name",
                    "object": "Person One",
                },
                {
                    "subject": "http://example.org/person/multi2",
                    "predicate": "http://schema.org/name",
                    "object": "Person Two",
                },
                {
                    "subject": "http://example.org/person/multi1",
                    "predicate": "http://xmlns.com/foaf/0.1/knows",
                    "object": "http://example.org/person/multi2",
                },
            ]
        },
    )

    # Success is indicated by no exception and empty result
    assert len(result) == 0


@pytest.mark.asyncio
async def test_add_triple_validation_error(client: Client) -> None:
    """Test that invalid URIs are properly validated."""
    with pytest.raises(ToolError):  # Should raise ToolError via FastMCP
        await client.call_tool(
            "add_triples",
            {"triples": [{"subject": "not-a-valid-uri", "predicate": "http://schema.org/name", "object": "John Doe"}]},
        )


@pytest.mark.asyncio
async def test_add_triples_invalid_identifiers(client: Client) -> None:
    """Test that truly invalid RDF identifiers raise appropriate errors."""
    invalid_identifiers = [
        "",  # Empty string
        "   ",  # Whitespace only
        # Note: Other cases like "not-a-uri" might be valid CURIEs or literals
    ]

    for identifier in invalid_identifiers:
        with pytest.raises(ToolError):
            await client.call_tool(
                "add_triples",
                {
                    "triples": [
                        {
                            "subject": identifier,
                            "predicate": "http://schema.org/name",
                            "object": "Test",
                        }
                    ]
                },
            )


@pytest.mark.asyncio
async def test_add_triples_valid_curie_and_urn(client: Client) -> None:
    """Test that CURIEs and URNs are accepted as valid identifiers."""
    valid_identifiers = [
        "rdf:type",
        "foaf:knows",
        "schema:name",
        "urn:uuid:12345-67890",
        "urn:isbn:1234567890",
        "mailto:test@example.org",
        "file:///local/path",
    ]

    for identifier in valid_identifiers:
        # Should not raise error
        result = await client.call_tool(
            "add_triples",
            {
                "triples": [
                    {
                        "subject": "http://example.org/test",
                        "predicate": identifier,
                        "object": "Test Value",
                    }
                ]
            },
        )
        assert len(result) == 0


@pytest.mark.asyncio
async def test_add_triples_empty_list(client: Client) -> None:
    """Test that empty triple list is handled gracefully."""
    result = await client.call_tool("add_triples", {"triples": []})
    assert len(result) == 0


@pytest.mark.asyncio
async def test_add_triples_missing_fields(client: Client) -> None:
    """Test that missing required fields raise validation errors."""
    # Missing subject
    with pytest.raises((ToolError, ValueError)):
        await client.call_tool(
            "add_triples",
            {
                "triples": [
                    {
                        "predicate": "http://schema.org/name",
                        "object": "Test",
                    }
                ]
            },
        )

    # Missing predicate
    with pytest.raises((ToolError, ValueError)):
        await client.call_tool(
            "add_triples",
            {
                "triples": [
                    {
                        "subject": "http://example.org/test",
                        "object": "Test",
                    }
                ]
            },
        )


@pytest.mark.asyncio
async def test_add_triples_invalid_graph_uri(client: Client) -> None:
    """Test that invalid graph URIs raise errors."""
    with pytest.raises(ToolError):
        await client.call_tool(
            "add_triples",
            {
                "triples": [
                    {
                        "subject": "http://example.org/test",
                        "predicate": "http://schema.org/name",
                        "object": "Test",
                        "graph_name": "",  # Empty graph URI
                    }
                ]
            },
        )


@pytest.mark.asyncio
async def test_add_triples_invalid_predicate(client: Client) -> None:
    """Test that invalid predicates raise errors."""
    with pytest.raises(ToolError):
        await client.call_tool(
            "add_triples",
            {
                "triples": [
                    {
                        "subject": "http://example.org/test",
                        "predicate": "",  # Empty predicate
                        "object": "Test Value",
                    }
                ]
            },
        )
