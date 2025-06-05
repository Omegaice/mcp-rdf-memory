# Pyoxigraph Documentation

## Overview

[Pyoxigraph](https://pyoxigraph.readthedocs.io/) is a Python graph database library that implements the SPARQL 1.1 standard. Built on the high-performance Rust-based [Oxigraph](https://github.com/oxigraph/oxigraph) library using PyO3 bindings, it provides a complete RDF triple store with full SPARQL query and update capabilities.

**Key Features:**
- Complete SPARQL 1.1 implementation (SELECT, CONSTRUCT, ASK, DESCRIBE, UPDATE)
- High-performance Rust backend with Python convenience
- Multiple RDF format support (JSON-LD, Turtle, N-Triples, RDF/XML, etc.)
- In-memory and persistent storage options
- Named graph support for context separation
- ACID transactions with "repeatable read" isolation
- Comprehensive I/O operations

## Installation

### Standard Installation
```bash
pip install pyoxigraph
```

### Alternative Sources
```bash
# Via conda-forge
conda install -c conda-forge pyoxigraph

# Development version (requires Git submodules)
git clone --recursive https://github.com/oxigraph/oxigraph.git
cd oxigraph/python
pip install .
```

**Requirements:** Python 3.8+

## Core Concepts

### RDF Model Classes

#### NamedNode
Represents IRIs (Internationalized Resource Identifiers):
```python
from pyoxigraph import NamedNode

# Create a named node
node = NamedNode("http://example.com/resource")
print(node.value)  # "http://example.com/resource"
print(str(node))   # "<http://example.com/resource>"
```

#### BlankNode
Represents anonymous RDF nodes:
```python
from pyoxigraph import BlankNode

# Auto-generated identifier
blank1 = BlankNode()

# Custom identifier
blank2 = BlankNode("custom_id")
```

#### Literal
Represents RDF literal values with optional datatype and language tags:
```python
from pyoxigraph import Literal

# Simple string literal
simple = Literal("hello")

# Language-tagged literal
lang_literal = Literal("hello", language="en")

# Typed literal
from pyoxigraph import XSD_INTEGER
int_literal = Literal(42, datatype=XSD_INTEGER)

# Python types automatically converted
bool_literal = Literal(True)
float_literal = Literal(3.14)
```

#### Triple and Quad
RDF statements in subject-predicate-object form:
```python
from pyoxigraph import Triple, Quad, NamedNode, Literal

subject = NamedNode("http://example.com/person")
predicate = NamedNode("http://schema.org/name")
object = Literal("John Doe")

# Triple (no graph context)
triple = Triple(subject, predicate, object)

# Quad (with named graph)
graph = NamedNode("http://example.com/graph1")
quad = Quad(subject, predicate, object, graph)
```

#### Dataset
In-memory collection of RDF quads:
```python
from pyoxigraph import Dataset, Quad

dataset = Dataset()
dataset.add(quad)
dataset.remove(quad)

# Query operations
quads_with_subject = dataset.quads_for_subject(subject)
quads_with_predicate = dataset.quads_for_predicate(predicate)
```

## Store Operations

### Store Creation
```python
from pyoxigraph import Store

# In-memory store (fast, temporary)
memory_store = Store()

# Persistent store (disk-based)
persistent_store = Store("/path/to/storage/directory")

# Read-only store
readonly_store = Store("/path/to/storage", read_only=True)
```

### Data Manipulation

#### Adding Data
```python
# Single quad
store.add(quad)

# Multiple quads (atomic transaction)
quads = [quad1, quad2, quad3]
store.extend(quads)

# Bulk insert (optimized, less transactional safety)
store.bulk_extend(quad_iterator)

# Bulk load from file
with open("data.nq", "rb") as file:
    store.bulk_load(file, "application/n-quads")
```

#### Removing Data
```python
# Remove specific quad
store.remove(quad)

# Clear entire store
store.clear()

# Clear specific named graph
graph_name = NamedNode("http://example.com/graph1")
store.clear_graph(graph_name)

# Remove entire named graph
store.remove_graph(graph_name)
```

#### Graph Management
```python
# Add named graph
store.add_graph(graph_name)

# List all named graphs
graphs = list(store.named_graphs())

# Check if graph exists
if graph_name in store.named_graphs():
    print("Graph exists")
```

### Querying

#### Pattern-Based Queries
```python
# Find quads matching pattern (None = wildcard)
results = store.quads_for_pattern(
    subject=NamedNode("http://example.com/person"),
    predicate=None,  # Any predicate
    object=None,     # Any object
    graph_name=None  # Any graph
)

for quad in results:
    print(f"Found: {quad}")
```

#### SPARQL Queries
```python
# SELECT query
select_query = """
SELECT ?name ?email WHERE {
    ?person <http://schema.org/name> ?name .
    ?person <http://schema.org/email> ?email .
}
"""

for binding in store.query(select_query):
    name = binding["name"].value
    email = binding["email"].value
    print(f"Name: {name}, Email: {email}")

# ASK query (boolean result)
ask_query = "ASK { ?s <http://schema.org/name> 'John Doe' }"
result = store.query(ask_query)
print(f"John Doe exists: {result}")

# CONSTRUCT query
construct_query = """
CONSTRUCT { ?person <http://example.com/hasName> ?name }
WHERE { ?person <http://schema.org/name> ?name }
"""
constructed_triples = list(store.query(construct_query))
```

#### Advanced Query Options
```python
# Query with options
results = store.query(select_query, {
    "base_iri": "http://example.com/",
    "use_default_graph_as_union": True,
    "default_graph": [NamedNode("http://example.com/default")],
    "named_graphs": [NamedNode("http://example.com/graph1")],
    "results_format": "json"  # or "xml", "csv", "tsv"
})
```

### SPARQL Updates
```python
# INSERT DATA
insert_query = """
INSERT DATA {
    <http://example.com/person1> <http://schema.org/name> "Alice" .
    <http://example.com/person1> <http://schema.org/email> "alice@example.com" .
}
"""
store.update(insert_query)

# DELETE/INSERT with WHERE clause
update_query = """
DELETE { ?person <http://schema.org/email> ?oldEmail }
INSERT { ?person <http://schema.org/email> "newemail@example.com" }
WHERE {
    ?person <http://schema.org/name> "Alice" .
    ?person <http://schema.org/email> ?oldEmail .
}
"""
store.update(update_query)

# DELETE WHERE
delete_query = """
DELETE WHERE {
    <http://example.com/person1> ?predicate ?object .
}
"""
store.update(delete_query)
```

## I/O Operations

### Supported RDF Formats

| Format | Media Type | File Extension | Description |
|--------|------------|----------------|-------------|
| Turtle | `text/turtle` | `.ttl` | Compact, human-readable |
| N-Triples | `application/n-triples` | `.nt` | Simple line-based |
| N-Quads | `application/n-quads` | `.nq` | N-Triples with graphs |
| TriG | `application/trig` | `.trig` | Turtle with named graphs |
| JSON-LD | `application/ld+json` | `.jsonld` | JSON-based RDF |
| RDF/XML | `application/rdf+xml` | `.rdf` | XML-based (legacy) |

### Loading Data

#### From Files
```python
# Load from file path
store.load("/path/to/data.ttl", format="text/turtle")

# Load with base IRI
store.load("/path/to/data.ttl", {
    "format": "text/turtle",
    "base_iri": "http://example.com/"
})

# Load into specific graph
store.load("/path/to/data.ttl", {
    "format": "text/turtle",
    "to_graph_name": NamedNode("http://example.com/graph1")
})
```

#### From Strings/Bytes
```python
turtle_data = """
@prefix schema: <http://schema.org/> .
<http://example.com/person1> schema:name "Alice" ;
                            schema:email "alice@example.com" .
"""

store.load(turtle_data.encode(), {
    "format": "text/turtle",
    "base_iri": "http://example.com/"
})
```

#### Bulk Loading
```python
# Efficient bulk loading for large datasets
with open("large_dataset.nq", "rb") as file:
    store.bulk_load(file, "application/n-quads")
```

### Exporting Data

#### Dump Entire Store
```python
# Export all data
turtle_output = store.dump(format="text/turtle")
print(turtle_output.decode())

# Export to file
with open("export.ttl", "wb") as file:
    store.dump(file, format="text/turtle")
```

#### Export Specific Graph
```python
# Export named graph
graph_data = store.dump({
    "format": "text/turtle",
    "from_graph_name": NamedNode("http://example.com/graph1")
})

# Export default graph only
default_graph_data = store.dump({
    "format": "application/n-triples",
    "from_graph_name": None  # Default graph
})
```

### Parsing Utilities
```python
from pyoxigraph import parse

# Parse RDF from various sources
triples = parse(
    input=turtle_string,
    format="text/turtle",
    base_iri="http://example.com/"
)

for triple in triples:
    print(triple)
```

## Performance Considerations

### Storage Options
- **In-memory**: Fastest for small to medium datasets, data lost on restart
- **Persistent**: Suitable for large datasets, survives restarts
- **Read-only**: Optimized for query-heavy workloads

### Bulk Operations
```python
# Prefer bulk operations for large datasets
quads = [generate_quad(i) for i in range(10000)]

# Fast bulk insert
store.bulk_extend(quads)

# For maximum performance with large files
with open("huge_dataset.nq", "rb") as file:
    store.bulk_load(file, "application/n-quads")
```

### Query Optimization
- Use specific patterns instead of wildcards when possible
- Leverage named graphs for data organization
- Consider indexing strategies for frequent query patterns

### Memory Management
```python
# For processing large result sets
for binding in store.query("SELECT * WHERE { ?s ?p ?o }"):
    # Process one binding at a time
    process_binding(binding)
    # Binding is automatically freed
```

## Error Handling

### Common Error Patterns
```python
from pyoxigraph import Store, NamedNode, SyntaxError

try:
    # Invalid URI
    invalid_node = NamedNode("not-a-valid-uri")
except ValueError as e:
    print(f"Invalid URI: {e}")

try:
    # Invalid SPARQL query
    store.query("INVALID SPARQL SYNTAX")
except SyntaxError as e:
    print(f"SPARQL syntax error: {e}")

try:
    # File I/O errors
    store.load("/nonexistent/file.ttl")
except OSError as e:
    print(f"File error: {e}")
```

### Best Practices
```python
def safe_query(store, query_string):
    """Safely execute a SPARQL query with error handling."""
    try:
        return list(store.query(query_string))
    except SyntaxError as e:
        print(f"SPARQL syntax error: {e}")
        return []
    except Exception as e:
        print(f"Query execution error: {e}")
        return []

def safe_add_triple(store, subject_uri, predicate_uri, object_value):
    """Safely add a triple with validation."""
    try:
        subject = NamedNode(subject_uri)
        predicate = NamedNode(predicate_uri)
        
        if isinstance(object_value, str) and object_value.startswith("http"):
            object_node = NamedNode(object_value)
        else:
            object_node = Literal(object_value)
            
        quad = Quad(subject, predicate, object_node)
        store.add(quad)
        return True
    except (ValueError, TypeError) as e:
        print(f"Failed to add triple: {e}")
        return False
```

## Migration Guide

### Version 0.3 to 0.4 Changes
- **Python Support**: Dropped Python 3.7
- **Error Handling**: `OSError` replaces `IOError`
- **Parameter Names**: `mime_type` → `format` in I/O functions
- **Query Results**: Boolean results now use `QueryBoolean` class

### Version 0.2 to 0.3 Migration
Major storage format change requires data migration:

```python
# Step 1: Export from old SledStore (v0.2)
from pyoxigraph import SledStore  # v0.2 only

old_store = SledStore('/old/storage/path')
with open('migration_temp.nq', 'wb') as fp:
    old_store.dump(fp, "application/n-quads")

# Step 2: Import to new Store (v0.3+)
from pyoxigraph import Store

new_store = Store('/new/storage/path')
with open('migration_temp.nq', 'rb') as fp:
    new_store.bulk_load(fp, "application/n-quads")
```

## Advanced Features

### Named Graphs for Context Management
```python
# Organize data by context
conversation_graph = NamedNode("http://mcp.local/context/conversation-123")
project_graph = NamedNode("http://mcp.local/context/project-abc")

# Add data to specific contexts
store.add(Quad(subject, predicate, object, conversation_graph))

# Query specific context
context_query = """
SELECT ?s ?p ?o FROM <http://mcp.local/context/conversation-123>
WHERE { ?s ?p ?o }
"""
```

### Transaction Safety
```python
# Atomic operations
try:
    quads_to_add = [quad1, quad2, quad3]
    store.extend(quads_to_add)  # All succeed or all fail
except Exception as e:
    print(f"Transaction failed: {e}")
    # Store remains in consistent state
```

### Custom Functions in SPARQL
```python
# SPARQL queries can use built-in functions
function_query = """
SELECT ?person ?name_length WHERE {
    ?person <http://schema.org/name> ?name .
    BIND(STRLEN(?name) AS ?name_length)
    FILTER(?name_length > 5)
}
"""
```

## Use Cases for MCP RDF Memory

### Knowledge Graph Building
```python
# Build a person-knowledge graph
def add_person(store, person_uri, name, knows_uris=None):
    knows_uris = knows_uris or []
    
    person = NamedNode(person_uri)
    name_pred = NamedNode("http://xmlns.com/foaf/0.1/name")
    knows_pred = NamedNode("http://xmlns.com/foaf/0.1/knows")
    
    # Add name
    store.add(Quad(person, name_pred, Literal(name)))
    
    # Add relationships
    for friend_uri in knows_uris:
        friend = NamedNode(friend_uri)
        store.add(Quad(person, knows_pred, friend))

# Usage
add_person(store, "http://example.org/john", "John Doe", 
          ["http://example.org/jane", "http://example.org/bob"])
```

### Semantic Search
```python
def find_connections(store, person_name, relationship_depth=2):
    """Find people connected to a person within N degrees."""
    query = f"""
    SELECT DISTINCT ?connected ?name WHERE {{
        ?person <http://xmlns.com/foaf/0.1/name> "{person_name}" .
        ?person (<http://xmlns.com/foaf/0.1/knows>){{1,{relationship_depth}}} ?connected .
        ?connected <http://xmlns.com/foaf/0.1/name> ?name .
    }}
    """
    
    connections = []
    for binding in store.query(query):
        connections.append({
            'uri': binding['connected'].value,
            'name': binding['name'].value
        })
    
    return connections
```

### Context-Aware Memory
```python
def store_conversation_memory(store, conversation_id, speaker, message, timestamp):
    """Store conversation data in a named graph."""
    graph = NamedNode(f"http://mcp.local/conversation/{conversation_id}")
    
    message_uri = NamedNode(f"http://mcp.local/message/{timestamp}")
    
    # Message properties
    store.add(Quad(message_uri, NamedNode("http://schema.org/author"), Literal(speaker), graph))
    store.add(Quad(message_uri, NamedNode("http://schema.org/text"), Literal(message), graph))
    store.add(Quad(message_uri, NamedNode("http://schema.org/dateCreated"), Literal(timestamp), graph))

def retrieve_conversation_history(store, conversation_id, limit=10):
    """Retrieve recent messages from a conversation."""
    query = f"""
    SELECT ?author ?text ?timestamp 
    FROM <http://mcp.local/conversation/{conversation_id}>
    WHERE {{
        ?message <http://schema.org/author> ?author ;
                <http://schema.org/text> ?text ;
                <http://schema.org/dateCreated> ?timestamp .
    }}
    ORDER BY DESC(?timestamp)
    LIMIT {limit}
    """
    
    return list(store.query(query))
```

## Testing and Development

### Unit Testing
```python
import unittest
from pyoxigraph import Store, NamedNode, Literal, Quad

class TestRDFStore(unittest.TestCase):
    def setUp(self):
        self.store = Store()  # In-memory for testing
        
    def test_add_and_query(self):
        # Add test data
        subject = NamedNode("http://test.com/person")
        predicate = NamedNode("http://schema.org/name")
        object_val = Literal("Test Person")
        
        self.store.add(Quad(subject, predicate, object_val))
        
        # Query back
        results = list(self.store.query(
            'SELECT ?name WHERE { <http://test.com/person> <http://schema.org/name> ?name }'
        ))
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'].value, "Test Person")

if __name__ == '__main__':
    unittest.main()
```

### Performance Testing
```python
import time
from pyoxigraph import Store, NamedNode, Literal, Quad

def benchmark_insertions(num_triples=10000):
    store = Store()
    
    start_time = time.time()
    
    quads = []
    for i in range(num_triples):
        subject = NamedNode(f"http://example.com/entity{i}")
        predicate = NamedNode("http://schema.org/name")
        object_val = Literal(f"Entity {i}")
        quads.append(Quad(subject, predicate, object_val))
    
    store.bulk_extend(quads)
    
    end_time = time.time()
    
    print(f"Inserted {num_triples} triples in {end_time - start_time:.2f} seconds")
    print(f"Rate: {num_triples / (end_time - start_time):.0f} triples/second")
```

## Resources and Links

### Official Documentation
- [Pyoxigraph Documentation](https://pyoxigraph.readthedocs.io/)
- [Oxigraph GitHub Repository](https://github.com/oxigraph/oxigraph)
- [Python Package Index (PyPI)](https://pypi.org/project/pyoxigraph/)
- [Conda Forge Package](https://anaconda.org/conda-forge/pyoxigraph)

### Community and Support
- [GitHub Discussions](https://github.com/oxigraph/oxigraph/discussions)
- [Gitter Chat](https://gitter.im/oxigraph/community)
- [Issue Tracker](https://github.com/oxigraph/oxigraph/issues)

### Standards and Specifications
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [SPARQL 1.1 Update](https://www.w3.org/TR/sparql11-update/)
- [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/)
- [Turtle Specification](https://www.w3.org/TR/turtle/)
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)

### Related Libraries
- [OxRDFLib](https://github.com/oxigraph/oxrdflib) - RDFLib store using Pyoxigraph
- [RDFLib](https://rdflib.readthedocs.io/) - Pure Python RDF library
- [PyO3](https://pyo3.rs/) - Rust-Python bindings framework

### Development Tools
- [Maturin](https://github.com/PyO3/maturin) - Build tool for PyO3 projects
- [Sphinx](https://www.sphinx-doc.org/) - Documentation generator
- [pytest](https://pytest.org/) - Testing framework

## Conclusion

Pyoxigraph provides a powerful, high-performance foundation for building RDF-based applications in Python. Its combination of Rust performance with Python convenience makes it ideal for the MCP RDF Memory server, offering:

- **Scalability**: Handles large datasets efficiently
- **Standards Compliance**: Full SPARQL 1.1 support
- **Flexibility**: Multiple storage and I/O options
- **Reliability**: ACID transactions and error handling
- **Developer Experience**: Pythonic API with comprehensive documentation

For the MCP RDF Memory project, pyoxigraph delivers all necessary features for semantic data persistence and querying, enabling LLMs to maintain structured, queryable memory using semantic web standards.