# 从零构建 AI Agent — 完整教学指南

本教程带你从零开始，手把手构建一个企业内部智能助手 Agent，涵盖 7 个学习阶段。

## 项目总览

```
agent-demo/
├── agent.py              # Agent 核心引擎 — ReAct 循环
├── prompts.py            # System prompt
├── context.py            # Token 管理与上下文裁剪
├── main.py               # 命令行入口
├── server.py             # FastAPI 后端（SSE 流式）
├── rag_service.py        # RAG 知识检索服务
├── knowledge/            # 知识库文档目录
├── tools/                # 工具模块
│   ├── calculator.py     #   计算器
│   ├── filesystem.py     #   文件读写
│   ├── search_knowledge.py # 知识库搜索
│   ├── submit_leave.py   #   请假申请（需确认）
│   └── __init__.py       #   工具注册
├── eval/                 # 评估体系
│   ├── test_cases.json   #   测试用例
│   ├── runner.py         #   批量运行
│   └── judge.py          #   LLM-as-Judge 打分
├── frontend/             # Vue 3 聊天前端
│   └── src/
│       ├── App.vue
│       ├── api.js
│       └── components/
│           ├── ChatPanel.vue
│           ├── MessageBubble.vue
│           └── ToolCallCard.vue
└── requirements.txt
```

---

## 阶段 1：ReAct Agent 核心

### 什么是 ReAct

ReAct = Reasoning + Acting，是 LLM Agent 的核心工作模式：

```
用户输入 → LLM 思考 → 决定行动（调工具）→ 获取结果 → 再思考 → ... → 最终回答
```

### 核心代码：`agent.py`

```python
MAX_TURNS = 5  # 最多思考轮次，防止死循环

class Agent:
    def __init__(self, base_url, model, api_key):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model
        self.messages = []  # 完整对话历史

    async def run(self, user_msg: str) -> str:
        self._init_messages(user_msg)  # 初始化 [system, user]

        for turn in range(MAX_TURNS):
            content, tool_calls = await self._stream_llm()

            if tool_calls:
                # LLM 想调工具 → 执行 → 结果追加到对话 → 继续循环
                for tc in tool_calls:
                    result = execute_tool(tc)
                    self.messages.append(tool_result)
                continue

            if content:
                # LLM 觉得够了 → 返回答案
                return content

        # 达到上限 → 强制总结
        return await self._force_summarize()
```

### 工具定义（OpenAI function calling 格式）

```python
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",          # ← 文件名必须与此一致
        "description": "执行数学计算",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "required": ["expression"]
        }
    }
}

def execute(expression: str) -> str:   # 实际执行函数
    return str(eval(expression, safe_scope))
```

### 关键设计点

- **工具名 = 文件名**：`agent.py` 通过 `__import__(f"tools.{tool_name}")` 动态加载，名字必须一致
- **MAX_TURNS**：防止 LLM 在工具调用中无限循环
- **tool_call 历史**：每轮工具调用结果必须追加到 `self.messages`，LLM 才能"记住"
- **安全校验**：计算器限制可用字符集，文件工具限制工作目录范围

---

## 阶段 2：RAG 知识检索

### 原理

```
用户提问 "公司年假政策"
    │
    ▼
Embedding 向量化 → Chroma 向量库检索 → Top-3 相关文档片段
    │
    ▼
LLM 基于检索结果 + 原始问题 → 生成回答
```

### 核心代码：`rag_service.py`

```python
import chromadb
from chromadb.utils import embedding_functions

# 初始化（只需执行一次）
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-zh-v1.5"  # 中文 embedding 模型
)
client = chromadb.PersistentClient(path="./knowledge/.chromadb")
collection = client.get_or_create_collection(name="knowledge",
                                             embedding_function=ef)

# 索引文档
def index_documents():
    docs = load_and_chunk("./knowledge/*.txt")  # 按 \n\n 分段
    collection.upsert(ids, documents, metadatas)

# 检索
def search(query: str, top_k: int = 3) -> str:
    results = collection.query(query_texts=[query], n_results=top_k)
    return format_results(results)
```

### 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 向量库 | Chroma | 零配置，pip install 即用 |
| Embedding | BGE-small-zh-v1.5 | 中文最优，~100MB，CPU 可跑 |
| 分片策略 | 空行分段 | 简单有效，适合 FAQ/政策文档 |
| 检索数 | Top-3 | 控制上下文 token 消耗 |

---

## 阶段 3：流式输出

### 为什么需要流式

非流式：等 3-5 秒 → 整段文字突然出现（用户体验差）

流式：LLM 边想边往外蹦字 → 体验跟 ChatGPT 一样

### 实现方式

```python
async def _stream_llm(self) -> tuple[str, list | None]:
    stream = await self.client.chat.completions.create(
        model=self.model,
        messages=self.messages,
        tools=TOOLS,
        stream=True,  # ← 关键参数
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            content_parts.append(delta.content)  # 逐字收集
        if delta.tool_calls:
            merge_tool_call_chunks(delta.tool_calls)  # 合并碎片
```

输出时逐字打印：

```python
for char in content:
    print(char, end="", flush=True)  # flush=True 立即刷新缓冲区
```

### 流式下的工具调用处理

工具调用在流式模式中是分片到达的（`function.name` 可能跨多个 chunk），需要手动合并：

```python
if delta.tool_calls:
    for tc in delta.tool_calls:
        idx = tc.index
        if tc.function.name:
            tc_map[idx]["function"]["name"] += tc.function.name  # 拼起来
```

---

## 阶段 4：上下文管理

### 要解决的问题

- LLM 有 token 上限（DeepSeek: 128K），对话太长会超限报错
- 每轮对话 + 工具返回都在堆消息，需要清理

### 裁剪策略

