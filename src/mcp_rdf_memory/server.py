"""
MCP RDF Memory Server

Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.
"""

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field
from pyoxigraph import (
    BlankNode,
    DefaultGraph,
    Literal,
    NamedNode,
    Quad,
    QueryBoolean,
    QuerySolutions,
    Store,
    Triple,
)

# Constants
URI_SCHEMES = ("http://", "https://")
FORBIDDEN_SPARQL_KEYWORDS = ["INSERT", "DELETE", "DROP", "CLEAR", "CREATE", "LOAD", "COPY", "MOVE", "ADD"]

# Create in-memory RDF store
store = Store()

mcp = FastMCP("RDF Memory")


def validate_uri(uri: str, context: str = "URI") -> None:
    """Validate that a string is a valid RDF identifier (URI, CURIE, URN, etc.)."""
    # Check for obviously invalid cases
    if not uri or uri.isspace():
        raise ToolError(f"{context} cannot be empty or whitespace-only")
    
    # Let pyoxigraph handle detailed URI validation
    # Accept: HTTP/HTTPS URIs, CURIEs (rdf:type), URNs (urn:uuid:123), etc.
    try:
        # Test if pyoxigraph can create a NamedNode with this URI
        NamedNode(uri)
    except ValueError as e:
        raise ToolError(f"{context} is not a valid RDF identifier: {e}") from e


def create_rdf_node(value: str) -> NamedNode | Literal:
    """Create an appropriate RDF node (NamedNode for URIs/CURIEs, Literal for other values)."""
    # Try to create a NamedNode first - if it fails, treat as Literal
    try:
        return NamedNode(value)
    except ValueError:
        # If NamedNode creation fails, treat as a literal value
        return Literal(value)


def format_rdf_object(obj: NamedNode | Literal | BlankNode | Triple) -> str:
    """Format an RDF object for display."""
    if isinstance(obj, NamedNode):
        return f"<{obj.value}>"
    if isinstance(obj, Literal):
        return f'"{obj.value}"'
    if isinstance(obj, BlankNode):
        return f"_:{obj.value}"
    # Triple case
    return str(obj)


def format_subject(subject: NamedNode | BlankNode | Triple) -> str:
    """Format an RDF subject for display."""
    if isinstance(subject, NamedNode):
        return f"<{subject.value}>"
    if isinstance(subject, BlankNode):
        return f"_:{subject.value}"
    # Triple case
    return str(subject)


def format_predicate(predicate: NamedNode | BlankNode) -> str:
    """Format an RDF predicate for display."""
    if isinstance(predicate, NamedNode):
        return f"<{predicate.value}>"
    # BlankNode case
    return f"_:{predicate.value}"


def _remove_sparql_comments_and_strings(query: str) -> str:
    """Remove comments and string literals from SPARQL query for keyword checking."""
    import re
    
    # Remove single-line comments (# comment)
    query = re.sub(r'#.*?$', ' ', query, flags=re.MULTILINE)
    
    # Remove string literals in single quotes
    query = re.sub(r"'[^']*'", ' ', query)
    
    # Remove string literals in double quotes  
    query = re.sub(r'"[^"]*"', ' ', query)
    
    # Remove multi-line string literals (triple quotes)
    query = re.sub(r'""".*?"""', ' ', query, flags=re.DOTALL)
    query = re.sub(r"'''.*?'''", ' ', query, flags=re.DOTALL)
    
    return query


class TripleModel(BaseModel):
    """Model for a single RDF triple."""

    subject: str = Field(description="URI string for the subject")
    predicate: str = Field(description="URI string for the predicate")
    object: str = Field(description="URI string or literal value for the object")
    graph: str | None = Field(default=None, description="Optional URI string for the named graph")


class QuadResult(BaseModel):
    """Model for a single RDF quad result."""

    subject: str = Field(description="Subject of the quad")
    predicate: str = Field(description="Predicate of the quad")
    object: str = Field(description="Object of the quad")
    graph: str = Field(description="Graph name (or 'default graph')")


