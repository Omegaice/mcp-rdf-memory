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
def add_triples(triples: list[dict]) -> str:
    """Add multiple RDF triples to the store in a single transaction.
    
    Each triple should be a dictionary with keys:
    - subject: URI string (required)
    - predicate: URI string (required) 
    - object: URI string or literal value (required)
    - graph: URI string (optional)
    """
    try:
        if not triples:
            raise ToolError("No triples provided")
        
        quads = []
        for i, triple in enumerate(triples):
            # Validate triple structure
            if not isinstance(triple, dict):
                raise ToolError(f"Triple {i+1} must be a dictionary")
            
            required_keys = {"subject", "predicate", "object"}
            missing_keys = required_keys - set(triple.keys())
            if missing_keys:
                raise ToolError(f"Triple {i+1} missing required keys: {missing_keys}")
            
            subject = triple["subject"]
            predicate = triple["predicate"]
            object_value = triple["object"]
            graph = triple.get("graph")
            
            # Validate and create subject URI
            if not subject.startswith(("http://", "https://")):
                raise ToolError(f"Triple {i+1}: Subject must be a valid HTTP(S) URI")
            subject_node = NamedNode(subject)
            
            # Validate and create predicate URI
            if not predicate.startswith(("http://", "https://")):
                raise ToolError(f"Triple {i+1}: Predicate must be a valid HTTP(S) URI")
            predicate_node = NamedNode(predicate)
            
            # Create object node - check if it's a URI or literal
            object_node = NamedNode(object_value) if object_value.startswith(("http://", "https://")) else Literal(object_value)
            
            # Create graph node if specified
            graph_node = None
            if graph:
                if not graph.startswith(("http://", "https://")):
                    raise ToolError(f"Triple {i+1}: Graph must be a valid HTTP(S) URI")
                graph_node = NamedNode(graph)
            
            # Create quad
            quad = Quad(subject_node, predicate_node, object_node, graph_node)
            quads.append(quad)
        
        # Add all quads in a single transaction
        store.extend(quads)
        
        # Build success message
        graph_counts = {}
        for quad in quads:
            # Handle both named graphs and default graph
            graph_name = quad.graph_name.value if hasattr(quad.graph_name, 'value') else "default graph"
            graph_counts[graph_name] = graph_counts.get(graph_name, 0) + 1
        
        graph_summary = ", ".join(f"{count} to {graph}" for graph, count in graph_counts.items())
        return f"Successfully added {len(quads)} triple(s): {graph_summary}"
        
    except ValueError as e:
        raise ToolError(f"Invalid URI format: {e}") from e
    except Exception as e:
        raise ToolError(f"Failed to add triples: {e}") from e


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


@mcp.tool()
def rdf_query(query: str) -> str:
    """Execute a read-only SPARQL query against the RDF store.
    
    Supports SELECT, ASK, CONSTRUCT, and DESCRIBE queries.
    Modification queries (INSERT, DELETE, DROP, CLEAR) are not allowed.
    """
    try:
        # Validate query is read-only
        query_upper = query.upper()
        forbidden_keywords = ["INSERT", "DELETE", "DROP", "CLEAR", "CREATE", "LOAD", "COPY", "MOVE", "ADD"]
        
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                raise ToolError(f"Modification queries not allowed. '{keyword}' operations are forbidden.")
        
        # Execute the SPARQL query
        results = store.query(query)
        
        # Format results based on query type - use runtime type checks
        # Import types for isinstance checks
        from pyoxigraph import QueryBoolean, QuerySolutions, QueryTriples
        
        if isinstance(results, QueryBoolean):
            # ASK query returns QueryBoolean (not iterable)
            return f"Query result: {results}"
        elif isinstance(results, QuerySolutions):
            # SELECT query returns QuerySolutions (iterable)
            bindings = list(results)
            
            if not bindings:
                return "Query returned no results."
            
            # Format SELECT results as table-like output
            formatted_results = []
            for i, binding in enumerate(bindings):
                binding_strs = []
                # Use string representation and parse manually for now
                binding_str = str(binding)
                # Extract variable=value pairs from string representation
                if "=" in binding_str:
                    # Parse format like "?name=literal"
                    pairs = binding_str.strip("{}").split(", ")
                    for pair in pairs:
                        if "=" in pair:
                            var, val = pair.split("=", 1)
                            binding_strs.append(f"{var}: {val}")
                        else:
                            binding_strs.append(pair)
                else:
                    # Fallback to string representation
                    binding_strs.append(binding_str)
                
                formatted_results.append(f"Result {i+1}: " + ", ".join(binding_strs))
            
            return f"Query returned {len(bindings)} result(s):\n" + "\n".join(formatted_results)
        
        else:
            # CONSTRUCT/DESCRIBE query returns QueryTriples (iterable)
            assert isinstance(results, QueryTriples), f"Expected QueryTriples, got {type(results)}"
            triples = list(results)
            
            if not triples:
                return "Query returned no triples."
            
            # Format triples for output
            formatted_triples = []
            for triple in triples:
                subject_str = f"<{triple.subject.value}>"
                predicate_str = f"<{triple.predicate.value}>"
                
                # Format object based on type
                if hasattr(triple.object, 'value'):
                    object_str = f"<{triple.object.value}>" if str(triple.object).startswith('<') else f'"{triple.object.value}"'
                else:
                    object_str = str(triple.object)
                
                formatted_triples.append(f"{subject_str} {predicate_str} {object_str} .")
            
            return f"Query returned {len(triples)} triple(s):\n" + "\n".join(formatted_triples)
            
    except ValueError as e:
        raise ToolError(f"Invalid SPARQL query syntax: {e}") from e
    except Exception as e:
        raise ToolError(f"Failed to execute SPARQL query: {e}") from e


if __name__ == "__main__":
    mcp.run()