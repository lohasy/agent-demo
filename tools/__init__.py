"""统一工具注册中心 — 本地工具 + MCP 工具"""

import asyncio
from .calculator import calculator_tool, execute as _calc_exec
from .filesystem import filesystem_tool, execute as _fs_exec
from .search_knowledge import knowledge_tool, execute as _search_exec
from .submit_leave import leave_tool, execute as _leave_exec

# Registry: name -> (is_async, callable)
_tool_registry = {}
_mcp_tool_defs: list[dict] = []
_mcp_client = None


def _register(name: str, fn, is_async: bool = False):
    _tool_registry[name] = (is_async, fn)


# 本地工具注册
_register("calculator", _calc_exec)
_register("filesystem", _fs_exec)
_register("search_knowledge", _search_exec)
_register("submit_leave", _leave_exec)

LOCAL_TOOLS = [calculator_tool, filesystem_tool, knowledge_tool, leave_tool]


def set_mcp_client(client):
    global _mcp_client
    _mcp_client = client


async def refresh_mcp_tools():
    """重新获取 MCP 工具列表（连接后调用）"""
    global _mcp_tool_defs
    if not _mcp_client:
        return
    _mcp_tool_defs = await _mcp_client.list_tools()
    for t in _mcp_tool_defs:
        name = t["function"]["name"]
        _register(name, None, is_async=True)


def get_all_tools() -> list[dict]:
    return list(LOCAL_TOOLS) + list(_mcp_tool_defs)


def get_tools_by_names(names: list[str]) -> list[dict]:
    """根据名称列表过滤工具定义"""
    name_set = set(names)
    return [t for t in get_all_tools() if t["function"]["name"] in name_set]


def get_tool_definition(name: str):
    """根据名称获取工具定义（OpenAI 格式）"""
    for t in get_all_tools():
        if t["function"]["name"] == name:
            return t
    return None


async def execute(name: str, args: dict) -> str:
    """统一执行：本地工具同步调用，MCP 工具异步调用"""
    entry = _tool_registry.get(name)
    if not entry:
        return f"错误: 没有名为 '{name}' 的工具"

    is_async, fn = entry
    if is_async:
        return await _mcp_client.call_tool(name, args)
    else:
        return fn(**args)
