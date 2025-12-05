"""
随机生成数据
"""
from faker import Faker
from faker.providers import BaseProvider
import random
import string

fake = Faker("zh_CN")

class CustomProvider(BaseProvider):
    def phone_number(self):
        """生成大陆手机号"""
        prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                    "150", "151", "152", "153", "155", "156", "157", "158", "159",
                    "170", "171", "173", "176", "177", "178",
                    "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
        return f"{random.choice(prefixes)}{''.join([str(random.randint(0, 9)) for _ in range(8)])}"

    def random_int(self, min_val=0, max_val=1000, step=""):
        """生成随机整数"""
        return random.randint(min_val, max_val)

    def random_str(self, length: int = 8) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def price(self, min_val=0, max_val=1000, decimal_places=2):
        return round(random.uniform(min_val, max_val), decimal_places)

fake.add_provider(CustomProvider)

def random_phone():
    """生成随机电话号码"""
    return fake.phone_number()

def random_name():
    """生成随机姓名"""
    return fake.name()

def random_email():
    """生成随机email"""
    return fake.email()

def random_int(min_val=0, max_val=1000):
    """生成随机整数"""
    return fake.random_int(min_val, max_val)

def random_str(length: int = 8) -> str:
    """生成随机字符串"""
    return fake.random_str(length)

def random_address():
    """生成随机地址"""
    return fake.address()

def random_ssn():
    """生成随机身份证号"""
    return fake.ssn()

def random_username():
    """生成随机用户名"""
    return fake.user_name()

def random_password():
    """生成随机密码"""
    return fake.password()

def random_birthdate():
    """生成随机生日"""
    return fake.date_of_birth()

def random_sex():
    """生成随机性别"""
    return fake.simple_profile()['sex']

def random_ipv4():
    """生成随机IPV4地址"""
    return fake.ipv4()

def random_domain():
    """生成随机域名"""
    return fake.domain_name()

def random_company():
    """生成随机公司名"""
    return fake.company()

def random_price(min_val=0, max_val=1000, decimal_places=2):
    """生成随机价格"""
    return fake.price(min_val=min_val, max_val=max_val, decimal_places=decimal_places)

if __name__ == '__main__':
    # print(random_phone())
    # print(random_name())
    # print(random_email())
    # print(random_str(10))
    # print(random_domain())
    print(random_price(0, 2000000, 2))
    # print(random_ipv4())