# Edge Case Testing

## Core Edge Case Testing Philosophy

Edge case testing focuses on boundary conditions, special characters, and unusual but realistic data that might break serialization, storage, or retrieval processes.

## Unicode and Special Character Handling

Test handling of Unicode, quotes, and special characters that might cause serialization issues:

```python
@pytest.mark.asyncio
async def test_special_character_handling(client: Client) -> None:
    """Test handling of Unicode, quotes, and special characters."""
    
    edge_cases = [
        # Unicode from different languages
        {"subject": "http://example.org/unicode", "predicate": "http://schema.org/name", "object": "测试 Test тест"},
        
        # Emoji and symbols
        {"subject": "http://example.org/emoji", "predicate": "http://schema.org/description", "object": "Test with emoji: 🌍🔥💯"},
        
        # Quotes and escaping
        {"subject": "http://example.org/quotes", "predicate": "http://schema.org/note", "object": "Text with \"quotes\" and 'apostrophes'"},
        
        # Long strings (test serialization limits)
        {"subject": "http://example.org/long", "predicate": "http://schema.org/content", "object": "A" * 10000},
        
        # Special RDF characters
        {"subject": "http://example.org/special", "predicate": "http://schema.org/value", "object": "Text with <brackets> and & ampersands"},
        
        # Newlines and whitespace
        {"subject": "http://example.org/whitespace", "predicate": "http://schema.org/text", "object": "Text with\nnewlines\tand\ttabs"},
    ]
    
    for test_case in edge_cases:
        # Should not raise errors for valid Unicode
        await client.call_tool("add_triples", {"triples": [test_case]})
        
        # Verify round-trip preservation
        result = await client.call_tool("quads_for_pattern", {"subject": test_case["subject"]})
        content = result[0]
        assert isinstance(content, TextContent)
        
        retrieved_quad = json.loads(content.text)[0]
        # Original data should be preserved (accounting for RDF serialization)
        assert test_case["object"] in retrieved_quad["object"] or test_case["object"] == retrieved_quad["object"].strip('"')
```

## Complex Unicode and Encoding Testing

Test comprehensive Unicode edge cases that might break in different contexts:

```python
@pytest.mark.asyncio
async def test_comprehensive_unicode_edge_cases(client: Client) -> None:
    """Test comprehensive Unicode edge cases."""
    
    unicode_test_cases = [
        {
            "name": "mixed_scripts",
            "data": {
                "subject": "http://example.org/mixed",
                "predicate": "http://schema.org/name",
                "object": "English 中文 العربية हिन्दी русский"
            }
        },
        {
            "name": "mathematical_symbols",
            "data": {
                "subject": "http://example.org/math",
                "predicate": "http://schema.org/formula",
                "object": "∑∞∫∂∇⊕⊗⟨⟩∈∉⊆⊇∪∩"
            }
        },
        {
            "name": "currency_and_symbols",
            "data": {
                "subject": "http://example.org/currency",
                "predicate": "http://schema.org/price",
                "object": "€50 £40 ¥5000 $60 ₹3000 ₽2000"
            }
        },
        {
            "name": "emoji_combinations",
            "data": {
                "subject": "http://example.org/emoji",
                "predicate": "http://schema.org/reaction",
                "object": "👨‍👩‍👧‍👦 🏴󠁧󠁢󠁳󠁣󠁴󠁿 🇺🇸 🌈 ❤️‍🔥"
            }
        },
        {
            "name": "zero_width_characters",
            "data": {
                "subject": "http://example.org/zwc",
                "predicate": "http://schema.org/text",
                "object": "Text\u200Bwith\u200Czero\u200Dwidth\uFEFFcharacters"
            }
        },
        {
            "name": "right_to_left",
            "data": {
                "subject": "http://example.org/rtl",
                "predicate": "http://schema.org/text",
                "object": "Mixed \u202Eright-to-left\u202C text"
            }
        },
        {
            "name": "combining_characters",
            "data": {
                "subject": "http://example.org/combining",
                "predicate": "http://schema.org/text",
                "object": "a\u0300e\u0301i\u0302o\u0303u\u0308"  # Various diacritics
            }
        }
    ]
    
    for test_case in unicode_test_cases:
        original_data = test_case["data"]
        
        # Add data
        await client.call_tool("add_triples", {"triples": [original_data]})
        
        # Retrieve and verify preservation
        result = await client.call_tool("quads_for_pattern", {"subject": original_data["subject"]})
        content = result[0]
        assert isinstance(content, TextContent)
        
        retrieved_quad = json.loads(content.text)[0]
        
        # Verify Unicode content is preserved in some form
        original_text = original_data["object"]
        retrieved_text = retrieved_quad["object"]
        
        # Check for preservation (may be wrapped in quotes or escaped)
        assert (original_text in retrieved_text or 
                original_text == retrieved_text.strip('"') or
                original_text.encode('unicode_escape').decode() in retrieved_text)
```

