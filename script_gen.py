# -*- coding: utf-8 -*-
"""
script_gen.py —— pytest 脚本生成模块
把结构化用例转成可运行的 pytest 代码，保存到 scripts 目录

用法：
  python script_gen.py <用例JSON文件>
"""
import json
import os
import sys

import config
import prompts
import llm_client


def generate_script(cases: list, path: str = None) -> str:
    """把用例列表转成 pytest 代码并保存，返回文件路径"""
    if path is None:
        path = os.path.join(config.SCRIPTS_DIR, "test_generated.py")
    os.makedirs(config.SCRIPTS_DIR, exist_ok=True)

    cases_json = json.dumps({"cases": cases}, ensure_ascii=False, indent=2)
    user_prompt = prompts.script_gen_prompt(cases_json)
    code = llm_client.ask("", user_prompt)

    # 剥掉可能的代码块包裹
    import re
    fence = re.search(r"```(?:python)?\s*(.*?)\s*```", code, re.DOTALL)
    if fence:
        code = fence.group(1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return path


def main():
    if len(sys.argv) < 2:
        print("用法：python script_gen.py <用例JSON文件>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        cases = json.load(f).get("cases", [])
    print(f"🧠 正在根据 {len(cases)} 条用例生成 pytest 脚本...")
    path = generate_script(cases)
    print(f"✅ 已生成脚本：{path}")


if __name__ == "__main__":
    main()
