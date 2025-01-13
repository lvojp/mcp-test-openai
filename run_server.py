"""
Example of running the MCP filesystem server
"""

import asyncio
import os
from mcp import stdio_server
from mcp_filesystem import FilesystemServer

async def main():
    # プロジェクトのルートディレクトリを使用
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    server = FilesystemServer(root_dir=root_dir, watch=True)
    print(f"Starting filesystem server with root directory: {root_dir}")
    
    await stdio_server(server)

if __name__ == "__main__":
    asyncio.run(main())