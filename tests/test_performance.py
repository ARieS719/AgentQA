import os
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from device_control.adb_controller import AdbController
from vision_core.performance_analyzer import PerformanceAnalyzer

def main():
    logger.info(" 启动 E2E 性能分析测试专项 ")
    
    adb = AdbController()
    analyzer = PerformanceAnalyzer()
    video_path = os.path.join(project_root, "perf_transition.mp4")
    
    # 请确保此时模拟器处在【主桌面】
    logger.info("请确保模拟器处于主桌面，3秒后将开始点击 '设置' 并分析冷启动性能...")
    time.sleep(3)
    
    # 1. 启动录屏守护进程
    adb.start_screen_record()
    
    # 2. 触发点击 (假设 778, 744 是设置图标。如果不对，AI 瞎点了个空白也行，只是测不出变化)
    logger.info(" 模拟用户手指按下 '设置' 图标...")
    adb.tap(778, 744)
    
    # 3. 故意等待 4 秒，确保界面彻底加载并渲染完毕
    logger.info("等待界面响应与渲染完成...")
    time.sleep(4)
    
    # 4. 结束录屏并拉回视频
    if adb.stop_and_pull_record(video_path):
        # 5. 移交视频流给 OpenCV 性能引擎进行切割分析
        logger.info("=================================")
        logger.info("开始进行帧级渲染分析...")
        analyzer.analyze_transition_time(video_path)
        logger.info("=================================")
    else:
        logger.error("录屏文件获取失败，无法进行性能分析。")

if __name__ == "__main__":
    main()