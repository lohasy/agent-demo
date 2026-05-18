import json
from openai import AsyncOpenAI
from prompts import SYSTEM_PROMPT
from tools import TOOLS, get_tool

MAX_TURNS = 5


class Agent:
    def __init__(self, base_url: str = "https://api.deepseek.com/v1",
                 model: str = "deepseek-chat", api_key: str = ""):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.messages: list[dict] = []

    def _init_messages(self, user_msg: str):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

    async def run(self, user_msg: str) -> str:
        self._init_messages(user_msg)

        for turn in range(MAX_TURNS):
            print(f"\n--- 第 {turn + 1} 轮思考 ---")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOLS,
            )

            msg = response.choices[0].message

            # LLM 决定直接回答
            if msg.content and not msg.tool_calls:
                print(f"[Agent 回答] {msg.content}")
                return msg.content

            # LLM 决定调用工具
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments)
                    print(f"[调用工具] {tool_name}({tool_args})")

                    tool = get_tool(tool_name)
                    if not tool:
                        result = f"错误: 没有名为 '{tool_name}' 的工具"
                    else:
                        mod = __import__(f"tools.{tool_name}",
                                         fromlist=["execute"])
                        result = mod.execute(**tool_args)

                    print(f"[工具返回] {result}")

                    # 把工具调用和结果追加到对话历史
                    self.messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc.model_dump() if hasattr(tc, "model_dump") else dict(tc)]
                    })
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

        print("\n[Agent 达到最大轮次限制，强制总结]")
        return await self._force_summarize()

    async def _force_summarize(self) -> str:
        self.messages.append({
            "role": "user",
            "content": "你已经达到了最大思考轮次，请根据上述所有工具返回的结果，给用户一个总结回答。"
        })
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
        )
        content = response.choices[0].message.content
        print(f"[Agent 总结] {content}")
        return content
