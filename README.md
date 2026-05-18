# Agent Demo — 从零构建 AI Agent

一个教学项目，手把手带你从 0 行代码构建企业级智能助手 Agent。涵盖 ReAct 循环、RAG 知识检索、流式输出、上下文管理、工具模式、评估体系和 Web 前后端。

## 快速体验

### 命令行模式

```bash
export DEEPSEEK_API_KEY="your-key"
pip install openai chromadb sentence-transformers
python main.py
```

### Web 模式

```bash
# 终端 1
pip install openai chromadb sentence-transformers fastapi uvicorn
python server.py

# 终端 2
cd frontend && npm install && npm run dev
```

浏览器打开 `http://localhost:5173`

### 评估模式

```bash
python eval/runner.py
```

## 项目结构

```
├── agent.py              # Agent 核心 — ReAct 循环
├── prompts.py            # System prompt
├── context.py            # Token 管理与裁剪
├── main.py               # 命令行入口
├── server.py             # FastAPI 后端 (SSE)
├── rag_service.py        # RAG 知识检索
├── knowledge/            # 知识库文档
├── tools/                # 工具模块
│   ├── calculator.py     #   计算器
│   ├── filesystem.py     #   文件读写
│   ├── search_knowledge.py # 知识库搜索
│   └── submit_leave.py   #   请假申请 (需确认)
├── eval/                 # 评估体系
│   ├── test_cases.json   #   测试用例
│   ├── runner.py         #   批量运行
│   └── judge.py          #   LLM-as-Judge
├── frontend/             # Vue 3 聊天前端
└── TUTORIAL.md           # 完整教学文档
```

## 学习阶段

| 阶段 | 主题 | 分支 |
|------|------|------|
| 1 | ReAct Agent 核心 + 工具调用 | `master` |
| 2 | RAG 知识检索 (Chroma + BGE) | `feature/rag` |
| 3 | 流式输出 (SSE) | `feature/streaming` |
| 4 | Token 管理与上下文裁剪 | `feature/context` |
| 5 | 并行工具 + 用户确认 | `feature/tool-patterns` |
| 6 | LLM-as-Judge 评估体系 | `feature/eval` |
| 7 | Vue 3 + FastAPI Web 前后端 | `feature/frontend` |

## 技术栈

| 层 | 技术 |
|---|------|
| Agent 框架 | 自研 (零框架依赖) |
| LLM | DeepSeek (兼容 OpenAI API) |
| 向量检索 | ChromaDB + BGE-small-zh-v1.5 |
| 后端 | FastAPI + SSE |
| 前端 | Vue 3 + Vite |
| 评估 | LLM-as-Judge |

## 文档

完整教学指南见 [TUTORIAL.md](TUTORIAL.md)

## License

MIT
