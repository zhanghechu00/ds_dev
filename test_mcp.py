import asyncio
import os
import sys
from mcp_client import MCPClient

async def main():
    mcp_server_path = os.path.abspath("mcp_server_shihua.py")
    print(f"Testing MCP server at: {mcp_server_path}")
    print(f"Using python: {sys.executable}")
    
    try:
        async with MCPClient(sys.executable, [mcp_server_path]) as client:
            print("Connected to server.")
            # Try to list tools if possible, or just call a simple one
            # But MCPClient only has call_tool.
            # Let's try to call a non-existent tool to see if it responds, or a simple one.
            # There is no simple 'ping' tool.
            # Let's try 'run_MIP' with a bad path, it should return an error string quickly.
            print("Calling run_MIP...")
            result = await client.call_tool("run_MIP", {"query": "C:\\nonexistent"})
            print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
