"""
缓存类
该模块定义了一个全局变量池，用于存储和管理全局变量。
"""
import typing as t
from collections import UserDict

class CachePool(UserDict):
    """全局变量池
    继承自UserDict，提供了获取、设置、检查变量的方法。
    """
    _instance = None  # 类属性，存储唯一实例

    def __new__(cls, *args, **kwargs):
        # 确保只有一个实例
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def get(self, key: t.Text, default=None) -> t.Any:
        # 获取指定键的值，如果键不存在则返回默认值
        return self.data.get(key, default)

    def set(self, key: t.Text, value: t.Any = None) -> None:
        # 设置指定键的值，如果键不存在则创建
        self.data[key] = value

    def has(self, key: t.Text) -> bool:
        # 检查指定键是否存在
        return key in self.data

    def __len__(self) -> int:
        # 返回变量池的长度
        return len(self.data)

    def __bool__(self) -> bool:
        # 判断变量池是否为空
        return bool(self.data)

# 创建全局变量池实例
cache = CachePool()

if __name__ == '__main__':
    # 测试全局变量池的功能
    cache.set('name', 'long')
    print(len(cache))
    print(cache.get('name'))