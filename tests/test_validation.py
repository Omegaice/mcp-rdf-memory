"""Tests for RDF validation functionality."""

import pytest

from mcp_rdf_memory.validation import is_empty_or_whitespace, validate_prefix


@pytest.mark.parametrize("value", [
    "",
    " ",
    "  ",
    "\t",
    "\n",
    "\r",
    "\r\n",
    "   \t  \n  ",
])
def test_is_empty_or_whitespace_returns_true(value: str) -> None:
    """Test that empty or whitespace-only strings return True."""
    assert is_empty_or_whitespace(value)


@pytest.mark.parametrize("value", [
    "text",
    " text ",
    "\ttext\t",
    "\ntext\n",
    "a",
    "123",
    "prefix-name",
    "prefix_name",
    "rdf",
    "schema",
])
def test_is_empty_or_whitespace_returns_false(value: str) -> None:
    """Test that non-empty strings with content return False."""
    assert not is_empty_or_whitespace(value)


@pytest.mark.parametrize("prefix", [
    "rdf",
    "rdfs",
    "owl",
    "foaf",
    "dc",
    "schema",
    "prefix123",
    "prefix_with_underscore",
    "prefix-with-dash",
    "a",
    "A",
    "ABC123",
    "test_prefix-123",
])
def test_validate_prefix_valid_prefixes(prefix: str) -> None:
    """Test that valid prefixes are accepted and returned trimmed."""
    result = validate_prefix(prefix)
    assert result == prefix.strip()


@pytest.mark.parametrize("prefix", [
    "",
    " ",
    "  ",
    "\t",
    "\n",
    "\r\n",
    "   \t  ",
])
def test_validate_prefix_empty_raises_error(prefix: str) -> None:
    """Test that empty or whitespace-only prefixes raise ValueError."""
    with pytest.raises(ValueError, match="Prefix cannot be empty or whitespace-only"):
        validate_prefix(prefix)


@pytest.mark.parametrize("prefix", [
    "pre:fix",
    "prefix:with:colons",
    "rdf:type",
    "schema:name",
    ":prefix",
    "prefix:",
    ":",
])
def test_validate_prefix_with_colons_raises_error(prefix: str) -> None:
    """Test that prefixes containing colons raise ValueError."""
    with pytest.raises(ValueError, match="Prefix should not contain colons"):
        validate_prefix(prefix)


@pytest.mark.parametrize("prefix", [
    "pre fix",          # Space
    "pre.fix",          # Dot
    "pre/fix",          # Slash
    "pre@fix",          # At symbol
    "pre#fix",          # Hash
    "pre%fix",          # Percent
    "pre&fix",          # Ampersand
    "pre*fix",          # Asterisk
    "pre+fix",          # Plus
    "pre=fix",          # Equals
    "pre?fix",          # Question mark
    "pre!fix",          # Exclamation
    "pre(fix",          # Parenthesis
    "pre)fix",          # Parenthesis
    "pre[fix",          # Bracket
    "pre]fix",          # Bracket
    "pre{fix",          # Brace
    "pre}fix",          # Brace
    "pre|fix",          # Pipe
    "pre\\fix",         # Backslash
    "pre\"fix",         # Quote
    "pre'fix",          # Apostrophe
    "pre<fix",          # Less than
    "pre>fix",          # Greater than
    "pre,fix",          # Comma
    "pre;fix",          # Semicolon
])
def test_validate_prefix_invalid_characters_raise_error(prefix: str) -> None:
    """Test that prefixes with invalid characters raise ValueError."""
    with pytest.raises(ValueError, match="Prefix must contain only ASCII letters, numbers, hyphens, and underscores"):
        validate_prefix(prefix)


@pytest.mark.parametrize("prefix", [
    "café",             # Non-ASCII in prefix
    "αβγ",              # Greek letters
    "рус",              # Cyrillic
    "中文",              # Chinese
    "emoji😀",          # Emoji
])
def test_validate_prefix_unicode_characters_raise_error(prefix: str) -> None:
    """Test that prefixes with Unicode characters raise ValueError."""
    with pytest.raises(ValueError, match="Prefix must contain only ASCII letters, numbers, hyphens, and underscores"):
        validate_prefix(prefix)


@pytest.mark.parametrize("input_prefix,expected", [
    ("  rdf  ", "rdf"),
    ("\tschema\t", "schema"),
    ("\nfoaf\n", "foaf"),
    ("  test-prefix  ", "test-prefix"),
    ("\t prefix_123 \n", "prefix_123"),
])
def test_validate_prefix_trims_whitespace(input_prefix: str, expected: str) -> None:
    """Test that leading and trailing whitespace is trimmed from valid prefixes."""
    result = validate_prefix(input_prefix)
    assert result == expected


def test_validate_prefix_empty_string_error_message() -> None:
    """Test that empty string error message is clear."""
    with pytest.raises(ValueError) as exc_info:
        validate_prefix("")
    assert "Prefix cannot be empty or whitespace-only" in str(exc_info.value)


def test_validate_prefix_colon_error_message() -> None:
    """Test that colon error message is clear."""
    with pytest.raises(ValueError) as exc_info:
        validate_prefix("pre:fix")
    assert "Prefix should not contain colons" in str(exc_info.value)


def test_validate_prefix_invalid_character_error_message() -> None:
    """Test that invalid character error message is clear."""
    with pytest.raises(ValueError) as exc_info:
        validate_prefix("pre fix")
    assert "Prefix must contain only ASCII letters, numbers, hyphens, and underscores" in str(exc_info.value)


def test_validate_prefix_single_character_lowercase() -> None:
    """Test that single lowercase character prefix works."""
    assert validate_prefix("a") == "a"


def test_validate_prefix_single_character_uppercase() -> None:
    """Test that single uppercase character prefix works."""
    assert validate_prefix("Z") == "Z"


def test_validate_prefix_single_digit() -> None:
    """Test that single digit prefix works."""
    assert validate_prefix("1") == "1"


def test_validate_prefix_mixed_case() -> None:
    """Test that mixed case prefixes work."""
    assert validate_prefix("CamelCase") == "CamelCase"


def test_validate_prefix_mixed_case_with_numbers() -> None:
    """Test that mixed case with numbers works."""
    assert validate_prefix("MixedCase123") == "MixedCase123"


def test_validate_prefix_complex_valid_characters() -> None:
    """Test that complex combinations of valid characters work."""
    assert validate_prefix("complex_prefix-123") == "complex_prefix-123"


def test_validate_prefix_alphanumeric_with_underscores_and_hyphens() -> None:
    """Test that alphanumeric with underscores and hyphens works."""
    assert validate_prefix("a1b2c3_d4e5-f6") == "a1b2c3_d4e5-f6"