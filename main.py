import asyncio
import os
from agent import Agent


async def main():
    # 通过环境变量配置 LLM 连接，默认连本地 Ollama
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    api_key = os.getenv("DEEPSEEK_API_KEY", "sk-b129d5d0e73c4345be4bfd4388f358b9")

    if not api_key:
        print("错误: 请设置环境变量 DEEPSEEK_API_KEY")
        return

    print(f"LLM: {base_url} | 模型: {model}")
    print("输入 'quit' 退出\n")

    agent = Agent(base_url=base_url, model=model, api_key=api_key)

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