## Extreme Whitespace and Control Character Testing

Test edge cases with various whitespace and control characters:

```python
@pytest.mark.asyncio
async def test_whitespace_and_control_characters(client: Client) -> None:
    """Test handling of extreme whitespace and control characters."""
    
    whitespace_cases = [
        {
            "name": "mixed_whitespace",
            "data": {
                "subject": "http://example.org/whitespace1",
                "predicate": "http://schema.org/text",
                "object": "Text with\n\r\t various\u2000\u2001\u2002 unicode\u00A0spaces"
            }
        },
        {
            "name": "leading_trailing_spaces",
            "data": {
                "subject": "http://example.org/whitespace2",
                "predicate": "http://schema.org/text",
                "object": "   Leading and trailing spaces   "
            }
        },
        {
            "name": "only_whitespace",
            "data": {
                "subject": "http://example.org/whitespace3",
                "predicate": "http://schema.org/text",
                "object": "   \t\n\r   "
            }
        },
        {
            "name": "zero_width_spaces",
            "data": {
                "subject": "http://example.org/whitespace4",
                "predicate": "http://schema.org/text",
                "object": "Text\u200Bwith\u200Czero\uFEFFwidth\u200Dspaces"
            }
        },
        {
            "name": "line_separators",
            "data": {
                "subject": "http://example.org/whitespace5",
                "predicate": "http://schema.org/text",
                "object": "Text\u2028with\u2029line\nseparators"
            }
        }
    ]
    
    for test_case in whitespace_cases:
        original_data = test_case["data"]
        
        # Should handle whitespace gracefully
        await client.call_tool("add_triples", {"triples": [original_data]})
        
        # Verify retrieval
        result = await client.call_tool("quads_for_pattern", {"subject": original_data["subject"]})
        content = result[0]
        assert isinstance(content, TextContent)
        
        retrieved_quad = json.loads(content.text)[0]
        
        # Whitespace should be preserved in some form
        assert len(retrieved_quad["object"].strip()) > 0 or test_case["name"] == "only_whitespace"
```

## Very Long String Testing

Test system behavior with extremely long strings:

```python
@pytest.mark.asyncio
async def test_very_long_strings(client: Client) -> None:
    """Test system behavior with very long strings."""
    
    long_string_cases = [
        {
            "name": "long_ascii",
            "length": 50000,
            "content": "A" * 50000
        },
        {
            "name": "long_unicode",
            "length": 10000,
            "content": "测试🌍" * 2500  # Each char may be multiple bytes
        },
        {
            "name": "long_mixed",
            "length": 20000,
            "content": ("Hello World! 你好世界! 🌍🎉 " * 800)[:20000]
        },
        {
            "name": "extremely_long",
            "length": 1000000,
            "content": ("X" * 1000000)
        }
    ]
    
    for test_case in long_string_cases:
        test_data = {
            "subject": f"http://example.org/long/{test_case['name']}",
            "predicate": "http://schema.org/content",
            "object": test_case["content"]
        }
        
        try:
            # Should handle long strings (up to reasonable limits)
            await client.call_tool("add_triples", {"triples": [test_data]})
            
            # Verify retrieval works
            result = await client.call_tool("quads_for_pattern", {"subject": test_data["subject"]})
            content = result[0]
            assert isinstance(content, TextContent)
            
            retrieved_quad = json.loads(content.text)[0]
            
            # Content should be preserved (may be truncated for extremely long strings)
            if test_case["length"] < 100000:
                # For reasonably sized strings, expect full preservation
                assert len(retrieved_quad["object"]) >= test_case["length"] * 0.9  # Allow for some encoding overhead
            else:
                # For extremely long strings, just verify something was stored
                assert len(retrieved_quad["object"]) > 1000
                
        except ToolError as e:
            # For extremely long strings, graceful failure is acceptable
            if test_case["length"] > 500000:
                assert "too long" in str(e).lower() or "limit" in str(e).lower()
            else:
                # Smaller strings should work
                raise
```

