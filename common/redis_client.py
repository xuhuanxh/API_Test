import redis
from utils.logger import logger

class RedisClient:
    def __init__(self, env_config):
        """初始化Redis连接"""
        self.env_config = env_config
        self.client = None
        self.connect()

    def connect(self):
        """建立Redis连接"""
        try:
            self.client = redis.Redis(
                host=self.env_config["host"],
                port=self.env_config["port"],
                password=self.env_config.get("password", ""),
                db=self.env_config["db"],
                decode_responses=True  # 自动解码为字符串
            )
            # 测试连接
            self.client.ping()
            logger.info(f"成功连接到Redis: {self.env_config['host']}:{self.env_config['port']} db={self.env_config['db']}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise

    def execute_command(self, *args, **kwargs):
        """执行redis命令"""
        try:
            return self.client.execute_command(*args, **kwargs)
        except Exception as e:
            logger.error(f"Redis命令执行失败:{str(e)}")
            raise

    def close(self):
        """关闭redis连接"""
        if self.client:
            self.client.close()
            # logger.info("Redis连接关闭")


if __name__ == '__main__':
    test_redis_config = {
        "host": "192.168.1.101",
        "port": 6379,
        "password": "Dly20160607",
        "db": 0
    }
    client = RedisClient(test_redis_config)
    result = client.execute_command("SET", "testkey", "test")
    print(result)
    result = client.execute_command("GET", "testkey")
    print(result)
    client.close()