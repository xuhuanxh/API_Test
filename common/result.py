"""
response响应处理
该模块用于处理请求的响应，包括提取结果和校验结果。
"""
import re
import typing as t

import jsonpath
import pytest
import allure
from requests import Response
from common.cache import cache
from common.regular import re, get_var
from utils.logger import logger

def get_result(r: Response, extract: t.List) -> None:
    """获取值：优先从JSON响应提取嵌套字段，再 fallback 到原有逻辑"""
    # 尝试解析响应为JSON（用于提取嵌套字段）
    resp_json = None
    try:
        resp_json = r.json()  # 解析完整响应
        logger.debug(f"响应JSON: {resp_json}")  # 确认data位置
    except Exception as e:
        logger.debug(f"响应解析JSON失败: {e}")
        return

    for key in extract:
        value = None
        if resp_json is not None:
            # 分割变量路径（支持顶级data和嵌套data.token）
            keys = key.split('.')
            temp = resp_json
            for k in keys:
                if isinstance(temp, dict) and k in temp:
                    temp = temp[k]  # 逐级获取值（如key="data"直接取resp_json["data"]）
                else:
                    temp = None
                    break
            value = temp

        # 2. 如果JSON中未找到，headers -> cookies -> 正则
        if value is None:
            if key in r.headers:
                value = r.headers[key]
            elif key in r.cookies:
                value = r.cookies.get(key)
            else:
                value = get_var(key, r.text)  # 原正则提取

        # 记录提取结果并存储到缓存
        logger.info(f"提取变量 {key} 的值：{value}")
        if value is not None:  # 确保提取到值再存入缓存
            cache.set(key, value)
            pytest.assume(key in cache, f"变量 {key} 未成功存入缓存")
        else:
            logger.warning(f"未提取到变量 {key} 的值")

    # 在Allure报告中添加提取步骤
    with allure.step("提取返回结果中的值"):
        for key in extract:
            allure.attach(name="提取%s" % key, body=str(cache.get(key)))

def check_results(r: Response, validate: t.Dict) -> None:
    """检查运行结果
    校验响应的状态码、预期值和正则表达式。
    """
    # 获取预期状态码
    expectcode = validate.get('expectcode')
    # 获取预期结果
    resultcheck = validate.get('resultcheck')
    # 获取正则表达式
    regularcheck = validate.get('regularcheck')
    # jsonpath断言
    jsonpath_check = validate.get('jsonpath_check')
    # 如果有预期状态码，则进行校验
    if expectcode:
        with allure.step("校验返回响应码"):
            allure.attach(name='预期响应码', body=str(expectcode))
            allure.attach(name='实际响应码', body=str(r.status_code))
        pytest.assume(int(expectcode) == r.status_code)
    # 如果有预期结果，则进行校验
    if resultcheck:
        with allure.step("校验响应预期值"):
            allure.attach(name='预期值', body=str(resultcheck))
            try:
                # 尝试解析为 JSON 并解码
                resp_json = r.json()
                import json
                actual_body = json.dumps(resp_json, ensure_ascii=False)
            except:
                actual_body = r.text
            allure.attach(name='实际值', body=actual_body)
        pytest.assume(resultcheck in actual_body)
    # 如果有正则表达式，则进行校验
    if regularcheck:
        with allure.step("正则校验返回结果"):
            allure.attach(name='预期正则', body=regularcheck)
            allure.attach(name='响应值', body=str(
                re.findall(regularcheck, r.text)))
        pytest.assume(re.findall(regularcheck, r.text))
    if jsonpath_check:
        try:
            resp_json = r.json()  # 解析响应为JSON
        except:
            pytest.assume(False, "响应不是JSON格式，无法进行JSONPath断言")
            return

        with allure.step("JSONPath校验"):
            for path, expected in jsonpath_check.items():
                # 执行JSONPath查询
                actual = jsonpath.jsonpath(resp_json, path)
                allure.attach(name=f"JSONPath: {path}",
                              body=f"预期: {expected}, 实际: {actual}")
                # 断言结果存在且匹配
                pytest.assume(actual is not False, f"JSONPath {path} 未找到匹配结果")
                pytest.assume(actual[0] == expected, f"JSONPath {path} 匹配失败")