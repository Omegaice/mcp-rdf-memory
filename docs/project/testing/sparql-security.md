# SPARQL Security Testing

## Core Security Principle

SPARQL security testing ensures that modification operations are blocked while allowing legitimate read operations. The system should prevent data corruption through malicious or accidental modification queries.

## Forbidden Operation Testing

Test that all modification operations are properly blocked:

```python
@pytest.mark.parametrize("forbidden_keyword", [
    "INSERT", "DELETE", "DROP", "CLEAR", "CREATE", "LOAD", "COPY", "MOVE", "ADD"
])
@pytest.mark.asyncio
async def test_sparql_query_should_reject_modification_operations(client: Client, forbidden_keyword: str) -> None:
    """Test that modification queries are properly blocked."""
    malicious_query = f"{forbidden_keyword} DATA {{ <http://example.org/test> <http://schema.org/name> \"hacked\" }}"
    
    with pytest.raises(ToolError) as exc_info:
        await client.call_tool("rdf_query", {"query": malicious_query})
    
    # Verify error message mentions the forbidden operation
    assert forbidden_keyword.lower() in str(exc_info.value).lower()
    assert "forbidden" in str(exc_info.value).lower()
```

## Case Sensitivity Security Testing

Ensure that case variations of forbidden operations are caught:

```python
@pytest.mark.asyncio
async def test_sparql_query_should_reject_case_variations(client: Client) -> None:
    """Test that case variations of forbidden operations are blocked."""
    case_variations = [
        "insert data { <http://test> <http://test> \"test\" }",
        "Insert Data { <http://test> <http://test> \"test\" }",
        "INSERT data { <http://test> <http://test> \"test\" }",
        "iNsErT dAtA { <http://test> <http://test> \"test\" }",
        "DELETE WHERE { ?s ?p ?o }",
        "delete where { ?s ?p ?o }",
        "Delete Where { ?s ?p ?o }",
        "dElEtE wHeRe { ?s ?p ?o }"
    ]
    
    for query in case_variations:
        with pytest.raises(ToolError):
            await client.call_tool("rdf_query", {"query": query})
```

## Comment and String Injection Testing

Test that forbidden keywords in comments or strings don't trigger false positives:

```python
@pytest.mark.asyncio
async def test_sparql_security_ignores_comments_and_strings(client: Client) -> None:
    """Test that keywords in comments and strings don't trigger security errors."""
    
    # Add test data first
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/test",
            "predicate": "http://schema.org/name",
            "object": "Test Person"
        }]
    })
    
    safe_queries = [
        # Keywords in comments should be ignored
        "SELECT ?name WHERE { # This query uses INSERT in comment\n ?s <http://schema.org/name> ?name }",
        
        # Keywords in string literals should be ignored
        "SELECT ?name WHERE { ?s <http://schema.org/name> ?name . FILTER(CONTAINS(?name, \"INSERT\")) }",
        
        # Keywords in single quotes should be ignored
        "SELECT ?name WHERE { ?s <http://schema.org/name> ?name . FILTER(?name = 'DELETE test') }",
        
        # Keywords in triple quotes should be ignored
        '''SELECT ?name WHERE { ?s <http://schema.org/name> ?name . FILTER(CONTAINS(?name, """INSERT test""")) }''',
    ]
    
    for query in safe_queries:
        # These should NOT raise ToolError - keywords are in safe contexts
        result = await client.call_tool("rdf_query", {"query": query})
        # Should execute successfully
        assert len(result) == 1
```

## Realistic Attack Vector Testing

Test SPARQL injection patterns that might realistically occur:

```python
@pytest.mark.asyncio
async def test_realistic_sparql_injection_attempts(client: Client) -> None:
    """Test realistic SPARQL injection patterns that might be attempted."""
    
    injection_attempts = [
        # Direct injection attempts
        "SELECT * WHERE { ?s ?p ?o } ; INSERT DATA { <http://malicious> <http://hacked> \"pwned\" }",
        
        # Union injection attempts
        "SELECT * WHERE { ?s ?p ?o } UNION { INSERT DATA { <http://evil> <http://bad> \"hacked\" } }",
        
        # Nested injection attempts
        "ASK { ?s ?p ?o . { INSERT DATA { <http://nested> <http://attack> \"evil\" } } }",
        
        # Comment-based attempts
        "SELECT * WHERE { ?s ?p ?o } /* */ INSERT DATA { <http://comment> <http://attack> \"bad\" }",
        
        # Whitespace evasion attempts
        "SELECT * WHERE { ?s ?p ?o }\n\nINSERT\nDATA\n{ <http://ws> <http://attack> \"spaced\" }",
        
        # Case mixing attempts
        "SELECT * WHERE { ?s ?p ?o } ; InSeRt DaTa { <http://mixed> <http://case> \"attack\" }",
    ]
    
    for injection_query in injection_attempts:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("rdf_query", {"query": injection_query})
        
        # Verify appropriate security error
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["forbidden", "not allowed", "modification"])
```

