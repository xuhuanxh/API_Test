"""
主运行文件
该脚本用于执行测试并生成Allure测试报告。
"""
import subprocess
def main():
    """主函数
    执行一系列命令，包括激活虚拟环境、运行pytest测试、复制环境配置文件、生成Allure报告。
    """
    # 定义要执行的命令列表
    cmd_all = (
        "source env/bin/activate",  # 激活虚拟环境
        "pytest --env Qspace -s tests/xxx.yaml --alluredir allure-results --clean-alluredir",  # 运行pytest测试并指定Allure结果目录
        "cp environment.properties allure-results",  # 复制环境配置文件到Allure结果目录
        "allure generate allure-results -c -o allure-report --lang zh ",  # 生成Allure报告
        # "allure open allure-report"  # 打开Allure报告（注释掉，可根据需要启用）
    )
    for cmd in cmd_all:
        subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    main()