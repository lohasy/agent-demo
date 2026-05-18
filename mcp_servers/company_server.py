"""MCP Server 示例：公司数据查询（原始 JSON-RPC over stdio）

客户端启动此 server 作为子进程，通过 stdin/stdout 进行 JSON-RPC 通信。

协议：
  ← tools/list    → 返回工具列表 {tools: [{name, description, inputSchema}]}
  ← tools/call    → 执行工具 {name, arguments} → 返回 {content: [{type: "text", text: ...}]}
  初始化: initialize → {serverInfo, capabilities} → initialized
"""

import sys
import json

# 模拟公司数据库
EMPLOYEES = {
    "张三": {"dept": "技术部", "title": "高级工程师", "years": 5, "email": "zhangsan@company.com"},
    "李四": {"dept": "产品部", "title": "产品经理", "years": 3, "email": "lisi@company.com"},
}

DEPARTMENTS = {
    "技术部": {"head": "王总", "members": 25},
    "产品部": {"head": "马总", "members": 12},
    "人事部": {"head": "赵总", "members": 6},
}

TOOLS = [
    {
        "name": "lookup_employee",
        "description": "查询员工信息：姓名、部门、职位、入职年限、邮箱",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "员工姓名"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "lookup_department",
        "description": "查询部门信息：负责人、成员数量",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dept_name": {"type": "string", "description": "部门名称"},
            },
            "required": ["dept_name"],
        },
    },
]


def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "company-server", "version": "1.0"},
            "capabilities": {"tools": {}},
        }

    if method == "tools/list":
        return {"tools": TOOLS}

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})

        if name == "lookup_employee":
            emp = EMPLOYEES.get(args.get("name", ""))
            text = (
                f"员工: {args.get('name', '')}\n"
                f"  部门: {emp['dept']}\n"
                f"  职位: {emp['title']}\n"
                f"  入职年限: {emp['years']} 年\n"
                f"  邮箱: {emp['email']}"
            ) if emp else f"未找到员工 '{args.get('name', '')}'"
            return {"content": [{"type": "text", "text": text}]}

        if name == "lookup_department":
            dept = DEPARTMENTS.get(args.get("dept_name", ""))
            text = (
                f"部门: {args.get('dept_name', '')}\n"
                f"  负责人: {dept['head']}\n"
                f"  成员数: {dept['members']} 人"
            ) if dept else f"未找到部门 '{args.get('dept_name', '')}'"
            return {"content": [{"type": "text", "text": text}]}

        return {"content": [{"type": "text", "text": f"未知工具: {name}"}]}

    return {"error": {"code": -32601, "message": f"未知方法: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        if "id" not in req:
            continue  # notification, no response
        resp = handle_request(req)
        result = {
            "jsonrpc": "2.0",
            "id": req["id"],
            "result": resp,
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
