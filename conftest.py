"""
pytest处理
该模块用于处理pytest测试，包括收集YAML测试文件、执行测试用例和处理测试结果。
"""
import typing as t
import yaml
import pytest
from requests import Response
from common.db import DatabaseClient
from common.redis_client import RedisClient
from common.cache import cache
from common.json import dumps, loads
from common.request import HttpRequest
from common.regular import findalls, sub_var
from common.result import get_result, check_results
from common.exceptions import YamlException, RequestException
from utils.logger import logger, log_handler


# @pytest.fixture(autouse=True)
# def reset_cache_before_test():
#     # 每次清空缓存
#     cache.data.clear()

def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default="dev",  # 默认使用开发环境
        help="指定测试环境，可选值：XXX/XXXX/XXXXX"
    )

@pytest.fixture(scope="session")
def env_config(request):
    """获取当前环境的配置（如baseurl）"""
    from config.environments import ENVIRONMENTS, DEFAULT_ENV
    # 获取命令行参数--env的值，默认使用DEFAULT_ENV
    env = request.config.getoption("--env")
    if env not in ENVIRONMENTS:
        raise ValueError(f"无效环境：{env}，可选环境：{list(ENVIRONMENTS.keys())}")
    return ENVIRONMENTS[env]

def pytest_collect_file(parent, file_path):
    """
    pytest收集文件钩子函数
    如果文件是.yaml后缀且文件名以test开头，则返回YamlFile对象，否则返回None。
    """
    if file_path.suffix == ".yaml" and file_path.name.startswith("test"):
        return YamlFile.from_parent(parent, path=file_path)
    else:
        return None

class YamlFile(pytest.File):
    """
    YAML文件类
    用于收集YAML文件中的测试用例。
    """
    def collect(self):
        # 加载YAML文件内容
        raw = yaml.safe_load(self.path.open(encoding='utf-8'))
        # 检查是否包含以test开头的键
        if not any(k.startswith('test') for k in raw.keys()):
            # 如果不包含，则抛出YamlException异常
            raise YamlException(f"{self.path}yaml non test found")
        # 获取变量配置
        if variable := raw.get('variable'):
            # 将变量添加到全局变量池
            for k, v in variable.items():
                cache.set(k, v)
        # 获取配置信息
        if config := raw.get('config'):
            # 查找需要替换的变量
            keys = findalls(dumps(config))
            # 替换变量
            config = loads(sub_var({k: cache.get(k)
                           for k in keys}, dumps(config)))
            if 'headers' in config:
                existing_headers = cache.get('headers', {})  # 获取缓存中已有的headers
                existing_headers.update(config['headers'])  # 合并新headers
                config['headers'] = existing_headers  # 更新为合并后的值
            # 将配置信息添加到全局变量池
            for k, v in config.items():
                cache.set(k, v)
        # 获取测试用例
        if tests := raw.get('tests'):
            for name, spec in tests.items():
                parameters = spec.get('parameters', None)
                if parameters:
                    logger.info(f"用例 {name} 解析到 {len(parameters)} 个参数组，将生成 {len(parameters)} 条独立用例")
                    for i, param in enumerate(parameters):
                        # 生成用例名称
                        param_desc = param.get('description')
                        if param_desc:
                            test_name = param_desc
                        else:
                            test_name = f"{spec.get('description') or name}_param_{i}"
                        logger.debug(f"生成独立用例：{test_name}，参数：{param}")
                        yield YamlTest.from_parent(
                            self,
                            name=test_name,
                            spec=spec,
                            param=param
                        )
                else:
                    yield YamlTest.from_parent(
                        self,
                        name=spec.get('description') or name,
                        spec=spec,
                        param=None
                    )

