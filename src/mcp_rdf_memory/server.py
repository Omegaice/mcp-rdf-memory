"""
MCP RDF Memory Server

Model Context Protocol server providing RDF triple store capabilities to LLMs through SPARQL.
"""

from fastmcp import FastMCP

mcp = FastMCP("RDF Memory")

@mcp.tool()
def hello_world(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}! Welcome to the RDF Memory server."

if __name__ == "__main__":
    mcp.run()