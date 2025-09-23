"""
异常类
该模块定义了自定义异常类，用于在用例执行失败时进行错误报告。
"""
from requests.exceptions import RequestException

class YamlException(Exception):
    """Custom exception for error reporting.
    自定义异常类，用于在用例执行失败时进行详细的错误报告。
    """
    def __init__(self, value):
        # 初始化异常信息
        self.value = value

    def __str__(self):
        # 返回格式化后的错误信息
        return "\n".join(
            [
                "usecase execution failed",
                f"   spec failed: {self.value}",
                "   For more details, see this the document.",
            ]
        )