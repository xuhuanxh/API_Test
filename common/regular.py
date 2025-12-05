"""
正则相关操作类
该模块提供了正则表达式的查找、替换和提取功能，支持嵌套结构变量提取。
"""
import re
import typing as t
from common.cache import cache
from common.json import is_json_str, loads, dumps
from utils.logger import logger
from utils.faker_utils import *

def _get_nested_value(obj: t.Union[dict, list, t.Any], path: str) -> t.Any:
    """
    从嵌套对象（字典/列表）中按路径提取值
    支持格式：dict.key 或 list.0.key（数字表示列表索引）
    """
    if not path:
        return obj  # 路径为空时返回原始对象
    parts = path.split('.')
    current = obj
    for part in parts:
        try:
            if isinstance(current, list):
                # 列表按索引访问（转换为整数）
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            elif isinstance(current, dict):
                # 字典按key访问
                if part in current:
                    current = current[part]
                else:
                    return None
            else:
                return None
        except (ValueError, TypeError) as e:
            logger.error(f"提取路径[{path}]失败：{str(e)}")
            return None
    return current


def findalls(string: t.Text) -> t.Dict[t.Text, t.Any]:
    """查找所有${key}格式的变量，支持嵌套路径（如${image_objs.0.image_url}）和根键含点的变量（如${data.token}）"""
    key_pattern = re.compile(r"\$\{([\w.]+)\}")
    keys = key_pattern.findall(string)
    res = {}
    for key in keys:
        if key.startswith('faker.'):
            func_name = key.split('faker.')[1].split('(')[0]
            args = re.findall(r"\((.*?)\)", key)[0].split(",") if "(" in key else []
            args = [arg.strip() for arg in args if arg.strip()]
            faker_funcs = {
                "phone": random_phone,
                "name": random_name,
                "email": random_email,
                "random_int": random_int,
                "random_str": random_str,
                "address": random_address,
                "ssn": random_ssn,
                "username": random_username,
                "password": random_password,
                "birthdate": random_birthdate,
                "sex": random_sex,
                "ip": random_ipv4,
                "domain": random_domain,
                "company": random_company,
                "price": random_price
            }

            if func_name in faker_funcs:
                # 处理带参数的调用
                if func_name == "random_int" and len(args) == 2:
                    res[key] = random_int(int(args[0]), int(args[1]))
                elif func_name == "random_str" and len(args) == 1:
                    res[key] = random_str(int(args[0]))
                else:
                    res[key] = faker_funcs[func_name]()
            continue

        # 优先检查缓存中是否存在完整带点的键（如data.token）
        if '.' in key and cache.get(key) is not None:
            res[key] = cache.get(key)
        elif '.' in key:
            # 缓存中无完整键，再按嵌套路径处理（如image_objs.0.image_url）
            root_key = key.split('.')[0]
            nested_path = '.'.join(key.split('.')[1:])
            root_value = cache.get(root_key)
            if root_value is None:
                res[key] = None
                continue
            nested_value = _get_nested_value(root_value, nested_path)
            res[key] = nested_value
        else:
            # 普通单键变量（如sessionid、type_id）
            res[key] = cache.get(key)
    # logger.debug("需要替换的变量：{}".format(res))
    return res


def sub_var(keys: t.Dict, string: t.Text) -> t.Text:
    """替换变量，自动处理JSON模板中的引号，确保类型正确"""
    res = string
    is_log_printed = False
    # 递归替换直到没有可替换的变量
    # 递归替换直到没有可替换的变量
    while True:
        # 查找当前字符串中剩余的变量
        remaining_vars = findalls(res)
        if not remaining_vars:
            break  # 无剩余变量，退出循环

        if not is_log_printed:
            logger.debug("需要替换的变量：{}".format(remaining_vars))
            is_log_printed = True

        # 替换剩余变量
        for key, value in remaining_vars.items():
            # 修复正则表达式，正确匹配 ${key} 模式（支持key含点号）
            pattern = re.compile(rf'(["\']?)\$\{{{re.escape(key)}}}(["\']?)')
            # 生成对应类型的JSON值字符串
            if value is None:
                value_str = "null"
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif isinstance(value, bool):
                value_str = "true" if value else "false"
            else:
                # 字符串类型不自动加引号，由模板原有引号决定
                value_str = str(value)

            # 替换时处理引号：非字符串类型移除原有引号，字符串类型保留原有引号
            def replace_func(match: re.Match) -> str:
                quote1, quote2 = match.group(1), match.group(2)
                # 非字符串类型，去掉前后引号
                if not isinstance(value, str):
                    return value_str
                # 字符串类型保留原有引号
                return f"{quote1}{value_str}{quote2}"

            res = pattern.sub(replace_func, res)

    # 验证替换结果
    try:
        res_dict = loads(res)
        filtered = {
            "method": res_dict.get("method"),
            "route": res_dict.get("route"),
            "RequestData": res_dict.get("RequestData")
        }
        logger.debug("替换结果（核心数据）：{}".format(dumps(filtered, ensure_ascii=False)))
    except Exception as e:
        logger.error(f"替换结果解析失败：{e}，原始替换结果：{res}")
    return res


def get_var(key: t.Text, raw_str: t.Text) -> t.Text:
    """获取变量"""
    if is_json_str(raw_str):
        _obj = re.compile(r'\"%s"\s*:\s*"([^"]+)"' % key).findall(raw_str)
        return _obj[0] if _obj else ""
    logger.warning(f"raw_str_is_not_json_str: {raw_str}")
    _obj = re.compile(r'%s' % key).findall(raw_str)
    return _obj[0] if _obj else ""


def sub_sql_var(keys: t.Dict, sql: t.Text) -> t.Text:
    """
    专门用于SQL语句的变量替换
    """
    res = sql
    while True:
        remaining_vars = findalls(res)  # 复用变量查找逻辑
        if not remaining_vars:
            break

        for key, value in remaining_vars.items():
            pattern = re.compile(rf'\$\{{{re.escape(key)}}}')  # 简化正则（SQL无需处理引号自动移除）

            # 1. 处理空值
            if value is None:
                value_str = "NULL"  # SQL空值用NULL（无引号）
            # 2. 处理数值类型（整数/浮点数）
            elif isinstance(value, (int, float)):
                value_str = str(value)  # 数值直接拼接，不加引号
            # 3. 处理布尔类型（SQL通常用1/0表示）
            elif isinstance(value, bool):
                value_str = "1" if value else "0"
            # 4. 处理字符串类型（转义单引号）
            else:
                # SQL字符串中的单引号需要转义为两个单引号（如 ' 转 ''）
                escaped_value = str(value).replace("'", "''")
                value_str = f"'{escaped_value}'"  # 字符串必须用单引号包裹

            res = pattern.sub(value_str, res)

    logger.debug(f"SQL变量替换完成: {res}")
    return res

def sub_redis_var(keys: t.Dict, cmd: t.Text) -> t.Text:
    """专门用于Redis命令的变量替换"""
    res = cmd
    while True:
        remaining_vars = findalls(res)  # 复用变量查找逻辑
        if not remaining_vars:
            break
        for key, value in remaining_vars.items():
            pattern = re.compile(rf'\$\{{{re.escape(key)}}}')
            # Redis命令参数通常直接拼接，无需单引号（字符串也可直接使用）
            value_str = str(value) if value is not None else ""
            res = pattern.sub(value_str, res)
    logger.debug(f"Redis命令替换完成: {res}")
    return res