MAX_TOKENS = 100_000  # DeepSeek 128K, 留余量


def estimate_tokens(messages: list[dict]) -> int:
    """粗略估算 token 数，中文 1 字 ≈ 1.5 token"""
    total = 0
    for msg in messages:
        content = msg.get("content")
        if content:
            total += len(content) * 1.5
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                total += len(str(tc)) * 1.5
    return int(total)


def trim(messages: list[dict], max_tokens: int = MAX_TOKENS,
         on_event=None) -> list[dict]:
    """超出上限时裁剪最早的非 system 消息对"""
    if len(messages) <= 1:
        return messages

    system = [messages[0]]
    rest = list(messages[1:])

    trimmed = 0
    while estimate_tokens(system + rest) > max_tokens and len(rest) >= 2:
        rest = rest[2:]
        trimmed += 2

    if trimmed:
        if on_event:
            on_event("context_trimmed", {"count": trimmed})
        else:
            print(f"[上下文] 裁剪了最早的 {trimmed} 条消息 (token 超限)")

    return system + rest
