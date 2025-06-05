"""
MCP RDF Memory Server

Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.
"""

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field
from pyoxigraph import BlankNode, DefaultGraph, Literal, NamedNode, Quad, QuerySolutions, QueryTriples, Store, Triple

# Constants
URI_SCHEMES = ("http://", "https://")
FORBIDDEN_SPARQL_KEYWORDS = ["INSERT", "DELETE", "DROP", "CLEAR", "CREATE", "LOAD", "COPY", "MOVE", "ADD"]

# Create in-memory RDF store
store = Store()

mcp = FastMCP("RDF Memory")


def validate_uri(uri: str, context: str = "URI") -> None:
    """Validate that a string is a valid HTTP(S) URI."""
    if not uri.startswith(URI_SCHEMES):
        raise ToolError(f"{context} must be a valid HTTP(S) URI")


def create_rdf_node(value: str) -> NamedNode | Literal:
    """Create an appropriate RDF node (NamedNode for URIs, Literal for other values)."""
    return NamedNode(value) if value.startswith(URI_SCHEMES) else Literal(value)


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


def format_triple(
    subject: NamedNode | BlankNode | Triple,
    predicate: NamedNode | BlankNode,
    obj: NamedNode | Literal | BlankNode | Triple,
    graph: NamedNode | BlankNode | DefaultGraph | None = None,
) -> str:
    """Format an RDF triple/quad for display."""
    subject_str = format_subject(subject)
    predicate_str = format_predicate(predicate)
    object_str = format_rdf_object(obj)

    # Handle graph case
    if graph is None or isinstance(graph, DefaultGraph):
        return f"{subject_str} {predicate_str} {object_str}"

    if isinstance(graph, NamedNode):
        return f"{subject_str} {predicate_str} {object_str} GRAPH <{graph.value}>"

    # BlankNode case
    return f"{subject_str} {predicate_str} {object_str} GRAPH _:{graph.value}"


def format_query_solutions(results: QuerySolutions) -> str:
    """Format SELECT query results (QuerySolutions) for display."""
    bindings = list(results)

    if not bindings:
        return "Query returned no results."

    formatted_results = []
    for i, binding in enumerate(bindings):
        binding_strs = []
        binding_str = str(binding)

        if "=" in binding_str:
            pairs = binding_str.strip("{}").split(", ")
            for pair in pairs:
                if "=" in pair:
                    var, val = pair.split("=", 1)
                    binding_strs.append(f"{var}: {val}")
                else:
                    binding_strs.append(pair)
        else:
            binding_strs.append(binding_str)

        formatted_results.append(f"Result {i + 1}: " + ", ".join(binding_strs))

    return f"Query returned {len(bindings)} result(s):\n" + "\n".join(formatted_results)


def format_query_triples(results: QueryTriples) -> str:
    """Format CONSTRUCT/DESCRIBE query results (QueryTriples) for display."""
    triples = list(results)

    if not triples:
        return "Query returned no triples."

    formatted_triples = []
    for triple in triples:
        formatted = format_triple(triple.subject, triple.predicate, triple.object)
        formatted_triples.append(f"{formatted} .")

    return f"Query returned {len(triples)} triple(s):\n" + "\n".join(formatted_triples)


class TripleModel(BaseModel):
    """Model for a single RDF triple."""

    subject: str = Field(description="URI string for the subject")
    predicate: str = Field(description="URI string for the predicate")
    object: str = Field(description="URI string or literal value for the object")
    graph: str | None = Field(default=None, description="Optional URI string for the named graph")


