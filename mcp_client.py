"""MCP 客户端：通过 subprocess + JSON-RPC 连接 MCP Server

协议说明：
- 启动 MCP Server 作为子进程（通过 stdio 通信）
- 使用 JSON-RPC 2.0 进行 tools/list 和 tools/call
- 初始化握手: initialize → initialized
"""

import asyncio
import json
import subprocess
import uuid


class MCPClient:
    def __init__(self):
        self._connections: dict[str, dict] = {}

    async def connect(self, name: str, command: str, args: list[str] = None):
        """启动 MCP Server 子进程，完成初始化握手"""
        proc = await asyncio.create_subprocess_exec(
            command, *(args or []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**__import__('os').environ, "PYTHONIOENCODING": "utf-8"},
        )

        # JSON-RPC 初始化握手
        await self._send(proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "agent-demo", "version": "1.0"},
        })
        init_resp = await self._recv(proc)
        server_info = init_resp.get("result", {})

        # JSON-RPC notification: 不带 id，server 不应回复
        await self._send(proc, "notifications/initialized", {}, is_notification=True)

        self._connections[name] = {
            "proc": proc,
            "server_info": server_info,
        }
        print(f"[MCP] 已连接 server: {name} "
              f"({server_info.get('serverInfo', {}).get('name', '?')})")

    async def list_tools(self) -> list[dict]:
        """获取工具列表，转为 OpenAI function calling 格式"""
        all_tools = []
        for name, conn in self._connections.items():
            resp = await self._send_recv(conn["proc"], "tools/list", {})
            for tool in resp.get("result", {}).get("tools", []):
                all_tools.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp_{name}_{tool['name']}",
                        "description": tool.get("description", ""),
                        "parameters": tool.get("inputSchema", {
                            "type": "object", "properties": {},
                        }),
                    },
                })
        return all_tools

    async def call_tool(self, full_name: str, args: dict) -> str:
        """调用 MCP 工具，格式: mcp_{server_name}_{tool_name}"""
        parts = full_name.split("_", 2)
        if len(parts) < 3:
            return f"错误: 无效的 MCP 工具名 '{full_name}'"
        server_name = parts[1]
        tool_name = parts[2]

        conn = self._connections.get(server_name)
        if not conn:
            return f"错误: MCP server '{server_name}' 未连接"

        resp = await self._send_recv(conn["proc"], "tools/call", {
            "name": tool_name,
            "arguments": args,
        })

        # 提取文本内容
        content = resp.get("result", {}).get("content", [])
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
        return "\n".join(texts) if texts else json.dumps(content)

    async def close(self):
        for name, conn in self._connections.items():
            conn["proc"].terminate()
            try:
                await asyncio.wait_for(conn["proc"].wait(), timeout=2)
            except asyncio.TimeoutError:
                conn["proc"].kill()
        self._connections.clear()

    # ── JSON-RPC helpers ──

    @staticmethod
    async def _send(proc, method: str, params: dict, is_notification: bool = False):
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        if not is_notification:
            msg["id"] = str(uuid.uuid4())[:8]
        proc.stdin.write((json.dumps(msg) + "\n").encode())
        await proc.stdin.drain()

    @staticmethod
    async def _recv(proc) -> dict:
        line = await proc.stdout.readline()
        return json.loads(line.decode())

    @staticmethod
    async def _send_recv(proc, method: str, params: dict) -> dict:
        await MCPClient._send(proc, method, params)
        return await MCPClient._recv(proc)


mcp_client = MCPClient()
