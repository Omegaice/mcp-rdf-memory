"""
MCP RDF Memory Server

Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.
"""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, PlainValidator, RootModel, WithJsonSchema
from pyoxigraph import (
    DefaultGraph,
    Literal,
    NamedNode,
    Quad,
    QueryBoolean,
    QuerySolutions,
    Store,
)

# Create in-memory RDF store
store = Store()

mcp = FastMCP("RDF Memory")

def validate_rdf_identifier(value) -> str:
    """Validate and return string representation of RDF identifier."""
    if isinstance(value, NamedNode):
        return value.value

    if not isinstance(value, str):
        raise ValueError("RDF identifier must be a string")

    if not value or value.isspace():
        raise ValueError("RDF identifier cannot be empty or whitespace-only")

    try:
        # Validate by creating NamedNode, but return string for JSON compatibility
        NamedNode(value)
        return value
    except ValueError as e:
        raise ValueError(f"Invalid RDF identifier: {e}") from e


def validate_rdf_node(value) -> str:
    """Validate and return string representation of RDF node."""
    if isinstance(value, NamedNode | Literal):
        return value.value

    if not isinstance(value, str):
        raise ValueError("RDF node must be a string")

    if not value or value.isspace():
        raise ValueError("RDF node value cannot be empty")

    # All strings are valid as RDF nodes (either identifiers or literals)
    return value


# Helper functions to convert validated strings back to RDF objects
def create_rdf_identifier(value: str) -> NamedNode:
    """Convert validated string to NamedNode."""
    return NamedNode(value)


def create_rdf_node(value: str) -> NamedNode | Literal:
    """Convert validated string to appropriate RDF node type."""
    try:
        return NamedNode(value)  # Try as identifier first
    except ValueError:
        return Literal(value)  # Fall back to literal


def create_graph_uri(graph_name: str | None) -> NamedNode | None:
    """Convert simple graph name to namespaced URI."""
    if graph_name is None:
        return None
    if not graph_name.strip():
        raise ToolError("Graph name cannot be empty")
    return NamedNode(f"http://mcp.local/{graph_name.strip()}")


# Pydantic validated types with JSON schema support
RDFIdentifier = Annotated[
    str,
    PlainValidator(validate_rdf_identifier),
    WithJsonSchema({"type": "string", "description": "RDF identifier (URI, CURIE, URN, etc.)"}),
]

RDFNode = Annotated[
    str,
    PlainValidator(validate_rdf_node),
    WithJsonSchema({"type": "string", "description": "RDF node (identifier or literal value)"}),
]




class TripleModel(BaseModel):
    """Model for a single RDF triple."""

    subject: RDFIdentifier = Field(description="RDF identifier for the subject")
    predicate: RDFIdentifier = Field(description="RDF identifier for the predicate")
    object: RDFNode = Field(description="RDF node (identifier or literal) for the object")
    graph_name: str | None = Field(default=None, examples=["chat-123", "project/myapp"])


class QuadResult(BaseModel):
    """Model for a single RDF quad result."""

    subject: str = Field(description="Subject of the quad")
    predicate: str = Field(description="Predicate of the quad")
    object: str = Field(description="Object of the quad")
    graph: str = Field(description="Graph name (or 'default graph')")

@mcp.tool()
def rdf_add_triples(triples: list[TripleModel]) -> None:
    """Add RDF triples to the knowledge graph for simple batch operations.
    Use rdf_sparql_query for complex insertions."""
    quads = []
    for triple in triples:
        # Convert validated strings to RDF objects
        subject_node = create_rdf_identifier(triple.subject)
        predicate_node = create_rdf_identifier(triple.predicate)
        object_node = create_rdf_node(triple.object)
        graph_node = create_graph_uri(triple.graph_name)

        quad = Quad(subject_node, predicate_node, object_node, graph_node)
        quads.append(quad)

    # Add all quads in a single transaction
    try:
        store.extend(quads)
    except Exception as e:
        raise ToolError(f"Failed to store triples in RDF database: {e}") from e


FindTriplesResult = RootModel[list[QuadResult]]
SparqlSelectResult = RootModel[list[dict]]
SparqlConstructResult = RootModel[list[QuadResult]]

@mcp.tool()
def rdf_find_triples(
    subject: RDFIdentifier | None = None,
    predicate: RDFIdentifier | None = None,
    object: RDFNode | None = None,
    graph_name: str | None = Field(default=None, examples=["chat-123", "project/myapp"]),
) -> FindTriplesResult:
    """Find RDF triples matching the pattern. Use None for wildcards.
    Use rdf_sparql_query for complex queries."""
    # Convert validated strings to RDF objects for pattern matching
    subject_node = create_rdf_identifier(subject) if subject else None
    predicate_node = create_rdf_identifier(predicate) if predicate else None
    object_node = create_rdf_node(object) if object else None
    graph_node = create_graph_uri(graph_name)

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
                subject=str(quad.subject),
                predicate=str(quad.predicate),
                object=str(quad.object),
                graph=graph_name,
            )
        )

    return FindTriplesResult(results)


@mcp.tool()
def rdf_sparql_query(query: str) -> bool | SparqlSelectResult | SparqlConstructResult:
    """Execute read-only SPARQL queries for complex knowledge graph operations.

    Returns:
    - ASK queries: bool
    - SELECT queries: SparqlSelectResult (variable bindings)
    - CONSTRUCT/DESCRIBE queries: SparqlConstructResult

    Supports read operations only (SELECT, ASK, CONSTRUCT, DESCRIBE).
    Use rdf_add_triples for simple insertions.
    """
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
                    binding[var_name] = str(value)
            solutions.append(binding)
        return SparqlSelectResult(solutions)

    # CONSTRUCT/DESCRIBE query returns QueryTriples - convert to QuadResult list
    construct_results = [
        QuadResult(
            subject=str(triple.subject),
            predicate=str(triple.predicate),
            object=str(triple.object),
            graph="default graph",  # Triples from CONSTRUCT/DESCRIBE don't have explicit graphs
        )
        for triple in results
    ]
    return SparqlConstructResult(construct_results)


@mcp.tool()
def rdf_sparql_update(update: str) -> str:
    """Execute SPARQL UPDATE operations for complex knowledge graph modifications.
    
    Supports modification operations (INSERT, DELETE, etc.).
    Use rdf_add_triples for simple insertions.
    
    Note: This is a placeholder function - UPDATE operations are not yet implemented.
    """
    # Validate that update parameter is provided (for future implementation)
    if not update or not update.strip():
        raise ToolError("SPARQL UPDATE query cannot be empty")
    
    raise ToolError("SPARQL UPDATE operations are not yet implemented. Use rdf_add_triples for simple insertions.")