@mcp.tool()
def add_triples(triples: list[TripleModel]) -> None:
    """Add multiple RDF triples to the store in a single transaction."""
    quads = []
    for i, triple in enumerate(triples):
        # Validate and create nodes using helper functions
        validate_uri(triple.subject, f"Triple {i + 1}: Subject")
        validate_uri(triple.predicate, f"Triple {i + 1}: Predicate")

        subject_node = NamedNode(triple.subject)
        predicate_node = NamedNode(triple.predicate)
        object_node = create_rdf_node(triple.object)

        # Create graph node if specified
        graph_node = None
        if triple.graph is not None:
            validate_uri(triple.graph, f"Triple {i + 1}: Graph")
            graph_node = NamedNode(triple.graph)

        # Create quad
        quad = Quad(subject_node, predicate_node, object_node, graph_node)
        quads.append(quad)

    # Add all quads in a single transaction
    try:
        store.extend(quads)
    except Exception as e:
        raise ToolError(f"Failed to store triples in RDF database: {e}") from e


@mcp.tool()
def quads_for_pattern(
    subject: str | None = None, predicate: str | None = None, object: str | None = None, graph: str | None = None
) -> list[QuadResult]:
    """Find quads matching the given pattern. Use None for wildcards."""
    # Convert string parameters to RDF nodes or None for wildcards
    try:
        # Validate non-None parameters first
        if subject is not None:
            validate_uri(subject, "Subject pattern")
            subject_node = NamedNode(subject)
        else:
            subject_node = None
            
        if predicate is not None:
            validate_uri(predicate, "Predicate pattern")
            predicate_node = NamedNode(predicate)
        else:
            predicate_node = None
            
        if object is not None:
            object_node = create_rdf_node(object)
        else:
            object_node = None
            
        if graph is not None:
            validate_uri(graph, "Graph pattern")
            graph_node = NamedNode(graph)
        else:
            graph_node = None
            
    except ToolError:
        # Re-raise ToolErrors from validation
        raise
    except ValueError as e:
        raise ToolError(f"Invalid identifier format in pattern parameters: {e}") from e

    # Query the store for matching quads
    try:
        quads = store.quads_for_pattern(subject_node, predicate_node, object_node, graph_node)
    except Exception as e:
        raise ToolError(f"Failed to execute pattern query against RDF store: {e}") from e

    # Convert to structured results
    results = []
    for quad in quads:
        # Format graph name
        if quad.graph_name is None or isinstance(quad.graph_name, DefaultGraph):
            graph_name = "default graph"
        else:
            graph_name = quad.graph_name.value

        results.append(
            QuadResult(
                subject=format_subject(quad.subject),
                predicate=format_predicate(quad.predicate),
                object=format_rdf_object(quad.object),
                graph=graph_name,
            )
        )

    return results


@mcp.tool()
def rdf_query(query: str) -> bool | list[dict] | list[QuadResult]:
    """Execute a read-only SPARQL query against the RDF store.

    Returns:
    - ASK queries: bool
    - SELECT queries: list[dict] (variable bindings)
    - CONSTRUCT/DESCRIBE queries: list[QuadResult]

    Modification queries (INSERT, DELETE, DROP, CLEAR) are not allowed.
    """
    # Validate query is read-only - check for forbidden keywords as actual operations
    # Remove comments and string literals before checking
    cleaned_query = _remove_sparql_comments_and_strings(query.upper())
    
    for keyword in FORBIDDEN_SPARQL_KEYWORDS:
        # Check if keyword appears as standalone operation (word boundary)
        import re
        if re.search(rf'\b{keyword}\b', cleaned_query):
            raise ToolError(f"Modification queries not allowed. '{keyword}' operations are forbidden.")

    # Execute the SPARQL query
    try:
        results = store.query(query)
    except ValueError as e:
        raise ToolError(f"Invalid SPARQL query syntax: {e}") from e
    except Exception as e:
        raise ToolError(f"Failed to execute SPARQL query against RDF store: {e}") from e

    # Return results based on query type

    # ASK query returns QueryBoolean
    if isinstance(results, QueryBoolean):
        return bool(results)

    # SELECT query returns QuerySolutions - convert to list of dicts
    if isinstance(results, QuerySolutions):
        solutions = []
        variables = results.variables
        for solution in results:
            binding = {}
            # Access each variable by name
            for var in variables:
                var_name = var.value  # Get variable name without ? prefix
                value = solution[var_name]
                if value is not None:
                    binding[var_name] = format_rdf_object(value)
            solutions.append(binding)
        return solutions

    # CONSTRUCT/DESCRIBE query returns QueryTriples - convert to QuadResult list
    return [
        QuadResult(
            subject=format_subject(triple.subject),
            predicate=format_predicate(triple.predicate),
            object=format_rdf_object(triple.object),
            graph="default graph",  # Triples from CONSTRUCT/DESCRIBE don't have explicit graphs
        )
        for triple in results
    ]


if __name__ == "__main__":
    mcp.run()
