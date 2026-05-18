"""多智能体编排器 — 将复杂任务分解并委派给专业子 Agent"""

import asyncio
from agent import Agent
from worker_config import get_worker_config, WORKER_CONFIGS
from tools.delegate_worker import DELEGATE_WORKER_TOOL
from prompts import ORCHESTRATOR_SYSTEM_PROMPT


class DelegateToWorker:
    """委派工具的执行器 — 每次调用创建临时 worker Agent 并运行到底"""

    def __init__(self, llm_config: dict, parent_on_event=None):
        self.llm_config = llm_config
        self.parent_on_event = parent_on_event

    async def execute(self, **kwargs) -> str:
        worker_name = kwargs["worker_name"]
        task = kwargs["task"]

        config = get_worker_config(worker_name)
        if not config:
            available = ", ".join(WORKER_CONFIGS.keys())
            return f"错误: 未知的工作者 '{worker_name}'，可选: {available}"

        await self._emit_parent("worker_start", {
            "worker": worker_name, "task": task,
        })

        try:
            worker = Agent(
                base_url=self.llm_config["base_url"],
                model=self.llm_config["model"],
                api_key=self.llm_config["api_key"],
                system_prompt=config.system_prompt,
                allowed_tools=config.tools,
                on_event=self._wrap_events(worker_name),
                confirm_callback=self._worker_auto_confirm,
            )

            result = await worker.run(task)

            await self._emit_parent("worker_end", {
                "worker": worker_name, "result": result,
            })
            return result

        except Exception as e:
            await self._emit_parent("worker_error", {
                "worker": worker_name, "error": str(e),
            })
            return f"[{worker_name}] 执行出错: {e}"

    def _wrap_events(self, worker_name: str):
        """将 worker 内部事件包裹进 worker_event 信封"""
        async def handler(event_type: str, data: dict):
            await self._emit_parent("worker_event", {
                "worker": worker_name,
                "type": event_type,
                "data": data,
            })
        return handler

    async def _emit_parent(self, event_type: str, data: dict):
        if self.parent_on_event:
            result = self.parent_on_event(event_type, data)
            if asyncio.iscoroutine(result):
                await result

    @staticmethod
    async def _worker_auto_confirm(tasks) -> bool:
        # Worker 内触发 confirm 的工具自动批准
        return True


def create_orchestrator(base_url: str, model: str, api_key: str,
                        on_event=None, confirm_callback=None) -> Agent:
    delegate = DelegateToWorker(
        llm_config={"base_url": base_url, "model": model, "api_key": api_key},
        parent_on_event=on_event,
    )

    return Agent(
        base_url=base_url,
        model=model,
        api_key=api_key,
        on_event=on_event,
        confirm_callback=confirm_callback,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        extra_tools=[DELEGATE_WORKER_TOOL],
        tool_executors={"delegate_to_worker": delegate.execute},
    )