## Boundary Condition Security Testing

Test edge cases in security validation:

```python
@pytest.mark.asyncio
async def test_sparql_security_boundary_conditions(client: Client) -> None:
    """Test edge cases in SPARQL security validation."""
    
    # Test empty and whitespace queries
    edge_cases = [
        "",  # Empty query
        "   ",  # Whitespace only
        "\n\t\r",  # Various whitespace characters
        "# Just a comment",  # Comment only
        "/* Block comment only */",  # Block comment only
    ]
    
    for edge_query in edge_cases:
        with pytest.raises(ToolError):
            # Empty/whitespace queries should fail for different reasons than security
            await client.call_tool("rdf_query", {"query": edge_query})
    
    # Test very long queries with forbidden keywords
    long_forbidden_query = "SELECT * WHERE { ?s ?p ?o } " + "# comment " * 1000 + " INSERT DATA { <http://long> <http://attack> \"evil\" }"
    
    with pytest.raises(ToolError) as exc_info:
        await client.call_tool("rdf_query", {"query": long_forbidden_query})
    
    assert "insert" in str(exc_info.value).lower()
```

## Multi-Operation Security Testing

Test that combinations of read operations with forbidden operations are caught:

```python
@pytest.mark.asyncio
async def test_multi_operation_security_blocking(client: Client) -> None:
    """Test that multiple operations with forbidden keywords are blocked."""
    
    multi_operation_queries = [
        # SELECT followed by INSERT
        """
        SELECT ?s ?p ?o WHERE { ?s ?p ?o } ;
        INSERT DATA { <http://multi1> <http://attack> "evil1" }
        """,
        
        # ASK followed by DELETE
        """
        ASK { ?s <http://schema.org/name> ?name } ;
        DELETE WHERE { ?s ?p ?o }
        """,
        
        # CONSTRUCT followed by DROP
        """
        CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } ;
        DROP GRAPH <http://target>
        """,
        
        # Multiple forbidden operations
        """
        INSERT DATA { <http://first> <http://attack> "evil1" } ;
        DELETE WHERE { ?s ?p ?o } ;
        DROP ALL
        """,
    ]
    
    for multi_query in multi_operation_queries:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("rdf_query", {"query": multi_query})
        
        # Should catch at least one forbidden operation
        error_msg = str(exc_info.value).lower()
        forbidden_found = any(keyword in error_msg for keyword in ["insert", "delete", "drop", "forbidden"])
        assert forbidden_found
```

## Legitimate Query Validation

Ensure that legitimate SPARQL queries are not blocked:

```python
@pytest.mark.asyncio
async def test_legitimate_sparql_queries_allowed(client: Client) -> None:
    """Test that legitimate read-only queries are properly allowed."""
    
    # Add test data first
    await client.call_tool("add_triples", {
        "triples": [
            {
                "subject": "http://example.org/person1",
                "predicate": "http://schema.org/name",
                "object": "Alice Smith"
            },
            {
                "subject": "http://example.org/person1",
                "predicate": "http://schema.org/age",
                "object": "30"
            },
            {
                "subject": "http://example.org/person2",
                "predicate": "http://schema.org/name",
                "object": "Bob Jones"
            }
        ]
    })
    
    legitimate_queries = [
        # Basic SELECT
        "SELECT ?name WHERE { ?s <http://schema.org/name> ?name }",
        
        # SELECT with FILTER
        "SELECT ?name WHERE { ?s <http://schema.org/name> ?name . FILTER(CONTAINS(?name, \"Alice\")) }",
        
        # ASK query
        "ASK { ?s <http://schema.org/name> \"Alice Smith\" }",
        
        # CONSTRUCT query
        "CONSTRUCT { ?s <http://example.org/fullInfo> ?info } WHERE { ?s <http://schema.org/name> ?info }",
        
        # Complex SELECT with multiple patterns
        """
        SELECT ?name ?age WHERE {
            ?person <http://schema.org/name> ?name .
            ?person <http://schema.org/age> ?age .
            FILTER(?age > 25)
        }
        """,
        
        # DESCRIBE query
        "DESCRIBE <http://example.org/person1>",
        
        # Query with OPTIONAL
        """
        SELECT ?name ?age WHERE {
            ?person <http://schema.org/name> ?name .
            OPTIONAL { ?person <http://schema.org/age> ?age }
        }
        """,
        
        # Query with UNION
        """
        SELECT ?info WHERE {
            { ?s <http://schema.org/name> ?info }
            UNION
            { ?s <http://schema.org/age> ?info }
        }
        """,
    ]
    
    for legitimate_query in legitimate_queries:
        # These should NOT raise ToolError
        result = await client.call_tool("rdf_query", {"query": legitimate_query})
        
        # Should return valid result
        assert len(result) == 1
        content = result[0]
        assert isinstance(content, TextContent)
        
        # Should parse as valid JSON
        data = json.loads(content.text)
        # Validate result structure based on query type
        if "ASK" in legitimate_query.upper():
            assert isinstance(data, bool)
        else:
            assert isinstance(data, list)
```

