"""
RDF validation functionality.

This module provides validation functions for RDF-related data structures.
It includes both pure string validation and RDF-specific validation that
may depend on external libraries like pyoxigraph.

Functions are organized into:
- Basic validation: Pure string validation functions
- RDF validation: Functions that work with RDF types and concepts
"""


def is_empty_or_whitespace(value: str) -> bool:
    """Check if a string is empty or contains only whitespace.

    This is a basic utility function used by other validation functions.

    Args:
        value: String to check

    Returns:
        True if the string is empty or whitespace-only, False otherwise

    Examples:
        >>> is_empty_or_whitespace("")
        True
        >>> is_empty_or_whitespace("   ")
        True
        >>> is_empty_or_whitespace("text")
        False
        >>> is_empty_or_whitespace(" text ")
        False
    """
    return not value or value.isspace()


def validate_prefix(prefix: str) -> str:
    """Validate RDF prefix format.

    A valid RDF prefix must:
    - Not be empty or whitespace-only
    - Not contain colons (those are for CURIEs)
    - Contain only alphanumeric characters, hyphens, and underscores

    Args:
        prefix: The prefix string to validate

    Returns:
        The trimmed prefix string if valid

    Raises:
        ValueError: If the prefix is invalid

    Examples:
        >>> validate_prefix("rdf")
        'rdf'
        >>> validate_prefix("my_prefix")
        'my_prefix'
        >>> validate_prefix("prefix-123")
        'prefix-123'
        >>> validate_prefix("")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ValueError: Prefix cannot be empty or whitespace-only
        >>> validate_prefix("pre:fix")  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ValueError: Prefix should not contain colons
    """
    if is_empty_or_whitespace(prefix):
        raise ValueError("Prefix cannot be empty or whitespace-only")

    # Trim whitespace first
    trimmed_prefix = prefix.strip()

    # Check again after trimming in case it becomes empty
    if not trimmed_prefix:
        raise ValueError("Prefix cannot be empty or whitespace-only")

    # Prefix should not contain colons (that's for CURIEs)
    if ":" in trimmed_prefix:
        raise ValueError("Prefix should not contain colons")

    # Should be a valid identifier pattern
    # Use same logic as CURIE validation but check entire string
    for char in trimmed_prefix:
        if not (char.isascii() and (char.isalnum() or char in "_-")):
            raise ValueError("Prefix must contain only ASCII letters, numbers, hyphens, and underscores")

    return trimmed_prefix
