"""评估运行器：批量运行测试用例，调用 Judge 打分，输出报告"""

import asyncio
import json
import os
import sys
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import Agent
from judge import Judge


async def auto_confirm(tasks) -> bool:
    """eval 模式自动确认所有需要确认的操作"""
    for _, tool_name, tool_args in tasks:
        print(f"  [自动确认] {tool_name}({tool_args})")
    return True


async def run_case(agent: Agent, case: dict) -> str:
    """运行单个测试用例，返回 agent 回答"""
    captured = StringIO()

    import builtins
    original_print = builtins.print

    def _capture(*args, **kwargs):
        file = kwargs.get("file", sys.stdout)
        if file is sys.stdout:
            kwargs["file"] = captured
        original_print(*args, **kwargs)

    builtins.print = _capture

    try:
        answer = await agent.run(case["question"])
    finally:
        builtins.print = original_print

    logs = captured.getvalue()
    tools_used = []
    for tool_name in ["search_knowledge", "calculator",
                       "filesystem", "submit_leave"]:
        if f"[调用工具] {tool_name}" in logs:
            tools_used.append(tool_name)

    print(f"  ✓ 回答完成 | 工具: {tools_used or '无'} | "
          f"长度: {len(answer or '')} 字")

    return answer or "(Agent未返回回答)"


async def main():
    api_key = os.getenv("DEEPSEEK_API_KEY", "sk-b129d5d0e73c4345be4bfd4388f358b9")
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL", "deepseek-chat")

    cases_path = Path(__file__).parent / "test_cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    print(f"加载了 {len(cases)} 个测试用例\n")

    agent = Agent(base_url=base_url, model=model, api_key=api_key,
                  confirm_callback=auto_confirm)
    judge = Judge(base_url=base_url, model=model, api_key=api_key)

    results = []
    total_scores = {"accuracy": 0, "completeness": 0, "citation": 0, "honesty": 0}

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']}")
        print(f"  问题: {case['question']}")

        answer = await run_case(agent, case)
        if answer:
            answer = answer[:2000]

        print(f"  评分中...")
        scores = await judge.score(
            question=case["question"],
            answer=answer,
            check_points=case["check_points"],
            forbidden_items=case.get("forbidden", []),
        )

        for k in total_scores:
            total_scores[k] += scores.get(k, 0)

        results.append({
            "id": case["id"],
            "question": case["question"],
            "answer": answer,
            "scores": scores,
        })
        print(f"  评分: {scores.get('summary', 'N/A')}")
        print(f"  分数: A{scores.get('accuracy')} C{scores.get('completeness')} "
              f"R{scores.get('citation')} H{scores.get('honesty')}")
        print()

    n = len(results)
    print("=" * 50)
    print("评估汇总报告")
    print("=" * 50)
    print(f"测试用例数: {n}")
    print(f"平均分:")
    print(f"  准确性:   {total_scores['accuracy'] / n:.1f}/5")
    print(f"  完整性:   {total_scores['completeness'] / n:.1f}/5")
    print(f"  引用质量: {total_scores['citation'] / n:.1f}/5")
    print(f"  诚实度:   {total_scores['honesty'] / n:.1f}/5")
    overall = sum(total_scores.values()) / (n * 4)
    print(f"  综合:     {overall:.1f}/5")
    print()

    report_path = Path(__file__).parent / "report.json"
    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"详细报告已保存到: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
