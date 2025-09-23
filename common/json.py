"""
序列化和反序列化类
该模块提供了JSON数据的序列化和反序列化功能，以及验证JSON字符串的方法。
"""
import json
import typing as t

def loads(content: t.Text) -> t.Any:
    """
    反序列化
        json对象 -> python数据类型
    将JSON字符串转换为Python数据类型。
    """
    return json.loads(content)

def dumps(content: t.Union[t.Dict, t.List], ensure_ascii: bool=True) -> t.Text:
    """
    序列化
        python数据类型 -> json对象
    将Python字典或列表转换为JSON字符串。
    """
    return json.dumps(content, ensure_ascii=ensure_ascii)

def is_json_str(string: t.Text) -> bool:
    """验证是否为json字符串
    尝试将字符串解析为JSON对象，如果解析成功则返回True，否则返回False。
    """
    try:
        json.loads(string)
        return True
    except:
        return False