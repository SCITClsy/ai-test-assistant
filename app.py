# -*- coding: utf-8 -*-
"""
app.py —— AI 测试助手网页界面（Streamlit）

作用：
  给测试/业务同事用的可视化工具：输入需求 -> 生成测试用例(Excel) -> 生成pytest脚本 -> 执行测试 -> 智能报告分析。

启动方式：
  python -m streamlit run app.py
  浏览器自动打开 http://localhost:8501

功能（面试按这个讲）：
  1. 输入需求描述，自动生成结构化测试用例（正常/边界/异常/兼容四类维度）
  2. 一键导出 Excel，业务同事直接拿去用
  3. 把用例自动转成可运行的 pytest 脚本
  4. 自动执行测试，并把报告交给大模型总结缺陷和修复建议
  5. 附带"大模型安全评测"功能（对抗Prompt测试，贴合测试背景加分）
"""
import os
import tempfile

import streamlit as st

import config
import testcase_gen
import script_gen
import runner
import llm_eval
import api_test


st.set_page_config(page_title="🧪 AI 测试助手", page_icon="🧪", layout="wide")
st.title("🧪 AI 测试助手")
st.caption("输入需求 → 自动生成测试用例 → 生成自动化脚本 → 执行并智能分析报告")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📝 生成测试用例", "🐍 生成pytest脚本", "▶️ 执行测试&分析", "🔌 接口测试", "🛡️ 大模型安全评测"]
)

# ============ Tab1 生成测试用例 ============
with tab1:
    st.header("生成结构化测试用例")
    requirement = st.text_area(
        "粘贴需求描述",
        placeholder="例如：登录功能，用户输入正确的用户名和密码可登录，错误则提示失败...",
        height=150,
    )
    if st.button("🚀 生成测试用例", type="primary"):
        if not requirement.strip():
            st.warning("请先输入需求描述")
        else:
            with st.spinner("大模型正在设计测试用例..."):
                try:
                    cases = testcase_gen.generate_cases(requirement)
                    path = testcase_gen.export_to_excel(cases)
                    st.success(f"✅ 共生成 {len(cases)} 条用例，已导出到 {path}")
                    # 展示前几条
                    st.markdown("**用例预览（前5条）**")
                    for c in cases[:5]:
                        st.markdown(
                            f"- **{c.get('id')}** [{c.get('dimension')}] {c.get('title')}"
                        )
                    # 保存用例JSON供Tab2使用
                    import json
                    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
                    with open(os.path.join(config.OUTPUT_DIR, "cases.json"), "w", encoding="utf-8") as f:
                        json.dump({"cases": cases}, f, ensure_ascii=False, indent=2)
                    st.session_state["cases"] = cases
                except Exception as e:
                    st.error(f"生成失败：{e}")

# ============ Tab2 生成pytest脚本 ============
with tab2:
    st.header("生成 pytest 自动化脚本")
    st.markdown("基于 Tab1 生成的用例，自动转成可运行的 pytest 代码。")
    if st.button("🐍 生成pytest脚本", type="primary"):
        cases = st.session_state.get("cases")
        if not cases:
            st.warning("请先在【生成测试用例】页生成用例")
        else:
            with st.spinner("大模型正在编写pytest脚本..."):
                try:
                    path = script_gen.generate_script(cases)
                    st.success(f"✅ 脚本已生成：{path}")
                    with open(path, "r", encoding="utf-8") as f:
                        st.code(f.read(), language="python")
                except Exception as e:
                    st.error(f"生成失败：{e}")

# ============ Tab3 执行测试&分析 ============
with tab3:
    st.header("执行测试并智能分析")
    st.markdown("运行 pytest，再把输出交给大模型总结缺陷与修复建议。")
    if st.button("▶️ 执行测试并分析", type="primary"):
        with st.spinner("正在执行测试..."):
            try:
                output = runner.run_pytest()
                st.text_area("pytest 输出", output, height=200)
                st.markdown("**🧠 智能报告分析**")
                with st.spinner("大模型正在分析报告..."):
                    analysis = runner.analyze_report(output)
                    st.markdown(analysis)
            except Exception as e:
                st.error(f"执行失败：{e}")

# ============ Tab4 接口测试（真实系统） ============
with tab4:
    st.header("🔌 接口测试（真实系统）")
    st.markdown(
        "输入真实接口信息，AI 自动生成接口用例 + 生成**真正调用该接口**的 pytest 脚本，执行并智能分析。"
        "这能测真实公司系统，是项目的进阶亮点。"
    )
    col_a, col_b = st.columns(2)
    api_url = col_a.text_input("接口地址", value=config.API_TEST_URL)
    api_method = col_b.selectbox("请求方式", ["GET", "POST", "PUT", "DELETE"])
    api_desc = st.text_area(
        "接口描述（让 AI 理解怎么测）",
        value="登录接口：POST https://httpbin.org/post，传用户名和密码，成功返回200",
        height=80,
    )
    if st.button("🚀 生成接口用例 + 脚本 + 执行", type="primary"):
        if not api_url.strip() or not api_desc.strip():
            st.warning("请填写接口地址和接口描述")
        else:
            # 动态更新被测接口配置
            config.API_TEST_URL = api_url.strip()
            config.API_TEST_METHOD = api_method
            with st.spinner("AI 正在生成接口测试用例..."):
                try:
                    cases = api_test.generate_api_cases(api_desc)
                    st.success(f"✅ 共生成 {len(cases)} 条接口用例")
                    st.markdown("**接口用例预览**")
                    for c in cases[:5]:
                        st.markdown(
                            f"- **{c.get('id')}** [{c.get('dimension')}] {c.get('title')} "
                            f"(期望状态码 {c.get('expected_status')})"
                        )
                except Exception as e:
                    st.error(f"生成接口用例失败：{e}")
                    cases = None
            if cases:
                try:
                    script_path = api_test.generate_api_script(cases)
                    st.success(f"✅ 已生成真实接口测试脚本：{script_path}")
                    with open(script_path, "r", encoding="utf-8") as f:
                        st.code(f.read(), language="python")
                except Exception as e:
                    st.error(f"生成脚本失败：{e}")
                try:
                    with st.spinner("正在执行真实接口测试..."):
                        output = api_test.run_api_tests()
                    st.text_area("接口测试 pytest 输出", output, height=180)
                    with st.spinner("AI 正在分析接口测试报告..."):
                        analysis = api_test.analyze_api_report(output, api_desc)
                    st.markdown("**🔍 接口测试智能分析**")
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"执行接口测试失败：{e}")

# ============ Tab5 大模型安全评测 ============
with tab5:
    st.header("大模型安全评测")
    st.markdown("用一批对抗Prompt（越狱/注入/诱导）测试大模型是否会越界回答。")
    if st.button("🛡️ 开始安全评测", type="primary"):
        with st.spinner("正在测试模型安全性..."):
            try:
                results = llm_eval.run_evaluation()
                safe_count = sum(1 for _, _, s in results if s)
                st.success(f"安全通过 {safe_count}/{len(results)}")
                for prompt, response, safe in results:
                    flag = "✅ 安全" if safe else "⚠️ 越界"
                    with st.expander(f"{flag} | {prompt}"):
                        st.write(response)
            except Exception as e:
                st.error(f"评测失败：{e}")
