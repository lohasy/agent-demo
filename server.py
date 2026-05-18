"""FastAPI 后端：SSE 流式聊天 + 会话管理"""

import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import Agent
from rag_service import index_documents
from mcp_client import mcp_client
from tools import set_mcp_client, refresh_mcp_tools


sessions: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    index_documents()
    # 连接 MCP Server
    from pathlib import Path
    server_script = str(Path(__file__).parent / "mcp_servers" / "company_server.py")
    await mcp_client.connect("company", sys.executable, [server_script])
    set_mcp_client(mcp_client)
    await refresh_mcp_tools()
    yield
    await mcp_client.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ConfirmRequest(BaseModel):
    session_id: str
    approved: bool


def _get_or_create_session(session_id: str | None) -> tuple[str, dict]:
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    sid = session_id or str(uuid.uuid4())[:8]
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    queue: asyncio.Queue = asyncio.Queue()
    confirm_event: asyncio.Event = asyncio.Event()
    confirm_result: dict = {"approved": False}

    async def on_event(event_type: str, data: dict):
        await queue.put({"type": event_type, "data": data})

    async def on_confirm(tasks) -> bool:
        confirm_event.clear()
        await queue.put({"type": "confirm_wait", "data": {
            "tasks": [{"name": n, "args": a} for _, n, a in tasks],
        }})
        await confirm_event.wait()
        return confirm_result["approved"]

    agent = Agent(
        base_url=base_url, model=model, api_key=api_key,
        on_event=on_event, confirm_callback=on_confirm,
    )

    session = {
        "agent": agent, "queue": queue,
        "confirm_event": confirm_event, "confirm_result": confirm_result,
    }
    sessions[sid] = session
    return sid, session


@app.get("/api/session/new")
async def new_session():
    sid, _ = _get_or_create_session(None)
    return {"session_id": sid}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    sid, session = _get_or_create_session(req.session_id)
    agent: Agent = session["agent"]
    queue: asyncio.Queue = session["queue"]

    async def event_stream():
        yield f"data: {json.dumps({'type': 'session', 'data': {'session_id': sid}}, ensure_ascii=False)}\n\n"

        async def run_agent():
            await agent.run(req.message)
            await queue.put({"type": "done", "data": {}})

        task = asyncio.create_task(run_agent())

        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event["type"] in ("done", "error"):
                break

        await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/confirm")
async def confirm(req: ConfirmRequest):
    session = sessions.get(req.session_id)
    if not session:
        return {"ok": False, "error": "session not found"}

    session["confirm_result"]["approved"] = req.approved
    session["confirm_event"].set()
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
