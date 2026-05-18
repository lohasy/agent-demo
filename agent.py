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

    async def _stream_llm(self) -> tuple[str, list[dict] | None]:
        """调用 LLM 流式接口，返回 (文本内容, 工具调用列表)"""
        content_parts = []
        tc_map: dict[int, dict] = {}

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=TOOLS,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tc_map:
                        tc_map[idx] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    entry = tc_map[idx]
                    if tc.id:
                        entry["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            entry["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            entry["function"]["arguments"] += tc.function.arguments

        content = "".join(content_parts) if content_parts else ""
        tool_calls = list(tc_map.values()) if tc_map else None
        return content, tool_calls

    async def run(self, user_msg: str) -> str:
        self._init_messages(user_msg)

        for turn in range(MAX_TURNS):
            print(f"\n--- 第 {turn + 1} 轮思考 ---")

            content, tool_calls = await self._stream_llm()

            # LLM 决定调用工具
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args = json.loads(tc["function"]["arguments"])
                    print(f"[调用工具] {tool_name}({tool_args})")

                    tool = get_tool(tool_name)
                    if not tool:
                        result = f"错误: 没有名为 '{tool_name}' 的工具"
                    else:
                        mod = __import__(f"tools.{tool_name}",
                                         fromlist=["execute"])
                        result = mod.execute(**tool_args)

                    print(f"[工具返回] {result}")

                    self.messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc],
                    })
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                continue

            # LLM 决定直接回答 — 流式输出
            if content:
                print("[Agent 回答] ", end="", flush=True)
                for char in content:
                    print(char, end="", flush=True)
                print()
                return content

        print("\n[Agent 达到最大轮次限制，强制总结]")
        return await self._force_summarize()

    async def _force_summarize(self) -> str:
        self.messages.append({
            "role": "user",
            "content": "你已经达到了最大思考轮次，请根据上述所有工具返回的结果，给用户一个总结回答。"
        })
        content, _ = await self._stream_llm()
        if content:
            print("[Agent 总结] ", end="", flush=True)
            for char in content:
                print(char, end="", flush=True)
            print()
        return content
