import os
import sys
import time
import logging
import pytest

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s'
)
logger = logging.getLogger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from device_control.adb_controller import AdbController
from ai_brain.vlm_client import VLMClient
from vision_core.image_processor import ImageProcessor

# TODO: 生产环境中需通过环境变量读取
# 安全实践：优先从环境变量读取，如果没有则提示用户填入
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your_api_key_here")

class TestSettingsApp:
    """
    系统设置应用相关的自动化测试套件
    """
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self):
        """
        类级别的初始化前置条件 (Fixture)
        """
        logger.info("--- 测试套件初始化开始 ---")
        # 实际项目中，这里通常会包含 adb 连接检查、应用重置等操作
        yield
        logger.info("--- 测试套件清理完成 ---")

    def test_open_settings_from_home(self):
        """
        测试用例: 从主屏幕成功打开设置应用
        """
        logger.info("开始执行用例: test_open_settings_from_home")
        
        # 1. 组件初始化
        adb = AdbController()
        vlm = VLMClient(api_key=SILICONFLOW_API_KEY)
        processor = ImageProcessor()
        
        raw_path = os.path.join(project_root, "screen_raw.png")
        som_path = os.path.join(project_root, "screen_som.png")
        after_path = os.path.join(project_root, "screen_after_som.png")
        
        # 2. 回到主屏幕 (测试环境收敛)
        logger.info("初始化设备状态: 触发 Home 键，确保处于主屏幕...")
        adb.run_adb_cmd(["shell", "input", "keyevent", "KEYCODE_HOME"])
        time.sleep(2)
        
        # 3. 状态采集与打标
        assert adb.get_screenshot(raw_path) is True, "前置截图获取失败"
        mark_dict = processor.generate_som_image(raw_path, som_path)
        assert mark_dict, "OpenCV 未能提取到任何 UI 标记"
        
        # 4. VLM 决策与点击
        target_id = vlm.find_element_by_som_id(som_path, "底部导航栏的设置（齿轮）图标")
        assert target_id != "-1" and target_id in mark_dict, f"VLM 定位失败，返回 ID: {target_id}"
        
        target_x, target_y = mark_dict[target_id]
        adb.tap(target_x, target_y)
        
        # 等待转场动画
        time.sleep(3)
        
        # 5. 结果采集与 AI 断言 (核心 QA 环节)
        adb.get_screenshot(after_path)
        
        expected_state = "当前界面是系统的设置 (Settings) 页面，通常包含网络、显示、声音等设置项列表"
        is_passed = vlm.assert_screen_state(after_path, expected_state)
        
        # 使用 Pytest 的原生 assert 抛出最终测试结果
        assert is_passed is True, "AI 断言失败：当前界面不符合预期的设置页面状态"