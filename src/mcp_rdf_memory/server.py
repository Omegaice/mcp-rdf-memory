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


@mcp.tool()
def quads_for_pattern(
    subject: str | None = None, 
    predicate: str | None = None, 
    object: str | None = None, 
    graph: str | None = None
) -> str:
    """Find quads matching the given pattern. Use None (omit parameter) for wildcards."""
    try:
        # Convert string parameters to RDF nodes or None for wildcards
        subject_node = NamedNode(subject) if subject else None
        predicate_node = NamedNode(predicate) if predicate else None
        
        # Handle object - could be URI or literal
        object_node = None
        if object:
            object_node = NamedNode(object) if object.startswith(("http://", "https://")) else Literal(object)
        
        graph_node = NamedNode(graph) if graph else None
        
        # Query the store for matching quads
        quads = list(store.quads_for_pattern(subject_node, predicate_node, object_node, graph_node))
        
        if not quads:
            return "No quads found matching the pattern."
        
        # Format results
        results = []
        for quad in quads:
            # Assert correct types for IDE diagnostics
            assert isinstance(quad.subject, NamedNode), f"Expected NamedNode for subject, got {type(quad.subject)}"
            assert isinstance(quad.predicate, NamedNode), f"Expected NamedNode for predicate, got {type(quad.predicate)}"
            
            subject_str = f"<{quad.subject.value}>"
            predicate_str = f"<{quad.predicate.value}>"
            
            # Format object based on type
            if hasattr(quad.object, 'value'):
                # Object can be NamedNode or Literal, both have .value
                assert isinstance(quad.object, NamedNode | Literal), f"Expected NamedNode or Literal for object, got {type(quad.object)}"
                object_str = f"<{quad.object.value}>" if str(quad.object).startswith('<') else f'"{quad.object.value}"'
            else:
                object_str = str(quad.object)
            
            # Include graph if present
            if quad.graph_name and hasattr(quad.graph_name, 'value'):
                # Graph should be NamedNode when it has a value
                assert isinstance(quad.graph_name, NamedNode), f"Expected NamedNode for named graph, got {type(quad.graph_name)}"
                graph_str = f" GRAPH <{quad.graph_name.value}>"
                results.append(f"{subject_str} {predicate_str} {object_str}{graph_str}")
            else:
                results.append(f"{subject_str} {predicate_str} {object_str}")
        
        return f"Found {len(quads)} quad(s):\n" + "\n".join(results)
        
    except ValueError as e:
        raise ToolError(f"Invalid URI format: {e}") from e
    except Exception as e:
        raise ToolError(f"Failed to query quads: {e}") from e

if __name__ == "__main__":
    mcp.run()