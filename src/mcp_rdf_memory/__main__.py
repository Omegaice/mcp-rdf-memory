import os

from fastmcp import FastMCP

from mcp_rdf_memory.server import RDFMemoryServer, register_mcp_server


def main() -> None:
    # Read environment variable for persistent storage
    store_path = os.environ.get("RDF_STORE_PATH", "./.memory/")

    # Create server instance
    server = RDFMemoryServer(store_path=store_path)

    # Create FastMCP instance
    mcp = FastMCP("RDF Memory")

    # Register server methods with FastMCP
    register_mcp_server(server, mcp)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
