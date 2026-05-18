from rag_service import search

knowledge_tool = {
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "搜索公司内部知识库，获取政策、流程、规定等信息。当用户询问公司制度、政策、福利、流程等问题时使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或问题，如'年假政策'、'报销流程'等"
                }
            },
            "required": ["query"]
        }
    }
}


def execute(query: str) -> str:
    return search(query)
