"""
MCP RDF Memory Server

Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.
"""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError, ToolError
from pydantic import BaseModel, Field, PlainValidator, RootModel, WithJsonSchema
from pyoxigraph import (
    DefaultGraph,
    Literal,
    NamedNode,
    Quad,
    QueryBoolean,
    QuerySolutions,
    RdfFormat,
    Store,
)

from .store_manager import StoreManager

# Constants
MCP_NAMESPACE = "http://mcp.local/"


def validate_rdf_identifier(value: str | NamedNode) -> str:
    """Validate and return string representation of RDF identifier."""
    if isinstance(value, NamedNode):
        return value.value

    if not value or value.isspace():
        raise ValueError("RDF identifier cannot be empty or whitespace-only")

    try:
        # Validate by creating NamedNode, but return string for JSON compatibility
        NamedNode(value)
        return value
    except ValueError as e:
        raise ValueError(f"Invalid RDF identifier: {e}") from e


def validate_rdf_node(value: str | NamedNode | Literal) -> str:
    """Validate and return string representation of RDF node."""
    if isinstance(value, NamedNode | Literal):
        return value.value

    if not value or value.isspace():
        raise ValueError("RDF node value cannot be empty")

    # All strings are valid as RDF nodes (either identifiers or literals)
    return value


def validate_prefix(prefix: str) -> str:
    """Validate RDF prefix format."""
    if not prefix or prefix.isspace():
        raise ValueError("Prefix cannot be empty or whitespace-only")

    # Prefix should not contain colons (that's for CURIEs)
    if ":" in prefix:
        raise ValueError("Prefix should not contain colons")

    # Should be a valid identifier pattern
    if not prefix.replace("_", "a").replace("-", "a").isalnum():
        raise ValueError("Prefix must contain only letters, numbers, hyphens, and underscores")

    return prefix.strip()


# Helper functions to convert validated strings back to RDF objects
def create_rdf_node(value: str) -> NamedNode | Literal:
    """Convert validated string to appropriate RDF node type."""
    try:
        return NamedNode(value)  # Try as identifier first
    except ValueError:
        return Literal(value)  # Fall back to literal


def create_graph_uri(graph_name: str | None) -> NamedNode | None:
    """Convert simple graph name to namespaced URI."""
    if graph_name is None or graph_name == "":
        return None
    if not graph_name.strip():
        raise ToolError("Graph name cannot be whitespace-only")
    return NamedNode(f"http://mcp.local/{graph_name.strip()}")


def is_curie(value: str) -> bool:
    """Check if a string matches the CURIE pattern (prefix:localname)."""
    # Basic CURIE pattern: alphanumeric prefix, colon, non-empty local part
    # Does not match full URIs (which contain ://)
    if "://" in value:
        return False
    parts = value.split(":", 1)
    if len(parts) != 2:
        return False
    prefix, local = parts
    # Prefix should be alphanumeric (possibly with _ or -)
    # Local part should be non-empty
    return bool(prefix and local and prefix.replace("_", "a").replace("-", "a").isalnum())


def expand_curie(value: str, global_prefixes: dict[str, str], graph_prefixes: dict[str, str] | None = None) -> str:
    """Expand a CURIE to a full IRI if the prefix is defined.

    Args:
        value: The potential CURIE string
        global_prefixes: Global prefix mappings
        graph_prefixes: Graph-specific prefix mappings (override global)

    Returns:
        Expanded IRI if prefix is found, otherwise original value
    """
    if not is_curie(value):
        return value

    prefix, local = value.split(":", 1)

    # Check graph-specific prefixes first (they override global)
    if graph_prefixes and prefix in graph_prefixes:
        return graph_prefixes[prefix] + local

    # Check global prefixes
    if prefix in global_prefixes:
        return global_prefixes[prefix] + local

    # No prefix found, return as-is
    return value


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


# Result type definitions
FindTriplesResult = RootModel[list[QuadResult]]
SparqlSelectResult = RootModel[list[dict[str, str]]]
SparqlConstructResult = RootModel[list[QuadResult]]


