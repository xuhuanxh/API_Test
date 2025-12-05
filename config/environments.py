ENVIRONMENTS = {
    "C2C": {  # C2C web/app
        "baseurl": "http://127.0.0.1:8080",
        "db": {
            "host": "192.168.1.203",
            "port": 3306,
            "user": "root",
            "password": "Dly20160607",
            "database": "ti_back",
            "charset": "utf8mb4"
        },
        "redis": {
            "host": "192.168.1.203",
            "port": 6379,
            "password": "Dly20160607",
            "db": 94
        }
    },
    "C2C_BOSS": {  # C2C_BOSS
        "baseurl": "http://192.168.2.199:7111/",
        "db": {
            "host": "192.168.1.203",
            "port": 3306,
            "user": "root",
            "password": "Dly20160607",
            "database": "ti_back",
            "charset": "utf8mb4"
        },
        "redis": {
            "host": "192.168.1.203",
            "port": 6379,
            "password": "Dly20160607",
            "db": 94
        }
    },
    "Qspace": {  # 指纹浏览器
        "baseurl": "http://47.239.197.209:10086",
        "db": {
            "host": "192.168.1.203",
            "port": 3306,
            "user": "root",
            "password": "Dly20160607",
            "database": "nav_browser",
            "charset": "utf8mb4"
        },
        "redis": {
            "host": "192.168.1.203",
            "port": 6379,
            "password": "Dly20160607",
            "db": 94
        }
    },
    "Wallet": {  # 钱包
        "baseurl": "http://127.0.0.1:8222",
        "db": {
            "host": "192.168.1.203",
            "port": 3306,
            "user": "root",
            "password": "Dly20160607",
            "database": "wallet",
            "charset": "utf8mb4"
        },
        "redis": {
            "host": "192.168.1.203",
            "port": 6379,
            "password": "Dly20160607",
            "db": 94
        }
    },
    "NFT": {
        "baseurl": "http://192.168.2.152:8009",
        "db": {
            "host": "192.168.1.101",
            "port": 3306,
            "user": "root",
            "password": "Dly20160607",
            "database": "trendsea",
            "charset": "utf8mb4"
        },
        "redis": {
            "host": "192.168.1.101",
            "port": 6379,
            "password": "Dly20160607",
            "db": 0
        }
    }
}

# 默认环境（若未指定则使用此环境）
DEFAULT_ENV = "Wallet"