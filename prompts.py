# -*- coding: utf-8 -*-
"""
prompts.py —— 提示词模板集中管理
方案B 的核心，面试重点讲：如何让大模型输出结构化、可用的测试用例。
"""
import config


def testcase_gen_prompt(requirement: str) -> str:
    """
    根据需求文档生成结构化测试用例。
    强制 JSON 输出，方便程序解析和导出 Excel。
    """
    dims = "、".join(config.COVERAGE_DIMENSIONS)
    return f"""你是一位资深软件测试工程师。请根据下面的【需求描述】，设计测试用例。

【需求描述】
{requirement}

请严格按照下面的 JSON 格式输出，不要输出任何其他文字、不要用代码块包裹：
{{
  "cases": [
    {{
      "id": "TC-001",
      "dimension": "正常场景",
      "title": "用例标题",
      "precondition": "前置条件（无则写\"无\"）",
      "steps": ["步骤1", "步骤2"],
      "expected": "预期结果"
    }}
  ]
}}

要求：
1. 覆盖以下维度：{dims}，每个维度至少 {config.CASES_PER_DIMENSION} 条。
2. 步骤要具体可执行，预期结果要可判定。
3. 只输出 JSON，禁止输出解释性文字。
"""


def script_gen_prompt(cases_json: str) -> str:
    """
    把结构化测试用例转成可运行的 pytest 代码。
    """
    return f"""你是一位 Python 测试开发工程师。请根据下面的【测试用例JSON】，生成一段可直接运行的 pytest 测试代码。

【测试用例JSON】
{cases_json}

要求：
1. 使用 pytest，函数名以 test_ 开头。
2. 每条用例对应一个 test 函数，用 pytest.raises 处理异常场景。
3. 用一个简单的被测函数 target_func() 作为待测对象（模拟被测试的业务函数），用例对它进行断言。
4. 只输出纯 Python 代码，禁止输出解释文字和代码块包裹。
"""


def report_analyze_prompt(pytest_output: str) -> str:
    """
    解析 pytest 执行结果，总结失败原因、归类缺陷、给出修复建议。
    """
    return f"""你是一位资深软件测试工程师。下面是一次 pytest 测试的执行输出，请分析并总结。

【pytest输出】
{pytest_output}

请输出：
1. 总用例数、通过数、失败数。
2. 失败用例的清单和失败原因归类（功能缺陷/边界遗漏/环境问题等）。
3. 每个失败项给出修复建议。
4. 用简洁的中文分条输出。
"""


def api_case_gen_prompt(api_desc: str) -> str:
    """
    根据接口描述生成接口测试用例。
    接口测试比业务用例更强调：请求方式、请求参数、期望状态码、响应字段。
    """
    return f"""你是一位资深接口测试工程师。请根据下面的【接口描述】，设计接口测试用例。

【接口描述】
{api_desc}

请严格按照下面的 JSON 格式输出，不要输出任何其他文字、不要用代码块包裹：
{{
  "cases": [
    {{
      "id": "API-001",
      "dimension": "正常场景",
      "title": "用例标题",
      "params": {{"参数名": "值"}},
      "headers": {{"Content-Type": "application/json"}},
      "expected_status": 200,
      "expected_field": "期望响应里应出现的字段名",
      "note": "这条用例在验证什么"
    }}
  ]
}}

要求：
1. 覆盖正常、边界、异常、鉴权/缺失参数四类场景，每个场景至少2条。
2. params/headers 必须是 JSON 对象，expected_status 是数字。
3. 只输出 JSON，禁止输出解释性文字。
"""


def api_report_analyze_prompt(pytest_output: str, api_desc: str) -> str:
    """
    针对接口测试报告做智能分析。
    """
    return f"""你是一位资深接口测试工程师。下面是一次接口自动化测试（pytest）的执行输出，以及被测接口描述。

【被测接口描述】
{api_desc}

【pytest输出】
{pytest_output}

请分析并输出：
1. 总用例数、通过数、失败数。
2. 失败用例清单及原因归类（接口bug/参数错误/环境问题/断言错误等）。
3. 每个失败项给出修复建议。
4. 用简洁的中文分条输出。
"""
