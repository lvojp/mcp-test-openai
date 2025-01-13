"""
Filesystem Server Implementation
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
from mcp import ServerSession, JSONRPCRequest, JSONRPCResponse
from watchfiles import awatch

from .exceptions import AccessError, InvalidPathError, PathNotFoundError

class FilesystemServer(ServerSession):
    """
    MCP Filesystem Server implementation that provides file system operations
    """
    
    def __init__(self, root_dir: str = ".", watch: bool = False):
        """
        Initialize the filesystem server.
        
        Args:
            root_dir (str): Root directory for file operations
            watch (bool): Whether to watch for filesystem changes
        """
        super().__init__()
        self.root_dir = Path(root_dir).resolve()
        self.watch = watch
        self._watch_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the server and filesystem watcher if enabled"""
        if self.watch:
            self._watch_task = asyncio.create_task(self._watch_filesystem())

    async def stop(self):
        """Stop the server and filesystem watcher"""
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

    def _validate_path(self, path: str) -> Path:
        """
        Validate and resolve a path relative to root_dir.
        
        Args:
            path (str): Path to validate
            
        Returns:
            Path: Resolved path object
            
        Raises:
            InvalidPathError: If path is invalid or outside root_dir
            AccessError: If path is not accessible
        """
        try:
            full_path = (self.root_dir / path).resolve()
            if not str(full_path).startswith(str(self.root_dir)):
                raise InvalidPathError("Path outside root directory")
            return full_path
        except Exception as e:
            raise InvalidPathError(f"Invalid path: {str(e)}")

    async def _watch_filesystem(self):
        """Watch for filesystem changes and broadcast notifications"""
        async for changes in awatch(self.root_dir):
            # Convert changes to notification messages and broadcast
            for change_type, path in changes:
                rel_path = str(Path(path).relative_to(self.root_dir))
                await self.notify("filesystem/change", {
                    "type": "filesystem_change",
                    "change_type": change_type,
                    "path": rel_path
                })

    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LIST command"""
        path = params.get("path", ".")
        try:
            full_path = self._validate_path(path)
            if not full_path.exists():
                raise PathNotFoundError(f"Path not found: {path}")
            
            entries = []
            for entry in full_path.iterdir():
                rel_path = entry.relative_to(self.root_dir)
                entries.append({
                    "name": entry.name,
                    "path": str(rel_path),
                    "type": "directory" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else None
                })
            
            return {"entries": entries}
        except Exception as e:
            raise ValueError(str(e))

    async def _handle_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle READ command"""
        path = params.get("path")
        if not path:
            raise ValueError("Path is required")
        
        try:
            full_path = self._validate_path(path)
            if not full_path.exists():
                raise PathNotFoundError(f"Path not found: {path}")
            if not full_path.is_file():
                raise InvalidPathError(f"Not a file: {path}")
            
            async with aiofiles.open(full_path, mode='rb') as f:
                content = await f.read()
            
            return {
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            raise ValueError(str(e))

    async def _handle_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WRITE command"""
        path = params.get("path")
        content = params.get("content")
        if not path:
            raise ValueError("Path is required")
        if content is None:
            raise ValueError("Content is required")
        
        try:
            full_path = self._validate_path(path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, mode='wb') as f:
                if isinstance(content, str):
                    await f.write(content.encode())
                else:
                    await f.write(content)
            
            return {}
        except Exception as e:
            raise ValueError(str(e))

    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle incoming JSON-RPC requests"""
        handlers = {
            "filesystem/list": self._handle_list,
            "filesystem/read": self._handle_read,
            "filesystem/write": self._handle_write,
        }
        
        method = request.method
        handler = handlers.get(method)
        if not handler:
            raise ValueError(f"Unknown method: {method}")
        
        result = await handler(request.params or {})
        return JSONRPCResponse(id=request.id, result=result)