class RDFMemoryServer:
    """RDF Memory server providing triple store capabilities with optional persistence."""

    def __init__(self, store_path: str | None = None) -> None:
        """Initialize RDF Memory server with optional persistent storage.

        Args:
            store_path: Path for persistent storage. If None, creates in-memory store.
        """
        self.store_path = store_path  # Keep for backward compatibility
        self.store_manager = StoreManager(store_path)

        # Initialize prefix storage with standard RDF namespaces
        self.global_prefixes: dict[str, str] = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "schema": "http://schema.org/",
        }
        self.graph_prefixes: dict[str, dict[str, str]] = {}

    @property
    def store(self) -> Store | None:
        """Access to store for backward compatibility. Only available for in-memory stores."""
        return self.store_manager.store

    def _remove_prefix(self, prefix: str, graph_name: str | None) -> None:
        """Remove a prefix from global or graph-specific storage."""
        if graph_name is None:
            self.global_prefixes.pop(prefix, None)
            return

        # Remove from graph-specific prefixes
        if graph_name not in self.graph_prefixes:
            return

        self.graph_prefixes[graph_name].pop(prefix, None)
        # Clean up empty graph prefix dict
        if not self.graph_prefixes[graph_name]:
            del self.graph_prefixes[graph_name]

    def _define_prefix(self, prefix: str, namespace_uri: str, graph_name: str | None) -> None:
        """Define a prefix in global or graph-specific storage."""
        if graph_name is None:
            self.global_prefixes[prefix] = namespace_uri
            return

        # Set graph-specific prefix
        if graph_name not in self.graph_prefixes:
            self.graph_prefixes[graph_name] = {}
        self.graph_prefixes[graph_name][prefix] = namespace_uri

    def rdf_define_prefix(self, prefix: str, namespace_uri: str | None = None, graph_name: str | None = None) -> None:
        """Define or remove RDF namespace prefix for SPARQL queries.

        Provide namespace_uri to define a prefix.
        Provide graph_name for graph-specific prefixes."""
        try:
            # Validate prefix format
            validated_prefix = validate_prefix(prefix)

            # Handle prefix removal
            if namespace_uri is None:
                self._remove_prefix(validated_prefix, graph_name)
                return

            # Handle prefix definition/update
            # Validate namespace URI
            try:
                NamedNode(namespace_uri)
            except ValueError as e:
                raise ToolError(f"Invalid namespace URI: {e}") from e

            self._define_prefix(validated_prefix, namespace_uri, graph_name)

        except ValueError as e:
            raise ToolError(f"Invalid prefix: {e}") from e
        except Exception as e:
            raise ToolError(f"Failed to define prefix: {e}") from e

    def rdf_add_triples(self, triples: list[TripleModel]) -> None:
        """Add RDF triples to the knowledge graph for simple batch operations.
        Use rdf_sparql_query for complex insertions."""
        quads = []
        for triple in triples:
            # Get graph-specific prefixes if graph is specified
            graph_prefixes = None
            if triple.graph_name and triple.graph_name in self.graph_prefixes:
                graph_prefixes = self.graph_prefixes[triple.graph_name]

            # Expand CURIEs to full IRIs
            expanded_subject = expand_curie(triple.subject, self.global_prefixes, graph_prefixes)
            expanded_predicate = expand_curie(triple.predicate, self.global_prefixes, graph_prefixes)
            expanded_object = expand_curie(triple.object, self.global_prefixes, graph_prefixes)

            # Convert validated strings to RDF objects
            subject_node = NamedNode(expanded_subject)
            predicate_node = NamedNode(expanded_predicate)
            object_node = create_rdf_node(expanded_object)
            graph_node = create_graph_uri(triple.graph_name)

            quad = Quad(subject_node, predicate_node, object_node, graph_node)
            quads.append(quad)

        # Add all quads in a single transaction
        try:
            with self.store_manager.get_store(read_only=False) as store:
                store.extend(quads)
                store.flush()  # Ensure data is written to disk
        except Exception as e:
            raise ToolError(f"Failed to store triples in RDF database: {e}") from e

    def rdf_find_triples(
        self,
        subject: RDFIdentifier | None = None,
        predicate: RDFIdentifier | None = None,
        object: RDFNode | None = None,
        graph_name: str | None = None,
    ) -> FindTriplesResult:
        """Find RDF triples matching the pattern. Use None for wildcards.
        Use rdf_sparql_query for complex queries."""
        # Convert validated strings to RDF objects for pattern matching
        subject_node = NamedNode(subject) if subject else None
        predicate_node = NamedNode(predicate) if predicate else None
        object_node = create_rdf_node(object) if object else None
        graph_node = create_graph_uri(graph_name)

        # Query the store for matching quads
        try:
            with self.store_manager.get_store(read_only=True) as store:
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

    def rdf_sparql_query(self, query: str) -> bool | SparqlSelectResult | SparqlConstructResult:
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
            with self.store_manager.get_store(read_only=True) as store:
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

    def export_all_graphs(self) -> str:
        """Export all RDF data from the triple store in N-Quads format."""
        # Should not return None because we are not setting output
        # Should not raise an exception because we are using a format that supports named graphs
        try:
            with self.store_manager.get_store(read_only=True) as store:
                serialized = store.dump(format=RdfFormat.N_QUADS, from_graph=None)
                assert serialized is not None
                return serialized.decode("utf-8")
        except Exception as e:
            raise ResourceError(f"Failed to export RDF data: {e}") from e

    def export_named_graph(self, graph_name: str) -> str:
        """Export a specific named graph in N-Triples format."""
        try:
            # Convert graph name to URI
            graph_uri = create_graph_uri(graph_name)

            # Export specific graph in N-Quads format
            with self.store_manager.get_store(read_only=True) as store:
                serialized = store.dump(format=RdfFormat.N_TRIPLES, from_graph=graph_uri)
                assert serialized is not None

                return serialized.decode("utf-8")
        except Exception as e:
            raise ResourceError(f"Failed to export graph '{graph_name}': {e}") from e

    def export_global_prefixes(self) -> dict[str, str]:
        """Export global RDF prefix definitions."""
        return self.global_prefixes

    def export_graph_prefixes(self, graph_name: str) -> dict[str, str]:
        """Export effective prefixes for specific graph (global + graph-specific)."""
        effective_prefixes = self.global_prefixes.copy()
        if graph_name in self.graph_prefixes:
            effective_prefixes.update(self.graph_prefixes[graph_name])
        return effective_prefixes


def register_mcp_server(server: RDFMemoryServer, mcp: FastMCP) -> None:
    """Register RDFMemoryServer methods with FastMCP instance."""
    # Register tools
    mcp.tool(server.rdf_define_prefix)
    mcp.tool(server.rdf_add_triples)
    mcp.tool(server.rdf_find_triples)
    mcp.tool(server.rdf_sparql_query)

    # Register resources
    mcp.resource("rdf://graph", mime_type="application/n-quads")(server.export_all_graphs)
    mcp.resource("rdf://graph/{graph_name}", mime_type="application/n-triples")(server.export_named_graph)
    mcp.resource("rdf://graph/prefix", mime_type="application/json")(server.export_global_prefixes)
    mcp.resource("rdf://graph/{graph_name}/prefix", mime_type="application/json")(server.export_graph_prefixes)
