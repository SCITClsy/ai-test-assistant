# -*- coding: utf-8 -*-
"""
api_test.py —— 接口测试模块（真实系统测试）

这是「测真实系统」的核心：输入一个真实接口的地址和描述，
自动生成接口测试用例 → 自动生成真正调用该接口的 pytest 脚本 → 执行并智能分析。

区别于业务用例模块：这里生成的脚本会真的用 requests 去请求真实接口，
而不是调用一个假函数。

用法：
  python api_test.py "登录接口：POST https://api.example.com/login，传用户名和密码，成功返回200和token"
"""
import json
import os
import re
import subprocess
import sys

import config
import prompts
import llm_client
from testcase_gen import clean_json


# ========== 1. 生成接口测试用例 ==========
def generate_api_cases(api_desc: str) -> list:
    """根据接口描述，让大模型生成结构化接口用例"""
    user_prompt = prompts.api_case_gen_prompt(api_desc)
    raw = llm_client.ask("", user_prompt)
    data = clean_json(raw)
    cases = data.get("cases", [])
    if not cases:
        raise ValueError("大模型返回的接口用例为空")
    return cases


# ========== 2. 生成真正调用接口的 pytest 脚本 ==========
def generate_api_script(cases: list, path: str = None) -> str:
    """
    把接口用例转成真正调用真实接口的 pytest 脚本。
    脚本里内置一个 api_request() 函数，它用 requests 发真实请求；
    每条用例对应一个 test 函数，对真实响应做断言。
    """
    if path is None:
        path = os.path.join(config.API_SCRIPT_DIR, "test_api.py")
    os.makedirs(config.API_SCRIPT_DIR, exist_ok=True)

    lines = [
        '# -*- coding: utf-8 -*-',
        '# 本文件由 AI 测试助手自动生成：对真实接口发起请求并断言',
        'import requests',
        'import pytest',
        '',
        'BASE_URL = %r' % config.API_TEST_URL,
        'METHOD = %r' % config.API_TEST_METHOD.upper(),
        'TIMEOUT = %d' % config.API_TIMEOUT,
        '',
        '',
        'def api_request(params=None, headers=None, json_body=None):',
        '    """真正向被测接口发一次请求，返回 requests.Response"""',
        '    url = BASE_URL',
        '    hdrs = {"Content-Type": "application/json"}',
        '    if headers:',
        '        hdrs.update(headers)',
        '    if METHOD == "POST":',
        '        return requests.post(url, headers=hdrs, params=params, json=json_body, timeout=TIMEOUT)',
        '    elif METHOD == "PUT":',
        '        return requests.put(url, headers=hdrs, params=params, json=json_body, timeout=TIMEOUT)',
        '    elif METHOD == "DELETE":',
        '        return requests.delete(url, headers=hdrs, params=params, timeout=TIMEOUT)',
        '    else:',
        '        return requests.get(url, headers=hdrs, params=params, timeout=TIMEOUT)',
        '',
        '',
    ]

    # 每条用例生成一个 test 函数
    for i, c in enumerate(cases, start=1):
        case_id = c.get("id") or f"API-{i:03d}"
        title = c.get("title") or f"用例{i}"
        params = c.get("params") or {}
        headers = c.get("headers") or {}
        exp_status = c.get("expected_status") or 200
        exp_field = c.get("expected_field") or ""
        note = c.get("note") or title

        func_name = "test_" + re.sub(r"\W+", "_", str(case_id).lower())
        lines.append(f'def {func_name}():')
        lines.append(f'    """{note}"""')
        lines.append(f'    resp = api_request(params={json.dumps(params, ensure_ascii=False)}, '
                     f'headers={json.dumps(headers, ensure_ascii=False)})')
        lines.append(f'    assert resp.status_code == {exp_status}, f"期望状态码{exp_status}，实际{{resp.status_code}}: {{resp.text}}"')
        if exp_field:
            # 去掉可能来自JSON的引号包裹，只取字段名本身
            exp_field = exp_field.strip().strip('"').strip("'")
            lines.append(f'    assert {json.dumps(exp_field, ensure_ascii=False)} in resp.text, "响应中应包含字段: {exp_field}"')
        lines.append('')
        lines.append('')

    script = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(script)
    return path


# ========== 3. 执行接口测试 ==========
def run_api_tests(script_dir: str = None) -> str:
    """执行生成的接口测试脚本，返回 pytest 输出"""
    if script_dir is None:
        script_dir = config.API_SCRIPT_DIR
    script_dir = os.path.abspath(script_dir)
    os.makedirs(script_dir, exist_ok=True)
    result = subprocess.run(
        ["python", "-m", "pytest", script_dir, "-v", "--disable-warnings"],
        capture_output=True, text=True, cwd=script_dir,
    )
    output = result.stdout + "\n" + result.stderr
    with open(config.API_RESULT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    return output


def analyze_api_report(pytest_output: str, api_desc: str) -> str:
    """让大模型分析接口测试报告"""
    user_prompt = prompts.api_report_analyze_prompt(pytest_output, api_desc)
    return llm_client.ask("", user_prompt)


def main():
    if len(sys.argv) < 2:
        print("用法：python api_test.py '接口描述'")
        sys.exit(1)
    api_desc = sys.argv[1]
    print(f"🧠 正在根据接口描述生成接口测试用例：{api_desc}")
    cases = generate_api_cases(api_desc)
    print(f"✅ 共生成 {len(cases)} 条接口用例")
    script_path = generate_api_script(cases)
    print(f"✅ 已生成真实接口测试脚本：{script_path}")
    print("🚀 开始执行接口测试...")
    output = run_api_tests()
    print("📋 pytest 输出：")
    print(output)
    print("🧠 正在让大模型分析接口测试报告...")
    analysis = analyze_api_report(output, api_desc)
    print("\n===== 接口测试智能分析 =====")
    print(analysis)


if __name__ == "__main__":
    main()
