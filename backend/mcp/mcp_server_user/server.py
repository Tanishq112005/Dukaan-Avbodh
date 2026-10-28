# Compatibility forwarder to mcp.user.server
from mcp.user.server import mcp

__all__ = ["mcp"]

if __name__ == "__main__":
    mcp.run()
