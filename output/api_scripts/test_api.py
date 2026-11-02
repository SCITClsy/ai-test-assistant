# -*- coding: utf-8 -*-
# 本文件由 AI 测试助手自动生成：对真实接口发起请求并断言
import requests
import pytest

BASE_URL = 'https://jsonplaceholder.typicode.com/posts/1'
METHOD = 'GET'
TIMEOUT = 15


def api_request(params=None, headers=None, json_body=None):
    """真正向被测接口发一次请求，返回 requests.Response"""
    url = BASE_URL
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    if METHOD == "POST":
        return requests.post(url, headers=hdrs, params=params, json=json_body, timeout=TIMEOUT)
    elif METHOD == "PUT":
        return requests.put(url, headers=hdrs, params=params, json=json_body, timeout=TIMEOUT)
    elif METHOD == "DELETE":
        return requests.delete(url, headers=hdrs, params=params, timeout=TIMEOUT)
    else:
        return requests.get(url, headers=hdrs, params=params, timeout=TIMEOUT)


def test_api_001():
    """验证正常获取仓库信息"""
    resp = api_request(params={"owner": "octocat", "repo": "Hello-World"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 200, f"期望状态码200，实际{resp.status_code}: {resp.text}"
    assert "name" in resp.text, "响应中应包含字段: name"


def test_api_002():
    """验证正常获取仓库描述"""
    resp = api_request(params={"owner": "octocat", "repo": "Hello-World"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 200, f"期望状态码200，实际{resp.status_code}: {resp.text}"
    assert "description" in resp.text, "响应中应包含字段: description"


def test_api_003():
    """验证owner为空时的响应"""
    resp = api_request(params={"owner": "", "repo": "Hello-World"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 404, f"期望状态码404，实际{resp.status_code}: {resp.text}"


def test_api_004():
    """验证repo为空时的响应"""
    resp = api_request(params={"owner": "octocat", "repo": ""}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 404, f"期望状态码404，实际{resp.status_code}: {resp.text}"


def test_api_005():
    """验证owner不存在时的响应"""
    resp = api_request(params={"owner": "non-existent", "repo": "Hello-World"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 404, f"期望状态码404，实际{resp.status_code}: {resp.text}"


def test_api_006():
    """验证repo不存在时的响应"""
    resp = api_request(params={"owner": "octocat", "repo": "non-existent"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 404, f"期望状态码404，实际{resp.status_code}: {resp.text}"


def test_api_007():
    """验证缺少owner时的响应"""
    resp = api_request(params={"repo": "Hello-World"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 400, f"期望状态码400，实际{resp.status_code}: {resp.text}"


def test_api_008():
    """验证缺少repo时的响应"""
    resp = api_request(params={"owner": "octocat"}, headers={"Content-Type": "application/json"})
    assert resp.status_code == 400, f"期望状态码400，实际{resp.status_code}: {resp.text}"

