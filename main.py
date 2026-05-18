import argparse
import asyncio
import os
import sys
from agent import Agent
from rag_service import index_documents
from mcp_client import mcp_client
from tools import set_mcp_client, refresh_mcp_tools, get_all_tools
from orchestrator import create_orchestrator


def cli_event_handler(event_type: str, data: dict):
    """将 agent 事件转为 CLI 可读输出"""
    if event_type == "turn":
        print(f"\n--- 第 {data['n']} 轮思考 ---")
    elif event_type == "tool_start":
        print(f"[调用工具] {data['name']}({data['args']})")
    elif event_type == "confirm_required":
        print(f"⚠ 即将执行: {data['name']}({data['args']})")
    elif event_type == "tool_result":
        print(f"[工具返回] ({data['name']}) {data['result']}")
    elif event_type == "context_trimmed":
        print(f"[上下文] 裁剪了最早的 {data['count']} 条消息")
    elif event_type == "answer_start":
        print("[Agent 回答] ", end="", flush=True)
    elif event_type == "token":
        print(data["text"], end="", flush=True)
    elif event_type == "answer_end":
        print()
    elif event_type == "max_turns":
        print("\n[Agent 达到最大轮次限制，强制总结]")
    elif event_type == "worker_start":
        print(f"\n{'='*30} [工作者: {data['worker']}] {'='*30}")
        print(f"  任务: {data['task']}")
    elif event_type == "worker_event":
        _print_worker_event(data["worker"], data["type"], data["data"])
    elif event_type == "worker_end":
        print(f"\n{'='*30} [工作者: {data['worker']}] 完成 {'='*30}")
        result_preview = str(data.get("result", ""))[:200]
        if result_preview:
            print(f"  结果: {result_preview}")
    elif event_type == "worker_error":
        print(f"\n[工作者: {data['worker']}] 错误: {data['error']}")


def _print_worker_event(worker: str, event_type: str, data: dict):
    prefix = f"  [{worker}] "
    if event_type == "turn":
        print(f"{prefix}--- 第 {data['n']} 轮 ---")
    elif event_type == "tool_start":
        print(f"{prefix}调用: {data['name']}({data['args']})")
    elif event_type == "tool_result":
        result_str = str(data.get("result", ""))[:150]
        print(f"{prefix}返回: {result_str}")
    elif event_type == "token":
        print(data["text"], end="", flush=True)
    elif event_type == "context_trimmed":
        print(f"{prefix}[裁剪了 {data['count']} 条消息]")
    elif event_type == "max_turns":
        print(f"{prefix}[达到最大轮次，强制总结]")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["single", "orchestrator"],
                        default="single", help="Agent 运行模式")
    args, _ = parser.parse_known_args()

    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    if not api_key:
        print("错误: 请设置环境变量 DEEPSEEK_API_KEY")
        return

    print(f"LLM: {base_url} | 模型: {model}")
    print("正在索引知识库文档...")
    index_documents()

    # 连接 MCP Server
    from pathlib import Path
    server_script = str(Path(__file__).parent / "mcp_servers" / "company_server.py")
    await mcp_client.connect("company", sys.executable, [server_script])
    set_mcp_client(mcp_client)
    await refresh_mcp_tools()
    print(f"MCP 工具: {[t['function']['name'] for t in get_all_tools()]}")
    print("输入 'quit' 退出\n")

    if args.mode == "orchestrator":
        print("模式: 多智能体编排器\n")
        agent = create_orchestrator(base_url=base_url, model=model, api_key=api_key,
                                    on_event=cli_event_handler)
    else:
        agent = Agent(base_url=base_url, model=model, api_key=api_key,
                      on_event=cli_event_handler)

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("再见！")
            break

        print("-" * 40)
        await agent.run(user_input)
        print("-" * 40 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
