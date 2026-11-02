# -*- coding: utf-8 -*-
"""
testcase_gen.py —— 测试用例生成模块
输入需求 -> 大模型生成结构化用例 -> 清洗为Python对象 -> 导出Excel

用法：
  python testcase_gen.py "登录功能：用户输入用户名和密码登录系统"
"""
import json
import re
import os
import sys

import pandas as pd

import config
import prompts
import llm_client


def clean_json(raw: str) -> dict:
    """
    清洗大模型返回的文本，提取出 JSON。
    大模型偶尔会在 JSON 前后加 ``` 或解释文字，这里把它们剥掉。
    """
    raw = raw.strip()
    # 去掉 ```json ... ``` 包裹
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    # 找到第一个 { 到最后一个 }
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("大模型未返回有效JSON")
    json_str = raw[start:end + 1]
    return json.loads(json_str)


def generate_cases(requirement: str) -> list:
    """生成测试用例列表，返回 list[dict]"""
    user_prompt = prompts.testcase_gen_prompt(requirement)
    raw = llm_client.ask("", user_prompt)
    data = clean_json(raw)
    cases = data.get("cases", [])
    if not cases:
        raise ValueError("大模型返回的用例为空")
    return cases


def export_to_excel(cases: list, path: str = None) -> str:
    """把用例列表导出为 Excel，业务同事可直接使用"""
    if path is None:
        path = os.path.join(config.OUTPUT_DIR, "test_cases.xlsx")
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    rows = []
    for c in cases:
        rows.append({
            "用例ID": c.get("id", ""),
            "维度": c.get("dimension", ""),
            "用例标题": c.get("title", ""),
            "前置条件": c.get("precondition", ""),
            "操作步骤": "\n".join(c.get("steps", [])),
            "预期结果": c.get("expected", ""),
        })
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
    return path


def main():
    if len(sys.argv) < 2:
        print("用法：python testcase_gen.py '需求描述'")
        sys.exit(1)
    requirement = sys.argv[1]
    print(f"🧠 正在根据需求生成测试用例：{requirement}")
    cases = generate_cases(requirement)
    print(f"✅ 共生成 {len(cases)} 条用例")
    path = export_to_excel(cases)
    print(f"📄 已导出到：{path}")


if __name__ == "__main__":
    main()