@mcp.tool()
def add_triples(triples: list[TripleModel]) -> str:
    """Add multiple RDF triples to the store in a single transaction."""
    try:
        quads = []
        for i, triple in enumerate(triples):
            try:
                # Validate and create nodes using helper functions
                validate_uri(triple.subject, f"Triple {i + 1}: Subject")
                validate_uri(triple.predicate, f"Triple {i + 1}: Predicate")

                subject_node = NamedNode(triple.subject)
                predicate_node = NamedNode(triple.predicate)
                object_node = create_rdf_node(triple.object)

                # Create graph node if specified
                graph_node = None
                if triple.graph:
                    validate_uri(triple.graph, f"Triple {i + 1}: Graph")
                    graph_node = NamedNode(triple.graph)

                # Create quad
                quad = Quad(subject_node, predicate_node, object_node, graph_node)
                quads.append(quad)

            except ToolError:
                # Re-raise ToolErrors with context preserved
                raise
            except ValueError as e:
                raise ToolError(f"Triple {i + 1}: Invalid URI format - {e}") from e
            except Exception as e:
                raise ToolError(f"Triple {i + 1}: Failed to create RDF quad - {e}") from e

        # Add all quads in a single transaction
        try:
            store.extend(quads)
        except Exception as e:
            raise ToolError(f"Failed to store triples in RDF database: {e}") from e

        # Build success message
        graph_counts = {}
        for quad in quads:
            if quad.graph_name is None or isinstance(quad.graph_name, DefaultGraph):
                graph_name = "default graph"
            else:
                graph_name = quad.graph_name.value
            graph_counts[graph_name] = graph_counts.get(graph_name, 0) + 1

        graph_summary = ", ".join(f"{count} to {graph}" for graph, count in graph_counts.items())
        return f"Successfully added {len(quads)} triple(s): {graph_summary}"

    except ToolError:
        # Re-raise ToolErrors as-is
        raise
    except Exception as e:
        raise ToolError(f"Unexpected error while adding triples: {e}") from e


@mcp.tool()
def quads_for_pattern(
    subject: str | None = None, predicate: str | None = None, object: str | None = None, graph: str | None = None
) -> str:
    """Find quads matching the given pattern. Use None for wildcards."""
    try:
        # Convert string parameters to RDF nodes or None for wildcards
        try:
            subject_node = NamedNode(subject) if subject else None
            predicate_node = NamedNode(predicate) if predicate else None
            object_node = create_rdf_node(object) if object else None
            graph_node = NamedNode(graph) if graph else None
        except ValueError as e:
            raise ToolError(f"Invalid URI format in pattern parameters: {e}") from e

        # Query the store for matching quads
        try:
            quads = list(store.quads_for_pattern(subject_node, predicate_node, object_node, graph_node))
        except Exception as e:
            raise ToolError(f"Failed to execute pattern query against RDF store: {e}") from e

        if not quads:
            return "No quads found matching the pattern."

        # Format results using helper function
        try:
            results = []
            for quad in quads:
                formatted = format_triple(quad.subject, quad.predicate, quad.object, quad.graph_name)
                results.append(formatted)

            return f"Found {len(quads)} quad(s):\n" + "\n".join(results)
        except Exception as e:
            raise ToolError(f"Failed to format query results: {e}") from e

    except ToolError:
        # Re-raise ToolErrors as-is
        raise
    except Exception as e:
        raise ToolError(f"Unexpected error while querying quads: {e}") from e


@mcp.tool()
def rdf_query(query: str) -> str:
    """Execute a read-only SPARQL query against the RDF store.

    Supports SELECT, ASK, CONSTRUCT, and DESCRIBE queries.
    Modification queries (INSERT, DELETE, DROP, CLEAR) are not allowed.
    """
    try:
        # Validate query is read-only using constant
        query_upper = query.upper()
        for keyword in FORBIDDEN_SPARQL_KEYWORDS:
            if keyword in query_upper:
                raise ToolError(f"Modification queries not allowed. '{keyword}' operations are forbidden.")

        # Execute the SPARQL query
        try:
            results = store.query(query)
        except ValueError as e:
            raise ToolError(f"Invalid SPARQL query syntax: {e}") from e
        except Exception as e:
            raise ToolError(f"Failed to execute SPARQL query against RDF store: {e}") from e

        # Format results based on query type using early returns
        try:
            from pyoxigraph import QueryBoolean, QuerySolutions

            # ASK query returns QueryBoolean
            if isinstance(results, QueryBoolean):
                return f"Query result: {results}"

            # SELECT query returns QuerySolutions
            if isinstance(results, QuerySolutions):
                return format_query_solutions(results)

            # CONSTRUCT/DESCRIBE query returns QueryTriples
            return format_query_triples(results)
        except Exception as e:
            raise ToolError(f"Failed to format SPARQL query results: {e}") from e

    except ToolError:
        # Re-raise ToolErrors as-is
        raise
    except Exception as e:
        raise ToolError(f"Unexpected error while executing SPARQL query: {e}") from e


if __name__ == "__main__":
    mcp.run()
