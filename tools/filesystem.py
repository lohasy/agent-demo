from pathlib import Path

WORK_DIR = Path("D:/agent-demo/workspace")

filesystem_tool = {
    "type": "function",
    "function": {
        "name": "filesystem",
        "description": "读写文件。action: 'read' 读取文件内容, 'write' 写入文件内容, 'list' 列出工作目录文件",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "list"],
                    "description": "操作类型"
                },
                "filename": {
                    "type": "string",
                    "description": "文件名（相对于工作目录）"
                },
                "content": {
                    "type": "string",
                    "description": "写入内容（仅 write 操作需要）"
                }
            },
            "required": ["action", "filename"]
        }
    }
}


def execute(action: str, filename: str, content: str = "") -> str:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    filepath = WORK_DIR / filename

    # 防止路径穿越
    try:
        filepath = filepath.resolve()
        WORK_DIR.resolve()
        if not str(filepath).startswith(str(WORK_DIR.resolve())):
            return "错误: 不允许访问工作目录之外的文件"
    except Exception:
        return "错误: 路径无效"

    if action == "read":
        if not filepath.exists():
            return f"错误: 文件 '{filename}' 不存在"
        return filepath.read_text(encoding="utf-8")

    elif action == "write":
        filepath.write_text(content, encoding="utf-8")
        return f"已写入 {len(content)} 个字符到 '{filename}'"

    elif action == "list":
        if not WORK_DIR.exists():
            return "工作目录为空"
        files = [f.name for f in WORK_DIR.iterdir()]
        return "工作目录文件: " + (", ".join(files) if files else "（空）")

    return f"错误: 未知操作 '{action}'"
