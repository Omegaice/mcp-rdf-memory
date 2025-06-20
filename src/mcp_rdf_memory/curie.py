"""
CURIE (Compact URI) handling functionality.

This module provides pure string functions for detecting and expanding CURIE patterns.
CURIEs are compact representations of URIs using the format 'prefix:localname'.

No external dependencies are required for the core functionality.
"""


def is_curie(value: str) -> bool:
    """Check if a string matches the CURIE pattern (prefix:localname).
    
    A valid CURIE must:
    - Not contain "://" (which indicates a full URI)
    - Have exactly one colon separator
    - Have a non-empty alphanumeric prefix (with optional _ or -)
    - Have a non-empty local part
    
    Args:
        value: String to check for CURIE pattern
        
    Returns:
        True if the string matches CURIE pattern, False otherwise
        
    Examples:
        >>> is_curie("rdf:type")
        True
        >>> is_curie("schema:name")
        True
        >>> is_curie("http://example.org/name")
        False
        >>> is_curie("no:colon:twice")
        False
        >>> is_curie("prefix:")
        False
        >>> is_curie(":localname")
        False
    """
    # Return False if string contains "://" (full URI)
    if "://" in value:
        return False
    
    # Check for exactly one colon separator
    parts = value.split(":")
    if len(parts) != 2:
        return False
    
    prefix, local = parts
    
    # Validate prefix part is alphanumeric (with _ or -)
    if not prefix:
        return False
    
    # Check if prefix contains only ASCII alphanumeric, underscore, or hyphen
    for char in prefix:
        if not (char.isascii() and (char.isalnum() or char in "_-")):
            return False
    
    # Ensure local part is non-empty
    return bool(local)