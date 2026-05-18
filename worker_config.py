"""Worker 配置：定义每种专业子 Agent 的角色、工具和 prompt"""

from dataclasses import dataclass


@dataclass
class WorkerConfig:
    name: str
    description: str        # 说明何时委派给此 worker
    system_prompt: str      # 覆盖默认 prompt
    tools: list[str]        # 可用工具名称列表


WORKER_CONFIGS: dict[str, WorkerConfig] = {
    "analyst": WorkerConfig(
        name="analyst",
        description="数据分析与计算，处理数学运算和文件读写",
        system_prompt="""你是一个数据分析师。你可以使用计算器和文件系统工具。

规则：
1. 用 calculator 做数学计算
2. 用 filesystem 读写文件
3. 不要编造数据和计算结果
4. 返回精确的数据，回答简洁，用中文""",
        tools=["calculator", "filesystem"],
    ),
    "researcher": WorkerConfig(
        name="researcher",
        description="知识库检索，查询公司政策、流程、制度",
        system_prompt="""你是一个知识检索研究员。你可以搜索公司内部知识库。

规则：
1. 用 search_knowledge 搜索相关知识
2. 基于检索结果回答，标注信息来源
3. 如果知识库找不到相关信息，如实告知
4. 不要编造公司政策
5. 回答简洁，用中文""",
        tools=["search_knowledge"],
    ),
    "hr_agent": WorkerConfig(
        name="hr_agent",
        description="人力资源操作，查询员工/部门信息，提交请假申请",
        system_prompt="""你是一个 HR 专员。你可以查询员工和部门信息，以及提交请假申请。

规则：
1. 用 MCP 工具查询员工或部门信息
2. 用 submit_leave 提交请假申请
3. 不要编造员工信息或部门数据
4. 回答简洁，用中文""",
        tools=[
            "mcp_company_lookup_employee",
            "mcp_company_lookup_department",
            "submit_leave",
        ],
    ),
}


def get_worker_config(name: str) -> WorkerConfig | None:
    return WORKER_CONFIGS.get(name)