## Special URI Edge Cases

Test edge cases in URI handling:

```python
@pytest.mark.asyncio
async def test_uri_edge_cases(client: Client) -> None:
    """Test URI edge cases that might cause parsing issues."""
    
    uri_edge_cases = [
        {
            "name": "very_long_uri",
            "subject": "http://example.org/" + "very-long-path/" * 100 + "endpoint",
            "predicate": "http://schema.org/name",
            "object": "Long URI Test"
        },
        {
            "name": "unicode_in_uri",
            "subject": "http://example.org/测试/路径",
            "predicate": "http://schema.org/name", 
            "object": "Unicode URI Test"
        },
        {
            "name": "percent_encoded",
            "subject": "http://example.org/test%20with%20spaces",
            "predicate": "http://schema.org/name",
            "object": "Percent Encoded Test"
        },
        {
            "name": "complex_query_params",
            "subject": "http://example.org/test?param1=value1&param2=value%202&param3=%E6%B5%8B%E8%AF%95",
            "predicate": "http://schema.org/name",
            "object": "Query Params Test"
        },
        {
            "name": "fragment_identifier",
            "subject": "http://example.org/test#fragment-with-unicode-测试",
            "predicate": "http://schema.org/name",
            "object": "Fragment Test"
        },
        {
            "name": "port_and_userinfo",
            "subject": "http://user:pass@example.org:8080/path",
            "predicate": "http://schema.org/name",
            "object": "Complex URI Test"
        },
        {
            "name": "urn_format",
            "subject": "urn:uuid:12345678-1234-5678-9abc-123456789abc",
            "predicate": "http://schema.org/name",
            "object": "URN Test"
        }
    ]
    
    for test_case in uri_edge_cases:
        try:
            await client.call_tool("add_triples", {"triples": [test_case]})
            
            # Verify retrieval works
            result = await client.call_tool("quads_for_pattern", {"subject": test_case["subject"]})
            content = result[0]
            assert isinstance(content, TextContent)
            
            retrieved_quad = json.loads(content.text)[0]
            assert test_case["object"] in retrieved_quad["object"]
            
        except ToolError as e:
            # Some complex URIs might not be supported - that's acceptable if clearly indicated
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in ["uri", "invalid", "format", "scheme"])
```

## Boundary Value Testing

Test boundary conditions in data size and structure:

```python
@pytest.mark.asyncio
async def test_boundary_value_conditions(client: Client) -> None:
    """Test boundary conditions in data size and structure."""
    
    # Test empty values (edge of validity)
    boundary_cases = [
        {
            "name": "minimal_valid_data",
            "data": {
                "subject": "http://a.b",  # Minimal valid URI
                "predicate": "http://c.d", 
                "object": "x"  # Single character
            }
        },
        {
            "name": "maximum_reasonable_batch",
            "data": [
                {
                    "subject": f"http://example.org/batch/item{i}",
                    "predicate": "http://schema.org/index",
                    "object": str(i)
                }
                for i in range(1000)  # Large but reasonable batch
            ]
        }
    ]
    
    # Test minimal valid data
    minimal_case = boundary_cases[0]
    await client.call_tool("add_triples", {"triples": [minimal_case["data"]]})
    
    result = await client.call_tool("quads_for_pattern", {"subject": minimal_case["data"]["subject"]})
    content = result[0]
    assert isinstance(content, TextContent)
    retrieved_quad = json.loads(content.text)[0]
    assert minimal_case["data"]["object"] in retrieved_quad["object"]
    
    # Test large batch
    large_batch_case = boundary_cases[1]
    await client.call_tool("add_triples", {"triples": large_batch_case["data"]})
    
    # Verify count of added items
    count_result = await client.call_tool("rdf_query", {
        "query": "SELECT (COUNT(?item) AS ?count) WHERE { ?item <http://schema.org/index> ?index }"
    })
    count_content = count_result[0]
    assert isinstance(count_content, TextContent)
    count_data = json.loads(count_content.text)[0]
    
    # Extract count (may be typed literal)
    count_value = count_data["count"]
    if "^^" in count_value:
        count_value = count_value.split("^^")[0].strip('"')
    assert int(count_value) >= 1000
```