## Security Performance Testing

Test that security validation doesn't significantly impact performance:

```python
@pytest.mark.asyncio
async def test_security_validation_performance(client: Client) -> None:
    """Test that security validation doesn't cause significant performance issues."""
    
    # Add test data
    await client.call_tool("add_triples", {
        "triples": [{
            "subject": "http://example.org/performance/test",
            "predicate": "http://schema.org/name",
            "object": "Performance Test"
        }]
    })
    
    # Test with increasingly complex but safe queries
    safe_complex_queries = [
        "SELECT ?name WHERE { ?s <http://schema.org/name> ?name }",
        
        "SELECT ?name WHERE { ?s <http://schema.org/name> ?name . FILTER(CONTAINS(?name, \"Test\")) }",
        
        """
        SELECT ?name WHERE {
            ?s <http://schema.org/name> ?name .
            # This is a very long comment that mentions INSERT and DELETE and CREATE
            # but should not trigger security validation because it's in a comment
            FILTER(CONTAINS(?name, "Performance"))
        }
        """,
        
        # Very long safe query
        "SELECT ?name WHERE { " + " ".join([f"# Comment {i}" for i in range(100)]) + " ?s <http://schema.org/name> ?name }",
    ]
    
    import time
    
    for query in safe_complex_queries:
        start_time = time.time()
        
        result = await client.call_tool("rdf_query", {"query": query})
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Security validation should not add significant overhead (< 1 second for test queries)
        assert execution_time < 1.0, f"Query took too long: {execution_time:.2f}s"
        
        # Should still return valid result
        assert len(result) == 1
        content = result[0]
        assert isinstance(content, TextContent)
```

## Error Message Quality Testing

Ensure security error messages are helpful for debugging:

```python
@pytest.mark.asyncio
async def test_security_error_message_quality(client: Client) -> None:
    """Test that security error messages provide helpful information."""
    
    test_cases = [
        {
            "query": "INSERT DATA { <http://test> <http://test> \"test\" }",
            "expected_keywords": ["insert", "forbidden", "not allowed"]
        },
        {
            "query": "DELETE WHERE { ?s ?p ?o }",
            "expected_keywords": ["delete", "forbidden", "not allowed"]
        },
        {
            "query": "DROP GRAPH <http://test>",
            "expected_keywords": ["drop", "forbidden", "not allowed"]
        },
    ]
    
    for test_case in test_cases:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("rdf_query", {"query": test_case["query"]})
        
        error_message = str(exc_info.value).lower()
        
        # Should mention the specific forbidden operation
        found_keywords = [kw for kw in test_case["expected_keywords"] if kw in error_message]
        assert len(found_keywords) >= 2, f"Error message missing keywords: {error_message}"
        
        # Should not expose internal implementation details
        internal_details = ["pyoxigraph", "regex", "implementation", "internal"]
        exposed_details = [detail for detail in internal_details if detail in error_message]
        assert len(exposed_details) == 0, f"Error message exposed internal details: {exposed_details}"
```

## Common SPARQL Security Anti-Patterns

**Don't test with unrealistic injection attempts**:
```python
# ❌ Wrong - Artificial injection that wouldn't occur in practice
"SELECT * FROM <javascript:alert('xss')> WHERE { ?s ?p ?o }"

# ✅ Correct - Realistic SPARQL modification attempts
"SELECT * WHERE { ?s ?p ?o } ; INSERT DATA { <http://realistic> <http://attack> \"data\" }"
```

**Don't skip case sensitivity testing**:
```python
# ❌ Wrong - Only testing uppercase
forbidden_operations = ["INSERT", "DELETE", "DROP"]

# ✅ Correct - Testing realistic case variations
case_variations = ["INSERT", "insert", "Insert", "iNsErT"]
```

**Don't test only direct injection**:
```python
# ❌ Wrong - Only testing direct keywords
"INSERT DATA { ... }"

# ✅ Correct - Testing complex injection patterns
"SELECT * WHERE { ?s ?p ?o } ; INSERT DATA { ... }"
```

**Don't ignore legitimate operations**:
```python
# ❌ Wrong - Only testing that forbidden operations fail

# ✅ Correct - Also testing that legitimate operations succeed
legitimate_queries = ["SELECT", "ASK", "CONSTRUCT", "DESCRIBE"]
for query_type in legitimate_queries:
    # Test that these work properly
```