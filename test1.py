import os
import subprocess

# 获取当前项目的路径
project_path = os.path.dirname(os.path.abspath(__file__))

# 生成 requirements.txt 文件
command = f"pipreqs {project_path} --force"
subprocess.run(command, shell=True)

print("requirements.txt 生成完毕！")