"""
日志类
该模块用于初始化和配置日志记录器，提供按时间轮转的日志文件功能。
"""
import os
import logging
import re
import sys
from logging.handlers import BaseRotatingHandler
from datetime import datetime

class CustomTestCaseRotatingHandler(BaseRotatingHandler):
    """自定义按时间命名的日志处理器
    继承自BaseRotatingHandler，实现按时间轮转日志文件的功能。
    """
    def __init__(self, log_dir, base_filename, encoding=None):
        # 日志目录
        self.log_dir = log_dir
        # 日志基础文件名
        self.base_filename = base_filename
        # 日志文件编码
        self.encoding = encoding
        # 用例名称
        self.current_test_name = None

        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)

        # 生成当前时间的日志文件名
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"{base_filename}_{current_time}.log")

        # 调用父类的构造函数
        super().__init__(log_file, 'a', encoding, delay=False)

    def set_test_name(self, test_name):
        """设置当前测试用例名称，用于生成新的日志文件"""
        if self.current_test_name != test_name:
            self.current_test_name = test_name
            # 生成包含用例名称和时间戳的新日志文件名
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 清理用例名称中的特殊字符，避免文件命名问题
            safe_test_name = re.sub(r'[\\/*?:"<>|]', '_', test_name)
            new_log_file = os.path.join(
                self.log_dir,
                f"{safe_test_name}_{current_time}.log"
            )
            # 切换到新的日志文件
            self.stream.close()
            self.baseFilename = new_log_file
            self.stream = self._open()

    def shouldRollover(self, record):
        return False

    def doRollover(self):
        pass

def init_logger():
    """初始化日志"""
    # 获取项目根目录
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 日志目录
    log_dir = os.path.join(basedir, 'logs')

    # 日志格式化器
    logger_formatter = logging.Formatter(
        '%(levelname)s %(asctime)s [%(filename)s:%(lineno)s] %(thread)d %(message)s')

    # 创建日志记录器
    logger_debug = logging.getLogger('apitest')
    logger_debug.handlers.clear()  # 清除已存在的处理器

    # 使用自定义处理器
    handler_debug = CustomTestCaseRotatingHandler(
        log_dir=log_dir,
        base_filename='testcase',
        encoding='utf-8'
    )

    # 设置处理器的格式化器
    handler_debug.setFormatter(logger_formatter)
    # 设置日志记录器的级别为DEBUG
    logger_debug.setLevel(logging.DEBUG)
    # 添加处理器到日志记录器
    logger_debug.addHandler(handler_debug)

    # 添加控制台输出
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(logger_formatter)
    # logger_debug.addHandler(console_handler)

    return logger_debug, handler_debug

# 初始化日志记录器和处理器
logger, log_handler = init_logger()

if __name__ == '__main__':
    # 测试日志记录功能
    logger.debug("debug")
    logger.info("info")
    logger.warning('warning')
    logger.error("error")
    logger.critical('critical')