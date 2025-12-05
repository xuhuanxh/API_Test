"""
requests二次封装
该模块对requests库进行了二次封装，提供了更方便的请求发送和处理功能。
"""
import typing as t
import allure
import urllib3
from requests import Session, Response
from common.cache import cache
from common.json import json, loads, dumps
from common.regular import sub_var, findalls
from utils.logger import logger
from typing import Tuple

# 禁用urllib3的警告信息
urllib3.disable_warnings()

class HttpRequest(Session):
    """requests方法二次封装
    继承自requests.Session，提供了自定义的请求发送和处理方法。
    """
    def __init__(self, *args: t.Union[t.Set, t.List], **kwargs: t.Dict[t.Text, t.Any]):
        # 调用父类的构造函数
        super(HttpRequest, self).__init__()
        # 获取异常类型，默认为Exception
        self.exception = kwargs.get("exception", Exception)

    def send_request(self, **kwargs: t.Dict[t.Text, t.Any]) -> Tuple[Response, t.Dict]:
        """发送请求
        :param method: 发送方法
        :param route: 发送路径
        optional 可选参数
        :param extract: 要提取的值
        :param params: 发送参数-"GET"
        :param data: 发送表单-"POST"
        :param json: 发送json-"post"
        :param headers: 头文件
        :param cookies: 验证字典
        :param files: 上传文件,字典：类似文件的对象``
        :param timeout: 等待服务器发送的时间
        :param auth: 基本/摘要/自定义HTTP身份验证
        :param allow_redirects: 允许重定向，默认为True
        :type bool
        :param proxies: 字典映射协议或协议和代理URL的主机名。
        :param stream: 是否立即下载响应内容。默认为“False”。
        :type bool
        :param verify: （可选）一个布尔值，在这种情况下，它控制是否验证服务器的TLS证书或字符串，在这种情况下，它必须是路径到一个CA包使用。默认为“True”。
        :type bool
        :param cert: 如果是字符串，则为ssl客户端证书文件（.pem）的路径
        :return: request响应
        """
        try:
            # 获取请求方法，默认为GET并转换为大写
            method = kwargs.get('method', 'GET').upper()
            # 拼接请求URL
            url = cache.get('baseurl') + kwargs.get('route')
            # 记录请求URL
            logger.info("Request Url: {}".format(url))
            # 记录请求方法
            logger.info("Request Method: {}".format(method))
            # 将请求参数转换为JSON字符串
            kwargs_str = dumps(kwargs)
            # 查找需要替换的变量
            if is_sub := findalls(kwargs_str):
                # 替换变量
                kwargs = loads(sub_var(is_sub, kwargs_str))
            # logger.info(f"变量替换后 route: {kwargs.get('route')}")
            filtered_kwargs = {
                "method": kwargs.get("method"),
                "route": kwargs.get("route"),
                "RequestData": kwargs.get("RequestData")  # 实际发送的参数（headers/json/params等）
            }
            logger.info("实际请求数据: {}".format(filtered_kwargs))
            # 合并请求数据
            request_data = HttpRequest.mergedict(kwargs.get('RequestData'),
                                                 headers=cache.get('headers'),
                                                 timeout=cache.get('timeout'))
            # 发送请求
            response = self.dispatch(method, url, **request_data)
            # 生成请求和响应的描述信息
            request_params = request_data.get('json') or request_data.get('params') or request_data.get('data') or {}
            description_html = f"""
                    <font color=red>请求方法: </font>{method}<br/>
                    <font color=red>请求地址: </font>{url}<br/>
                    <font color=red>请求头: </font>{str(request_data.get('headers', ''))}<br/>
                    <font color=red>请求参数:</font><br/>
                    <pre>{json.dumps(request_params, ensure_ascii=False, indent=2)}</pre><br/>
                    <font color=red>响应状态码: </font>{str(response.status_code)}<br/>
                    <font color=red>响应时间: </font>{str(response.elapsed.total_seconds())}<br/>
                    """
            try:
                # 解析响应为JSON并处理中文编码
                response_json = response.json()
                response_str = json.dumps(response_json, ensure_ascii=False, indent=2)
            except:
                # 非JSON响应直接使用文本
                response_str = response.text

            description_html += f"""
                    <font color=red>响应内容:</font><br/>
                    <pre>{response_str}</pre><br/>
                    """
            allure.dynamic.description_html(description_html)  # 更新Allure报告描述
            # 记录请求结果
            logger.info("请求结果: {}{}".format(response, response.text))
            return response, kwargs
        except self.exception as e:
            # 记录异常信息
            logger.exception(format(e))
            raise e

    def dispatch(self, method: t.Text, *args: t.Union[t.List, t.Tuple], **kwargs: t.Dict) -> Response:
        """请求分发
        根据请求方法调用相应的requests方法。
        """
        handler = getattr(self, method.lower())
        return handler(*args, **kwargs)

    @staticmethod
    def mergedict(args: t.Dict, **kwargs: t.Dict):
        """合并字典
        将两个字典进行合并，如果有相同的键，则将值合并。
        """
        if args is None:
            args = {}
        for k, v in args.items():
            if k in kwargs:
                # 检查 kwargs[k] 和 args[k] 是否为 None
                if kwargs[k] is None:
                    kwargs[k] = {}
                if args[k] is None:
                    args[k] = {}
                kwargs[k] = {**args[k], **kwargs.pop(k)}
        args.update(kwargs)
        return args