## JSON Serialization Edge Cases

Test edge cases in JSON serialization and deserialization:

```python
@pytest.mark.asyncio
async def test_json_serialization_edge_cases(client: Client) -> None:
    """Test edge cases in JSON serialization."""
    
    # Add test data with challenging characters
    challenging_data = {
        "subject": "http://example.org/json-test",
        "predicate": "http://schema.org/content",
        "object": "Text with JSON chars: {\"key\": \"value\", \"array\": [1, 2, 3], \"null\": null, \"bool\": true}"
    }
    
    await client.call_tool("add_triples", {"triples": [challenging_data]})
    
    # Retrieve and ensure JSON parsing works
    result = await client.call_tool("quads_for_pattern", {"subject": challenging_data["subject"]})
    content = result[0]
    assert isinstance(content, TextContent)
    
    # Should be valid JSON
    raw_json = json.loads(content.text)
    assert isinstance(raw_json, list)
    assert len(raw_json) == 1
    
    # Should contain our challenging JSON content (may be escaped)
    quad_data = raw_json[0]
    retrieved_object = quad_data["object"]
    assert "key" in retrieved_object
    assert "value" in retrieved_object
    assert "array" in retrieved_object
```

## Performance Edge Cases

Test performance with edge case data patterns:

```python
@pytest.mark.asyncio
async def test_performance_edge_cases(client: Client) -> None:
    """Test performance with challenging data patterns."""
    
    import time
    
    # Test with many similar subjects (stress subject indexing)
    similar_subjects_start = time.time()
    
    similar_triples = []
    base_subject = "http://example.org/similar/"
    for i in range(100):
        similar_triples.append({
            "subject": f"{base_subject}{i:05d}",  # Similar but distinct subjects
            "predicate": "http://schema.org/name",
            "object": f"Similar Item {i}"
        })
    
    await client.call_tool("add_triples", {"triples": similar_triples})
    similar_subjects_time = time.time() - similar_subjects_start
    
    # Test querying with similar subjects
    query_start = time.time()
    result = await client.call_tool("quads_for_pattern", {"predicate": "http://schema.org/name"})
    query_time = time.time() - query_start
    
    # Should handle reasonable loads efficiently
    assert similar_subjects_time < 10.0, f"Adding similar subjects took too long: {similar_subjects_time:.2f}s"
    assert query_time < 5.0, f"Querying with many similar subjects took too long: {query_time:.2f}s"
    
    # Verify all data was added
    if isinstance(result, list):
        return  # Empty result
        
    content = result[0]
    assert isinstance(content, TextContent)
    retrieved_quads = json.loads(content.text)
    similar_quads = [q for q in retrieved_quads if "similar" in q["subject"].lower()]
    assert len(similar_quads) >= 100
```

## Common Edge Case Anti-Patterns

**Don't test artificial edge cases**:
```python
# ❌ Wrong - Artificial edge case that won't occur
{"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "\x00\x01\x02"}

# ✅ Correct - Realistic edge case
{"subject": "http://example.org/test", "predicate": "http://schema.org/name", "object": "Text with\nnewlines and\ttabs"}
```

**Don't ignore serialization preservation**:
```python
# ❌ Wrong - Not testing round-trip
await client.call_tool("add_triples", {"triples": [unicode_data]})

# ✅ Correct - Testing round-trip preservation
await client.call_tool("add_triples", {"triples": [unicode_data]})
result = await client.call_tool("quads_for_pattern", {"subject": unicode_data["subject"]})
assert unicode_data["object"] in json.loads(result[0].text)[0]["object"]
```

**Don't test only extreme cases**:
```python
# ❌ Wrong - Only testing extreme lengths
test_cases = ["A" * 1000000, "B" * 2000000]

# ✅ Correct - Testing realistic range of lengths
test_cases = ["Short", "Medium length text", "A" * 1000, "A" * 10000, "A" * 100000]
```