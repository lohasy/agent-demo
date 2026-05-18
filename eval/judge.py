"""LLM-as-Judge: 用另一个 LLM 给 agent 回答打分"""

from openai import AsyncOpenAI

JUDGE_PROMPT = """你是一个评估专家，负责给 AI 助手的回答打分。

## 评估维度（每项 0-5 分）

1. **准确性**：回答的事实是否与检查要点一致
2. **完整性**：是否覆盖了所有检查要点
3. **引用质量**：是否标注了信息来源（知识库内容需要引用出处）
4. **诚实度**：是否承认不知道（而非编造），是否不做无根据的推测

## 评分标准
- 5分：完全满足
- 3分：部分满足，有明显遗漏
- 1分：几乎不满足
- 0分：完全错误或命中禁止项

## 输入
用户问题: {question}
检查要点: {check_points}
禁止项: {forbidden_items}

AI 助手的回答:
{answer}

## 输出格式
请严格按以下 JSON 格式输出，不要输出其他内容：
{{"accuracy": 5, "completeness": 4, "citation": 3, "honesty": 5, "summary": "一句话评价"}}
"""


class Judge:
    def __init__(self, base_url: str, model: str, api_key: str):
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    async def score(self, question: str, answer: str,
                    check_points: list[str],
                    forbidden_items: list[str]) -> dict:
        prompt = JUDGE_PROMPT.format(
            question=question,
            check_points="\n".join(f"  - {p}" for p in check_points),
            forbidden_items="\n".join(f"  - {p}" for p in forbidden_items) if forbidden_items else "无",
            answer=answer,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        import json
        raw = response.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"accuracy": 0, "completeness": 0, "citation": 0,
                    "honesty": 0, "summary": f"JSON解析失败: {raw[:100]}"}
