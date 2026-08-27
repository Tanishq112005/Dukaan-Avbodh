# mcp/main.py
from mcp.server import mcp

# yeh imports zaroori hain — inhi se @mcp.tool() decorators run hoke
# tools ko mcp instance ke andar register karte hain
import mcp.product
import mcp.order
import mcp.user

if __name__ == "__main__":
    mcp.run()