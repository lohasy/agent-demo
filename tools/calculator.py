calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "执行数学计算，支持 +、-、*、/、**（幂）、sqrt 等运算",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '123 * 456' 或 'sqrt(144)'"
                }
            },
            "required": ["expression"]
        }
    }
}


def execute(expression: str) -> str:
    import math
    allowed = set("0123456789+-*/.() eEcCrRsSqQtTpPiI")
    if not all(c in allowed for c in expression):
        return f"错误: 表达式中包含不允许的字符"

    safe_dict = {
        "sqrt": math.sqrt,
        "pow": pow,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "sin": math.sin,
        "cos": math.cos,
        "log": math.log,
    }

    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"
