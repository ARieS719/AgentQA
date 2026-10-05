import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

try:
    from device_control.adb_controller import AdbController
    from ai_brain.vlm_client import VLMClient
    from vision_core.image_processor import ImageProcessor
    from ai_brain.agent_engine import AgentEngine
except Exception as e:
    print(f"====== [致命错误] 组件导入失败！原因: {e} ======")
    sys.exit(1)

# TODO: 填入你的 API Key
# 安全实践：优先从环境变量读取，如果没有则提示用户填入
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your_api_key_here")
def main():
    logger.info("系统初始化...")
    
    adb = AdbController()
    vlm = VLMClient(api_key=SILICONFLOW_API_KEY)
    processor = ImageProcessor()
    
    engine = AgentEngine(
        adb_controller=adb,
        vlm_client=vlm,
        image_processor=processor,
        max_steps=8 
    )
    
    # 明确界定任务完成（DONE）的条件，防止 AI 陷入重复点击的死循环
    # 宏观目标：测试异常自愈能力
    macro_goal = """
    请帮我打开系统的 'Camera' (相机) 应用，或者 'Contacts' (通讯录) 应用。
    进入应用后，任务即告完成 (DONE)。
    【注意】：如果你遇到了系统权限请求弹窗，请自主处理。
    """
    
    logger.info("将任务目标移交 Agent 引擎托管。")
    is_success = engine.execute_task(goal=macro_goal)
    
    if is_success:
        logger.info(" 自动化测试用例通过！Agent 成功完成了宏观目标。")
    else:
        logger.error(" 自动化测试用例失败！Agent 无法达成宏观目标。")

if __name__ == "__main__":
    main()