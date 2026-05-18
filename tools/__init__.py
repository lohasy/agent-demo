from .calculator import calculator_tool
from .filesystem import filesystem_tool

TOOLS = [calculator_tool, filesystem_tool]

def get_tool(name: str):
    for t in TOOLS:
        if t["function"]["name"] == name:
            return t
    return None
