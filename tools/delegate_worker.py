"""delegate_to_worker 工具定义（仅 schema，执行逻辑在 orchestrator.py）"""

DELEGATE_WORKER_TOOL = {
    "type": "function",
    "function": {
        "name": "delegate_to_worker",
        "description": (
            "将子任务委派给指定的专业工作者执行。"
            "可用的工作者: "
            "analyst(数据分析与计算), "
            "researcher(知识库检索), "
            "hr_agent(员工/部门查询, 请假申请)。"
            "如果多个子任务互相独立，同时调用多个委托以提高效率。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "worker_name": {
                    "type": "string",
                    "enum": ["analyst", "researcher", "hr_agent"],
                    "description": "要委派的工作者名称",
                },
                "task": {
                    "type": "string",
                    "description": "具体任务描述，应包含所有上下文信息，使工作者能独立完成",
                },
            },
            "required": ["worker_name", "task"],
        },
    },
}
