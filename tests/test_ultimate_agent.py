import sys
import os
import time
import logging

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
from vision_core.image_processor import ImageProcessor

# TODO: 生产环境中需通过环境变量或 KMS (密钥管理系统) 注入
# 安全实践：优先从环境变量读取，如果没有则提示用户填入
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your_api_key_here")
def main() -> None:
    logger.info("初始化基于 SoM 架构的视觉自动化 Agent 流水线...")
    
    try:
        # 1. 实例化核心组件
        adb = AdbController()
        vlm = VLMClient(api_key=SILICONFLOW_API_KEY)
        processor = ImageProcessor()
        
        # 2. 声明 I/O 路径
        raw_path = os.path.join(project_root, "screen_raw.png")
        som_path = os.path.join(project_root, "screen_som.png")
        after_path = os.path.join(project_root, "screen_after_som.png")
        
        target_element = "底部导航栏的设置（齿轮）图标"
        logger.info("当前下发测试任务目标: [%s]", target_element)
        
        # ================= 闭环流转开始 =================
        
        # 阶段 1: 状态采集
        logger.info("阶段 1/5: 采集初始 UI 状态...")
        if not adb.get_screenshot(raw_path):
            logger.error("屏幕状态采集失败，中断执行。")
            return
            
        # 阶段 2: 视觉标记注入 (SoM)
        logger.info("阶段 2/5: 执行 OpenCV 边缘检测与控件标定 (SoM)...")
        mark_dict = processor.generate_som_image(raw_path, som_path)
        
        if not mark_dict:
            logger.error("控件提取失败: 未能生成有效标记集。")
            return
            
        # 阶段 3: 语义决策
        logger.info("阶段 3/5: 请求 VLM 云端进行语义决策与 ID 匹配...")
        target_id = vlm.find_element_by_som_id(som_path, target_element)
        
        if target_id == "-1" or target_id not in mark_dict:
            logger.error("决策引擎异常: VLM 未返回有效标签或返回的 ID (%s) 不在标记集中。", target_id)
            return
            
        # 阶段 4: 坐标映射与执行
        target_x, target_y = mark_dict[target_id]
        logger.info("决策通过，锁定标签 ID: [%s], 映射绝对坐标: (X:%d, Y:%d)", target_id, target_x, target_y)
        
        logger.info("阶段 4/5: 通过 ADB 驱动底层执行硬件级点击指令...")
        adb.tap(target_x, target_y)
        
        logger.info("线程挂起 (3s)，等待底层 UI 渲染完成...")
        time.sleep(3)
        
        # 阶段 5: 断言/状态确认准备
        logger.info("阶段 5/5: 采集操作后的 UI 状态用于结果断言...")
        adb.get_screenshot(after_path)
        logger.info("流水线单次任务执行结束。操作后状态已存至: %s", os.path.basename(after_path))

    except Exception as e:
        logger.critical("主流程抛出未捕获异常: %s", str(e))

if __name__ == "__main__":
    main()