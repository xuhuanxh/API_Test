import mysql.connector
from  mysql.connector import Error
from utils.logger import logger

class DatabaseClient:
    def __init__(self, env_config):
        """初始化数据库"""
        self.env_config = env_config()
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        """建立连接"""
        try:
            self.connection = mysql.connector.connect(
                host=self.env_config['host'],
                port=self.env_config['port'],
                user=self.env_config['user'],
                password=self.env_config['password'],
                database=self.env_config['database'],
                charset=self.env_config['charset'],
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info(f"成功连接到数据：{self.env_config['database']}")
        except Error as e:
            logger.error(f"数据库连接失败：{str(e)}")
            raise

    def execute(self, sql, params=None):
        """执行sql"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            # logger.debug(f"执行sql:{sql}, 参数:{params}")
            self.cursor.execute(sql, params or {})
            # 根据sql的类型,判断是否需要提交事务
            if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP')):
                self.connection.commit()
                return self.cursor.rowcount
            else:
                return self.cursor.fetchall()
        except Error as e:
            logger.error(f"sql执行失败{str(e)}, sql:{sql}, params:{params}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            # logger.info("数据库连接已关闭")


if __name__ == '__main__':
    db = {
        "host": "192.168.1.203",
        "port": 3306,
        "user": "root",
        "password": "Dly20160607",
        "database": "ti_back",
        "charset": "utf8mb4"
    }
    client = DatabaseClient(lambda: db)
    result = client.execute("select * from ti_user")
    print(result)
    for i in result:
        print(i["username"])
    client.close()