class YamlTest(pytest.Item):
    """
    YAML测试用例类
    用于执行YAML文件中的测试用例。
    """
    def __init__(self, name, parent, spec, param=None):
        # 调用父类的构造函数
        super(YamlTest, self).__init__(name, parent)
        # 保存测试用例的规格信息
        self.spec = spec
        # 接收参数化数据
        self.param = param
        # 创建HttpRequest对象
        self.request = HttpRequest(exception=(RequestException, Exception))
        self.db_client = None
        self.redis_client = None

    def runtest(self):
        """Some custom test execution (dumb example follows).
        执行测试用例，发送请求并处理响应。
        """
        if self.param:
            for key in self.param.keys():
                if key in cache.data:  # 直接操作缓存底层数据结构
                    del cache.data[key]
        # 切换到当前用例再打印
        log_handler.set_test_name(self.name)
        logger.info(f"当前执行参数组：{self.param}")
        # 处理参数化变量：将当前参数存入缓存
        if self.param:
            for k, v in self.param.items():
                cache.set(k, v)
        logger.debug(f"发送请求前缓存内容: {cache.data}")
        from config.environments import ENVIRONMENTS  # 导入环境配置
        env = self.config.getoption("--env")
        # 验证环境有效性
        if env not in ENVIRONMENTS:
            raise ValueError(f"无效环境：{env}，可选环境：{list(ENVIRONMENTS.keys())}")
        # 获取环境配置并覆盖baseurl
        env_config = ENVIRONMENTS[env]
        cache.set("baseurl", env_config["baseurl"])
        self._init_clients(env_config)
        try:
            self._exec_db_operations("setup_db")
            self._exec_redis_operations("setup_redis")
            # 发送请求
            r, processed_kwargs = self.request.send_request(** self.spec)
            # 处理响应
            self.response_handle(r, processed_kwargs.get('Validate'), processed_kwargs.get('Extract'))
            self._exec_db_operations("teardown_db")
            self._exec_redis_operations("teardown_redis")
        finally:
            self._close_clients()

    def _init_clients(self, env_config):
        if "db" in env_config:
            self.db_client = DatabaseClient(lambda: env_config["db"])
            logger.info("数据库客户端初始化成功")

        if "redis" in env_config:
            self.redis_client = RedisClient(env_config["redis"])
            logger.info("Redis客户端初始化成功")

    def _exec_db_operations(self, operation_type):
        if not self.db_client:
            return
        operation_sql = self.param.get(operation_type) if self.param else self.spec.get(operation_type)
        if not operation_sql:
            return

        sql = sub_var(cache.data, operation_sql)
        logger.info(f"执行{operation_type} SQL: {sql}")

        try:
            result = self.db_client.execute(sql)
            logger.debug(f"{operation_type} 执行结果: {result}")
        except Exception as e:
            logger.error(f"{operation_type} 执行失败: {str(e)}")
            raise
        self._extract_db_result(result)

    def _extract_db_result(self, db_result):
        extract_config = self.spec.get("extract_db")
        if not extract_config or not db_result:
            return

        for item in extract_config:
            for cache_key, extract_rule in item.items():
                # 支持提取全部结果或指定字段（如"id"取所有id字段，""取全部）
                if extract_rule == "":
                    cache.set(cache_key, db_result)
                else:
                    # 提取指定字段（适用于字典列表结果）
                    extracted = [row.get(extract_rule) for row in db_result if row.get(extract_rule)]
                    cache.set(cache_key, extracted)
        logger.debug(f"数据库提取后缓存: {cache.data}")

    def _exec_redis_operations(self, operation_type):
        if not self.redis_client:
            return
        redis_spec = self.spec.get("redis", {})
        operation_cmd = redis_spec.get(operation_type)
        if not operation_cmd:
            return

        cmd = sub_var(cache.data, operation_cmd)
        cmd_parts = cmd.split()  # 拆分命令（如"HGET user:123 balance"拆分为列表）
        if not cmd_parts:
            logger.warning("Redis命令为空，跳过执行")
            return
        logger.info(f"执行{operation_type} Redis命令: {cmd}")

        # 执行Redis命令并处理结果
        try:
            result = self.redis_client.execute_command(*cmd_parts)
            logger.debug(f"{operation_type} 执行结果: {result}")
        except Exception as e:
            logger.error(f"{operation_type} 执行失败: {str(e)}")
            raise

        # 提取结果到缓存（extract_redis配置）
        self._extract_redis_result(result)

    def _extract_redis_result(self, redis_result):
        redis_spec = self.spec.get("redis", {})
        extract_config = redis_spec.get("extract_redis")
        if not extract_config or redis_result is None:
            return

        for item in extract_config:
            for cache_key, extract_rule in item.items():
                cache.set(cache_key, redis_result)
        logger.debug(f"Redis提取后缓存: {cache.data}")

    def _close_clients(self):
        if self.db_client:
            self.db_client.close()
            logger.info("数据库连接已关闭")
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis连接已关闭")

    def response_handle(self, r: Response, validate: t.Dict, extract: t.List):
        """Handling of responses
        处理响应，包括校验和提取结果。
        """
        # 如果有校验信息，则进行校验
        if validate:
            check_results(r, validate)
        # 如果有提取信息，则进行提取
        if extract:
            get_result(r, extract)
        # logger.debug(f"提取变量后缓存内容: {cache}")

    def repr_failure(self, excinfo):
        """
        当测试用例执行失败时，记录异常信息。
        """
        logger.critical(excinfo.value)
        # 检查 excinfo.traceback 的长度
        if len(excinfo.traceback) >= 6:
            logger.critical(excinfo.traceback[-6:-1])
        else:
            logger.critical(excinfo.traceback)

    def reportinfo(self):
        """
        返回测试用例的报告信息。
        """
        return self.fspath, 0, f"use_case: {self.name}"

if __name__ == '__main__':
    pytest.main()