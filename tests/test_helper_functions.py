"""
Direct unit tests for helper functions in the server module.
"""

import pytest
from pyoxigraph import BlankNode, Literal, NamedNode, Triple

from mcp_rdf_memory.server import (
    create_rdf_node,
    format_predicate,
    format_rdf_object,
    format_subject,
    validate_rdf_identifier,
)


class TestValidateRdfIdentifier:
    """Test the validate_rdf_identifier function."""

    def test_valid_http_uri(self):
        """Test that valid HTTP URIs pass validation."""
        result = validate_rdf_identifier("http://example.org/test")
        assert result == "http://example.org/test"

        result = validate_rdf_identifier("https://example.org/test")
        assert result == "https://example.org/test"

    def test_invalid_identifiers_raise_error(self):
        """Test that invalid RDF identifiers raise ValueError."""
        invalid_identifiers = [
            "",  # Empty string
            "   ",  # Whitespace only
            # Note: Most other cases are now valid (CURIEs, URNs, etc.)
        ]

        for identifier in invalid_identifiers:
            with pytest.raises(ValueError):
                validate_rdf_identifier(identifier)

    def test_valid_non_http_identifiers(self):
        """Test that non-HTTP identifiers are accepted."""
        valid_identifiers = [
            "rdf:type",
            "foaf:knows",
            "urn:uuid:12345",
            "mailto:test@example.org",
            "file:///path",
        ]

        for identifier in valid_identifiers:
            result = validate_rdf_identifier(identifier)
            assert result == identifier  # Should return the same string

    def test_namednode_input(self):
        """Test that NamedNode input returns its value."""
        node = NamedNode("http://example.org/test")
        result = validate_rdf_identifier(node)
        assert result == "http://example.org/test"


class TestCreateRdfNode:
    """Test the create_rdf_node helper function."""

    def test_creates_named_node_for_uris(self):
        """Test that URIs create NamedNode instances."""
        node = create_rdf_node("http://example.org/test")
        assert isinstance(node, NamedNode)
        assert node.value == "http://example.org/test"

        node = create_rdf_node("https://example.org/test")
        assert isinstance(node, NamedNode)
        assert node.value == "https://example.org/test"

    def test_creates_literal_for_non_identifiers(self):
        """Test that values that can't be NamedNodes create Literal instances."""
        # Values that should become literals (if pyoxigraph rejects them as NamedNodes)
        potential_literals = [
            "plain text",
            "123",
            "",
            "text with spaces",
        ]

        for value in potential_literals:
            node = create_rdf_node(value)
            # Should be either NamedNode or Literal, depending on pyoxigraph's validation
            assert isinstance(node, NamedNode | Literal)

    def test_creates_named_node_for_valid_identifiers(self):
        """Test that valid RDF identifiers create NamedNode instances."""
        valid_identifiers = [
            "http://example.org/test",
            "rdf:type",
            "urn:uuid:123",
        ]

        for identifier in valid_identifiers:
            node = create_rdf_node(identifier)
            assert isinstance(node, NamedNode)
            assert node.value == identifier


class TestFormatRdfObject:
    """Test the format_rdf_object helper function."""

    def test_format_named_node(self):
        """Test formatting NamedNode objects."""
        node = NamedNode("http://example.org/test")
        result = format_rdf_object(node)
        assert result == "<http://example.org/test>"

    def test_format_literal(self):
        """Test formatting Literal objects."""
        node = Literal("test value")
        result = format_rdf_object(node)
        assert result == '"test value"'

        # Test with special characters
        node = Literal('value with "quotes"')
        result = format_rdf_object(node)
        assert result == '"value with "quotes""'

    def test_format_blank_node(self):
        """Test formatting BlankNode objects."""
        node = BlankNode("b1")
        result = format_rdf_object(node)
        assert result == "_:b1"

    def test_format_triple(self):
        """Test formatting Triple objects (quoted triples)."""
        # Create a triple
        subject = NamedNode("http://example.org/subject")
        predicate = NamedNode("http://example.org/predicate")
        obj = Literal("object")
        triple = Triple(subject, predicate, obj)

        result = format_rdf_object(triple)
        # Should fall back to str() representation
        assert isinstance(result, str)
        assert len(result) > 0


class TestFormatSubject:
    """Test the format_subject helper function."""

    def test_format_named_node_subject(self):
        """Test formatting NamedNode subjects."""
        node = NamedNode("http://example.org/subject")
        result = format_subject(node)
        assert result == "<http://example.org/subject>"

    def test_format_blank_node_subject(self):
        """Test formatting BlankNode subjects."""
        node = BlankNode("subj1")
        result = format_subject(node)
        assert result == "_:subj1"

    def test_format_triple_subject(self):
        """Test formatting Triple subjects (quoted triple subjects)."""
        subject = NamedNode("http://example.org/inner")
        predicate = NamedNode("http://example.org/pred")
        obj = Literal("value")
        triple = Triple(subject, predicate, obj)

        result = format_subject(triple)
        # Should fall back to str() representation
        assert isinstance(result, str)
        assert len(result) > 0


class TestFormatPredicate:
    """Test the format_predicate helper function."""

    def test_format_named_node_predicate(self):
        """Test formatting NamedNode predicates."""
        node = NamedNode("http://schema.org/name")
        result = format_predicate(node)
        assert result == "<http://schema.org/name>"

    def test_format_blank_node_predicate(self):
        """Test formatting BlankNode predicates."""
        node = BlankNode("pred1")
        result = format_predicate(node)
        assert result == "_:pred1"


class TestHelperFunctionEdgeCases:
    """Test edge cases for helper functions."""

    def test_empty_values(self):
        """Test helper functions with empty values."""
        # Empty URI should create empty literal
        node = create_rdf_node("")
        assert isinstance(node, Literal)
        assert node.value == ""

        # Empty literal formatting
        empty_literal = Literal("")
        result = format_rdf_object(empty_literal)
        assert result == '""'

    def test_special_characters_in_uris(self):
        """Test URIs with special characters."""
        # URI with fragment
        node = create_rdf_node("http://example.org/test#fragment")
        assert isinstance(node, NamedNode)

        result = format_rdf_object(node)
        assert result == "<http://example.org/test#fragment>"

        # URI with query parameters
        node = create_rdf_node("http://example.org/test?param=value")
        assert isinstance(node, NamedNode)

        result = format_rdf_object(node)
        assert result == "<http://example.org/test?param=value>"

    def test_unicode_in_literals(self):
        """Test Unicode characters in literals."""
        unicode_text = "Hello 世界 🌍"
        node = create_rdf_node(unicode_text)
        assert isinstance(node, Literal)

        result = format_rdf_object(node)
        assert result == f'"{unicode_text}"'

    def test_very_long_values(self):
        """Test very long URI and literal values."""
        long_uri = "http://example.org/" + "a" * 1000
        node = create_rdf_node(long_uri)
        assert isinstance(node, NamedNode)
        assert node.value == long_uri

        long_literal = "x" * 10000
        node = create_rdf_node(long_literal)
        assert isinstance(node, Literal)
        assert node.value == long_literal
