leave_tool = {
    "type": "function",
    "function": {
        "name": "submit_leave",
        "description": "提交请假申请。用户说出差旅、休假、请假等意图时使用。执行前会要求用户确认。",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "请假天数"
                },
                "reason": {
                    "type": "string",
                    "description": "请假原因，如'年假'、'病假'、'事假'等"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，格式 YYYY-MM-DD"
                }
            },
            "required": ["days", "reason"]
        }
    },
    "confirm": True,
}


def execute(days: int, reason: str, start_date: str = "待定") -> str:
    return (
        f"[模拟] 请假申请已提交\n"
        f"  天数: {days} 天\n"
        f"  原因: {reason}\n"
        f"  日期: {start_date}\n"
        f"  状态: 等待直属领导审批"
    )
