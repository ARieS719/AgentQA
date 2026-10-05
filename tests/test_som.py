import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from vision_core.image_processor import ImageProcessor

def main():
    processor = ImageProcessor()
    
    # 我们使用之前已经保存好的屏幕截图
    input_image = os.path.join(project_root, "screen_before.png")
    output_image = os.path.join(project_root, "screen_som.png")
    
    if not os.path.exists(input_image):
        logger.error("找不到原始截图，请先运行一遍前面的测试采集图片。")
        return
        
    logger.info("开始对截图进行 SoM 处理...")
    mark_dict = processor.generate_som_image(input_image, output_image)
    
    logger.info("处理完成。提取到的控件坐标映射表: ")
    for k, v in mark_dict.items():
        print(f"  [ID: {k}] -> 坐标: {v}")
        
    logger.info("查看根目录的 screen_som.png，看图标是否已被标记")

if __name__ == "__main__":
    main()