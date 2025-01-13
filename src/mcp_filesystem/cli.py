"""
Command line interface for the MCP filesystem server
"""

import asyncio
import argparse
import os
from pathlib import Path

from .server import FilesystemServer

async def main(root_dir: str = ".", watch: bool = False):
    """
    Main entry point for the filesystem server
    
    Args:
        root_dir (str): Root directory for file operations
        watch (bool): Whether to watch for filesystem changes
    """
    server = FilesystemServer(root_dir=root_dir, watch=watch)
    await server.start()
    try:
        await server.run()
    finally:
        await server.stop()

def cli():
    """Command line interface entry point"""
    parser = argparse.ArgumentParser(description="MCP Filesystem Server")
    parser.add_argument(
        "--root-dir",
        default=".",
        help="Root directory for file operations (default: current directory)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for filesystem changes"
    )
    
    args = parser.parse_args()
    root_dir = os.path.abspath(args.root_dir)
    
    asyncio.run(main(root_dir=root_dir, watch=args.watch))

if __name__ == "__main__":
    cli()