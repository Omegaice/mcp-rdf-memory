"""Tests for CURIE (Compact URI) handling functionality."""

import pytest

from mcp_rdf_memory.curie import is_curie


@pytest.mark.parametrize("curie", [
    "rdf:type",
    "schema:name", 
    "ex:alice",
    "foaf:knows",
    "dc:title",
    "skos:prefLabel",
    "a:b",  # Minimal valid CURIE
    "prefix_with_underscore:local",
    "prefix-with-dash:local", 
    "prefix123:local456",
    "a1b2:c3d4",
])
def test_valid_curie_patterns(curie: str) -> None:
    """Test that valid CURIE patterns return True."""
    assert is_curie(curie)


@pytest.mark.parametrize("uri", [
    "http://example.org/name",
    "https://schema.org/name",
    "ftp://example.com/file", 
    "mailto://user@example.com",
    "file://path/to/file",
    "urn://example:resource",
])
def test_full_uris_return_false(uri: str) -> None:
    """Test that full URIs (containing ://) return False."""
    assert not is_curie(uri)


@pytest.mark.parametrize("value", [
    "no:colon:twice",
    "three:colon:parts:here",
    "http:example:com", 
    "a:b:c:d",
])
def test_multiple_colons_return_false(value: str) -> None:
    """Test that strings with multiple colons return False."""
    assert not is_curie(value)


@pytest.mark.parametrize("value", [
    "nocolon",
    "justtext",
    "example",
    "123456",
    "under_score",
    "dash-here",
])
def test_no_colon_returns_false(value: str) -> None:
    """Test that strings without colons return False."""
    assert not is_curie(value)


@pytest.mark.parametrize("value", [
    ":localname",  # Empty prefix
    "prefix:",     # Empty local part
    ":",           # Both empty
])
def test_empty_parts_return_false(value: str) -> None:
    """Test that CURIEs with empty prefix or local parts return False."""
    assert not is_curie(value)


@pytest.mark.parametrize("value", [
    "pre fix:local",    # Space in prefix
    "pre.fix:local",    # Dot in prefix
    "pre/fix:local",    # Slash in prefix
    "pre@fix:local",    # At symbol in prefix
    "pre#fix:local",    # Hash in prefix
    "pre%fix:local",    # Percent in prefix
    "pre&fix:local",    # Ampersand in prefix
    "pre*fix:local",    # Asterisk in prefix
    "pre+fix:local",    # Plus in prefix
    "pre=fix:local",    # Equals in prefix
    "pre?fix:local",    # Question mark in prefix
    "pre!fix:local",    # Exclamation in prefix
    "pre(fix:local",    # Parenthesis in prefix
    "pre)fix:local",    # Parenthesis in prefix
    "pre[fix:local",    # Bracket in prefix
    "pre]fix:local",    # Bracket in prefix
    "pre{fix:local",    # Brace in prefix
    "pre}fix:local",    # Brace in prefix
    "pre|fix:local",    # Pipe in prefix
    "pre\\fix:local",   # Backslash in prefix
    "pre\"fix:local",   # Quote in prefix
    "pre'fix:local",    # Apostrophe in prefix
    "pre<fix:local",    # Less than in prefix
    "pre>fix:local",    # Greater than in prefix
    "pre,fix:local",    # Comma in prefix
    "pre;fix:local",    # Semicolon in prefix
])
def test_invalid_prefix_characters_return_false(value: str) -> None:
    """Test that prefixes with invalid characters return False."""
    assert not is_curie(value)


def test_empty_string_returns_false() -> None:
    """Test that empty string returns False."""
    assert not is_curie("")


def test_whitespace_only_string_returns_false() -> None:
    """Test that whitespace-only string returns False."""
    assert not is_curie("   ")


def test_single_character_no_colon_returns_false() -> None:
    """Test that single character without colon returns False."""
    assert not is_curie("a")


def test_just_colon_returns_false() -> None:
    """Test that just a colon returns False."""
    assert not is_curie(":")


def test_double_colon_returns_false() -> None:
    """Test that double colon returns False."""
    assert not is_curie("::")


def test_triple_colon_returns_false() -> None:
    """Test that triple colon returns False."""
    assert not is_curie(":::")


def test_too_many_colons_returns_false() -> None:
    """Test that strings with too many colons return False."""
    assert not is_curie("a:b:c")


def test_numeric_prefix_valid() -> None:
    """Test that numeric prefix is valid."""
    assert is_curie("123:abc")


def test_numeric_local_part_valid() -> None:
    """Test that numeric local part is valid."""
    assert is_curie("abc:123")


def test_underscores_in_both_parts_valid() -> None:
    """Test that underscores in both parts are valid."""
    assert is_curie("a_b:c_d")


def test_hyphens_in_both_parts_valid() -> None:
    """Test that hyphens in both parts are valid."""
    assert is_curie("a-b:c-d")


def test_mixed_characters_valid() -> None:
    """Test that mixed valid characters are accepted."""
    assert is_curie("a_1-2:b_3-4")


@pytest.mark.parametrize("value,expected", [
    ("café:bar", False),           # Non-ASCII in prefix
    ("foo:café", True),            # Non-ASCII in local (allowed)
    ("αβγ:δεζ", False),            # Greek letters in prefix
    ("рус:text", False),           # Cyrillic in prefix
    ("中文:text", False),           # Chinese in prefix
    ("emoji😀:text", False),       # Emoji in prefix
])
def test_unicode_characters(value: str, expected: bool) -> None:
    """Test behavior with Unicode characters."""
    assert is_curie(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("prefix :local", False),      # Space after prefix
    ("prefix: local", True),       # Space in local (allowed)
    ("prefix:\tlocal", True),      # Tab in local (allowed)
    ("prefix:\nlocal", True),      # Newline in local (allowed)
    (" prefix:local", False),      # Leading space in prefix
    ("prefix:local ", True),       # Trailing space in local (allowed)
    ("\tprefix:local", False),     # Tab in prefix
    ("pre\nfix:local", False),     # Newline in prefix
])
def test_whitespace_handling(value: str, expected: bool) -> None:
    """Test behavior with whitespace characters."""
    assert is_curie(value) == expected


@pytest.mark.parametrize("value,expected", [
    # Common RDF vocabularies
    ("rdf:type", True),
    ("rdfs:label", True),
    ("rdfs:comment", True),
    ("owl:Class", True),
    ("owl:ObjectProperty", True),
    ("foaf:Person", True),
    ("foaf:knows", True),
    ("dc:title", True),
    ("dc:creator", True),
    ("skos:Concept", True),
    ("skos:prefLabel", True),
    ("schema:Person", True),
    ("schema:name", True),
    ("dbo:birthPlace", True),
    ("dbr:Albert_Einstein", True),
    # Should not match full URIs
    ("http://www.w3.org/1999/02/22-rdf-syntax-ns#type", False),
    ("https://schema.org/Person", False),
    ("http://xmlns.com/foaf/0.1/Person", False),
])
def test_realistic_rdf_examples(value: str, expected: bool) -> None:
    """Test with realistic RDF namespace prefixes and terms."""
    assert is_curie(value) == expected