```python
MAX_TOKENS = 100_000  # 留 28K 余量

def estimate_tokens(messages):
    # 粗略估算：中文 1 字 ≈ 1.5 token
    return sum(len(str(msg)) * 1.5 for msg in messages)

def trim(messages, max_tokens):
    # 保留 system prompt，裁剪最早的非 system 消息对
    system = [messages[0]]
    rest = messages[1:]
    while estimate_tokens(system + rest) > max_tokens:
        rest = rest[2:]  # 去掉最早的一对 (user + assistant)
    return system + rest
```

在 agent 每次追加消息后调用 `self.messages = trim(self.messages)`。

---

## 阶段 5：工具模式

### 并行执行

多个独立工具调用 → `asyncio.gather` 同时跑：

```python
results = await asyncio.gather(
    *[_exec(tc, name, args) for tc, name, args in tasks]
)
```

总耗时 ≈ max(单工具耗时)，而非 sum(所有工具耗时)。

### 用户确认

危险操作（提交审批、修改数据）执行前暂停：

```python
# 工具定义加 confirm 标记
submit_leave_tool = {
    "type": "function",
    "function": { "name": "submit_leave", ... },
    "confirm": True,  # ← 需要确认
}

# Agent 中检查
if tool.get("confirm"):
    if self.confirm_callback:
        approved = await self.confirm_callback(tasks)
    else:
        ok = input("确认执行? (y/n): ")
        approved = ok == "y"
```

CLI 模式用 `input()`，Web 模式用回调，评估模式自动返回 `True`。

---

## 阶段 6：评估体系

### 三层结构

```
测试用例(JSON) → Agent.run() → Judge LLM 打分 → 汇总报告
```

### 测试用例格式

```json
{
  "id": "annual_leave_basic",
  "question": "公司年假怎么算",
  "expect_tools": ["search_knowledge"],
  "check_points": ["入职满1年享有5天年假", "每增加1年增加1天", "上限15天"],
  "forbidden": ["编造", "不清楚"]
}
```

### LLM-as-Judge

```python
JUDGE_PROMPT = """评估以下 AI 回答：
检查要点: {check_points}
禁止项: {forbidden_items}
AI 回答: {answer}

输出 JSON: {"accuracy": 5, "completeness": 4, "citation": 3, "honesty": 5, "summary": "..."}
"""
```

四个评分维度：
- **准确性**：事实是否正确
- **完整性**：是否覆盖所有检查点
- **引用质量**：是否标注信息来源
- **诚实度**：不确定时是否承认（不编造）

---

## 阶段 7：Web 前后端

### 架构

```
浏览器 (Vue 3) ←→ FastAPI (SSE) ←→ Agent ←→ DeepSeek API
```

### 后端核心：SSE 流式传输

```python
@router.post("/api/chat")
async def chat(req: ChatRequest):
    agent = get_session_agent(req.session_id)
    queue = asyncio.Queue()

    # Agent 事件 → Queue → SSE
    agent.on_event = lambda t, d: queue.put({"type": t, "data": d})

    async def event_stream():
        asyncio.create_task(agent.run(req.message))
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["type"] in ("done", "error"):
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 前端核心：EventSource 读取

```javascript
const reader = response.body.getReader()
while (true) {
    const { done, value } = await reader.read()
    // 解析 SSE 格式：data: {...}\n\n
    const event = JSON.parse(line.slice(6))
    if (event.type === 'token') agentMsg.content += event.data.text
    if (event.type === 'tool_start') showToolCard(event.data)
    if (event.type === 'confirm_wait') showConfirmBar(event.data)
}
```

### 事件类型一览

| 事件 | 触发时机 | 前端展示 |
|------|---------|---------|
| `token` | LLM 输出一个字符 | 逐字追加到气泡 |
| `tool_start` | 开始调工具 | 显示工具卡片 |
| `tool_result` | 工具返回结果 | 更新卡片状态 |
| `confirm_required` | 需要确认 | 弹出确认栏 |
| `confirm_wait` | 等待用户确认 | 黄色确认条 |
| `turn` | 新一轮思考 | （CLI 用） |
| `done` | 回答结束 | 停止流式动画 |

---

## 运行指南

### 环境准备

```bash
pip install openai chromadb sentence-transformers fastapi uvicorn
cd frontend && npm install
```

### 命令行模式

```bash
$env:DEEPSEEK_API_KEY = "your-key"
python main.py
```

### Web 模式

```bash
# 终端 1：后端
python server.py

# 终端 2：前端
cd frontend && npm run dev
```

浏览器打开 `http://localhost:5173`。

### 评估模式

```bash
python eval/runner.py
```

---

## 学习路线回顾

| 阶段 | 文件 | 核心概念 |
|------|------|---------|
| 1 | `agent.py` | ReAct 循环、function calling |
| 2 | `rag_service.py` | 向量检索、文档分片、ChromaDB |
| 3 | `agent.py` (修改) | OpenAI stream API、chunk 合并 |
| 4 | `context.py` | token 估算、上下文裁剪 |
| 5 | `agent.py` + `tools/leave.py` | asyncio.gather、确认模式 |
| 6 | `eval/` | LLM-as-Judge、测试用例设计 |
| 7 | `server.py` + `frontend/` | SSE、Vue 3、会话管理 |

## 关键设计原则

1. **工具名 = 文件名 = function.name**，三者必须一致
2. **每次回答后重置消息**，避免跨会话污染（CLI），Web 模式可按 session 保持
3. **MAX_TURNS** 是安全阀，防止 LLM 陷入无限工具调用循环
4. **所有输出走事件回调**，CLI 和 Web 只是不同的渲染器
5. **不需要 agent 框架**，ReAct 核心就是一个 while 循环，300 行足够
