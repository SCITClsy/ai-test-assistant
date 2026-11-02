# -*- coding: utf-8 -*-
"""
llm_client.py —— 大模型调用封装（本地 Ollama）
统一从这里调用模型，其他模块不直接连模型。
"""
from langchain_ollama import ChatOllama
import config


def get_llm():
    """创建对话模型实例，temperature 调低保证输出稳定"""
    return ChatOllama(
        model=config.LLM_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0.1,  # 低温度，减少随机性
    )


def ask(system_prompt: str, user_prompt: str) -> str:
    """执行一次 系统提示词 + 用户提示词 的对话，返回文本结果"""
    llm = get_llm()
    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )
    return response.content
