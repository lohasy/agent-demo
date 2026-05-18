from .calculator import calculator_tool
from .filesystem import filesystem_tool
from .search_knowledge import knowledge_tool
from .submit_leave import leave_tool

TOOLS = [calculator_tool, filesystem_tool, knowledge_tool, leave_tool]

def get_tool(name: str):
    for t in TOOLS:
        if t["function"]["name"] == name:
            return t
    return None
