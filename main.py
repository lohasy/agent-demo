import asyncio
import os
from agent import Agent
from rag_service import index_documents


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


async def main():
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    if not api_key:
        print("错误: 请设置环境变量 DEEPSEEK_API_KEY")
        return

    print(f"LLM: {base_url} | 模型: {model}")
    print("正在索引知识库文档...")
    index_documents()
    print("输入 'quit' 退出\n")

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
