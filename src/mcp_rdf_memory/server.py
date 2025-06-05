"""
MCP RDF Memory Server

Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.
"""


from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pyoxigraph import Literal, NamedNode, Quad, Store

# Create in-memory RDF store
store = Store()

mcp = FastMCP("RDF Memory")

@mcp.tool()
def hello_world(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}! Welcome to the RDF Memory server."

@mcp.tool()
def add_triple(subject: str, predicate: str, object: str, graph: str | None = None) -> str:
    """Add an RDF triple to the store."""
    try:
        # Validate and create subject URI
        if not subject.startswith(("http://", "https://")):
            raise ToolError("Subject must be a valid HTTP(S) URI")
        subject_node = NamedNode(subject)
        
        # Validate and create predicate URI
        if not predicate.startswith(("http://", "https://")):
            raise ToolError("Predicate must be a valid HTTP(S) URI")
        predicate_node = NamedNode(predicate)
        
        # Create object node - check if it's a URI or literal
        object_node = NamedNode(object) if object.startswith(("http://", "https://")) else Literal(object)
        
        # Create graph node if specified
        graph_node = None
        if graph:
            if not graph.startswith(("http://", "https://")):
                raise ToolError("Graph must be a valid HTTP(S) URI")
            graph_node = NamedNode(graph)
        
        # Create and add quad to store
        quad = Quad(subject_node, predicate_node, object_node, graph_node)
        store.add(quad)
        
        return f"Successfully added triple: <{subject}> <{predicate}> {object!r} to {'graph <' + graph + '>' if graph else 'default graph'}"
        
    except ValueError as e:
        raise ToolError(f"Invalid URI format: {e}") from e
    except Exception as e:
        raise ToolError(f"Failed to add triple: {e}") from e

if __name__ == "__main__":
    mcp.run()