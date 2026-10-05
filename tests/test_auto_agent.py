import sys
import os
import time
import logging
from PIL import Image, ImageDraw

# 配置标准日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from device_control.adb_controller import AdbController
from ai_brain.vlm_client import VLMClient

# TODO: 在生产环境中，建议通过环境变量获取 API 密钥，例如 os.environ.get("SILICONFLOW_API_KEY")
# 安全实践：优先从环境变量读取，如果没有则提示用户填入
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your_api_key_here")
def generate_debug_trace(image_path: str, x: int, y: int, output_path: str) -> None:
    """
    在截图上渲染调试标记，记录 AI 推理的 (x, y) 坐标落点。
    
    Args:
        image_path (str): 原始截图路径。
        x (int): 推理得出的 X 坐标。
        y (int): 推理得出的 Y 坐标。
        output_path (str): 带有调试标记的输出图片路径。
    """
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        radius = 15
        # 绘制红色调试靶心
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius), 
            fill="red", 
            outline="white", 
            width=2
        )
        img.save(output_path)
        logger.info("调试落点图已生成: %s", output_path)
    except Exception as e:
        logger.error("生成调试落点图失败: %s", str(e))

def main() -> None:
    logger.info("初始化 Agent UI 交互流水线...")
    
    try:
        # 实例化核心组件
        adb = AdbController()
        vlm = VLMClient(api_key=SILICONFLOW_API_KEY)
        
        # 定义输入输出路径
        before_path = os.path.join(project_root, "screen_before.png")
        after_path = os.path.join(project_root, "screen_after.png")
        debug_path = os.path.join(project_root, "screen_debug.png")
        
        target_element = "设置（齿轮图标）"
        logger.info("当前目标 UI 元素: [%s]", target_element)
        
        # 阶段 1: 状态观测
        logger.info("阶段 1/4: 采集当前设备屏幕状态...")
        if not adb.get_screenshot(before_path):
            logger.error("屏幕状态采集失败，流水线终止。")
            return

        # 阶段 2: 坐标推理
        logger.info("阶段 2/4: 请求视觉大模型进行坐标推理...")
        x, y = vlm.find_element_coordinates(before_path, target_element)
        
        if x == -1 or y == -1:
            logger.error("推理失败，未找到目标元素或数据解析异常。")
            return
            
        logger.info("坐标推理成功，锁定目标位置: (X: %d, Y: %d)", x, y)
        generate_debug_trace(before_path, x, y, debug_path)
        
        # 阶段 3: 动作执行
        logger.info("阶段 3/4: 通过 ADB 下发坐标点击指令...")
        adb.tap(x, y)
        
        logger.info("挂起进程，等待 UI 界面渲染完成 (3秒)...")
        time.sleep(3) 
        
        # 阶段 4: 状态校验
        logger.info("阶段 4/4: 采集操作后的 UI 状态...")
        adb.get_screenshot(after_path)
        logger.info("流水线执行完毕。请通过 %s 核对推理落点偏差。", os.path.basename(debug_path))
        
    except Exception as e:
        logger.critical("流水线执行过程中发生未捕获异常: %s", str(e))

if __name__ == "__main__":
    main()