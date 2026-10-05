import time
import sys
import os

# 核心魔法：把项目的根目录(AgentQA_Project)强行加入到 Python 的搜索路径中
# 这样 Python 就能找到 device_control 文件夹里的代码了
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 此时导入就不会报错了
from device_control.adb_controller import AdbController

def main():
    print("--- 准备测试车机连接 ---")
    controller = AdbController()

    # 把截图保存在项目的根目录，方便在 VSCode 左侧直接看到
    before_path = os.path.join(project_root, "screen_before.png")
    after_path = os.path.join(project_root, "screen_after.png")

    # 1. 截取点击前屏幕
    controller.get_screenshot(before_path)
    print("等待 3 秒...")
    time.sleep(3)

    # 2. 点击屏幕中央 (基于 1408x792 屏幕)
    controller.tap(704, 396)
    print("已点击屏幕中央！等待车机界面反应...")
    time.sleep(2) 

    # 3. 截取点击后屏幕
    controller.get_screenshot(after_path)
    print("测试执行完毕！请在根目录查看生成的前后对比截图。")

if __name__ == "__main__":
    main()