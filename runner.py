# -*- coding: utf-8 -*-
"""
runner.py —— 测试执行 + 报告解析模块
用 pytest 执行生成的脚本，再把报告丢给大模型总结缺陷和修复建议

用法：
  python runner.py          # 默认执行 scripts/ 下的生成脚本
"""
import subprocess
import os
import sys

import config
import prompts
import llm_client


def run_pytest(script_dir: str = None) -> str:
    """执行 pytest，返回输出文本"""
    if script_dir is None:
        script_dir = config.SCRIPTS_DIR
    # 统一转成绝对路径，避免 subprocess 的 cwd 与相对路径冲突
    script_dir = os.path.abspath(script_dir)
    os.makedirs(script_dir, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # 生成一个可被 import 的被测函数模块，供生成的测试脚本引用
    func_mod = os.path.join(script_dir, "target_func.py")
    with open(func_mod, "w", encoding="utf-8") as f:
        f.write('''def target_func(a, b):
    """示例被测函数：两数相加"""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("参数必须是数字")
    return a + b
''')

    result = subprocess.run(
        ["python", "-m", "pytest", script_dir, "-v", "--disable-warnings"],
        capture_output=True, text=True, cwd=script_dir,
    )
    output = result.stdout + "\n" + result.stderr
    with open(config.PYTEST_RESULT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    return output


def analyze_report(pytest_output: str) -> str:
    """把 pytest 输出丢给大模型，总结缺陷和修复建议"""
    user_prompt = prompts.report_analyze_prompt(pytest_output)
    return llm_client.ask("", user_prompt)


def main():
    print("🚀 开始执行测试...")
    output = run_pytest()
    print("📋 pytest 输出：")
    print(output)
    print("🧠 正在让大模型分析测试报告...")
    analysis = analyze_report(output)
    print("\n===== 智能测试报告分析 =====")
    print(analysis)


if __name__ == "__main__":
    main()
