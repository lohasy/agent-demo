import asyncio
import json
from openai import AsyncOpenAI
from prompts import SYSTEM_PROMPT
from tools import TOOLS, get_tool
from context import trim

MAX_TURNS = 5


class Agent:
    def __init__(self, base_url: str = "https://api.deepseek.com/v1",
                 model: str = "deepseek-chat", api_key: str = "",
                 confirm_callback=None, on_event=None):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.messages: list[dict] = []
        self.confirm_callback = confirm_callback
        self.on_event = on_event or (lambda t, d: None)

    async def _emit(self, event_type: str, data: dict):
        result = self.on_event(event_type, data)
        if asyncio.iscoroutine(result):
            await result

    def _init_messages(self, user_msg: str):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]

    async def _stream_llm(self) -> tuple[str, list[dict] | None]:
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
            await self._emit("turn", {"n": turn + 1})

            content, tool_calls = await self._stream_llm()

            if tool_calls:
                tasks = []
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args = json.loads(tc["function"]["arguments"])
                    await self._emit("tool_start", {
                        "name": tool_name, "args": tool_args,
                    })
                    tasks.append((tc, tool_name, tool_args))

                needs_confirm = False
                for tc, tool_name, tool_args in tasks:
                    tool = get_tool(tool_name)
                    if tool and tool.get("confirm"):
                        needs_confirm = True
                        await self._emit("confirm_required", {
                            "name": tool_name, "args": tool_args,
                        })

                if needs_confirm:
                    if self.confirm_callback:
                        ok = await self.confirm_callback(tasks)
                        approved = ok is True or str(ok).strip().lower() in ("y", "yes")
                    else:
                        ok = input("确认执行? (y/n): ").strip().lower()
                        approved = ok in ("y", "yes")
                    if not approved:
                        result = "用户取消了操作"
                        await self._emit("tool_result", {
                            "name": tasks[0][1], "result": result,
                        })
                        for tc, _, _ in tasks:
                            self.messages.append({
                                "role": "assistant", "content": None,
                                "tool_calls": [tc],
                            })
                            self.messages.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": result,
                            })
                        self.messages = trim(self.messages, on_event=self.on_event)
                        continue

                async def _exec(tc, tool_name, tool_args):
                    tool = get_tool(tool_name)
                    if not tool:
                        result = f"错误: 没有名为 '{tool_name}' 的工具"
                    else:
                        mod = __import__(f"tools.{tool_name}",
                                         fromlist=["execute"])
                        result = mod.execute(**tool_args)
                    return tc, tool_name, tool_args, result

                results = await asyncio.gather(
                    *[_exec(tc, name, args) for tc, name, args in tasks]
                )

                for tc, tool_name, tool_args, result in results:
                    await self._emit("tool_result", {
                        "name": tool_name, "result": result,
                    })
                    self.messages.append({
                        "role": "assistant", "content": None,
                        "tool_calls": [tc],
                    })
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
                self.messages = trim(self.messages, on_event=self.on_event)
                continue

            if content:
                await self._emit("answer_start", {})
                for char in content:
                    await self._emit("token", {"text": char})
                await self._emit("answer_end", {})
                return content

        await self._emit("max_turns", {})
        return await self._force_summarize()

    async def _force_summarize(self) -> str:
        self.messages.append({
            "role": "user",
            "content": "你已经达到了最大思考轮次，请根据上述所有工具返回的结果，给用户一个总结回答。"
        })
        self.messages = trim(self.messages, on_event=self.on_event)
        content, _ = await self._stream_llm()
        if content:
            for char in content:
                await self._emit("token", {"text": char})
        return content
