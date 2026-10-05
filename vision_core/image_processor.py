import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        logger.info("初始化计算机视觉处理模块 (OpenCV)...")

    def generate_som_image(self, input_path: str, output_path: str) -> dict:
        """
        核心方法：使用 OpenCV 识别屏幕上的图标/按钮，绘制数字标记 (Set-of-Mark)。
        
        Args:
            input_path (str): 原始截图路径。
            output_path (str): 绘制标记后的输出图片路径。
            
        Returns:
            dict: 标记 ID 与其中心点坐标的映射字典。例如: {'1': (x1, y1), '2': (x2, y2)}
        """
        # 1. 读取图片
        img = cv2.imread(input_path)
        if img is None:
            logger.error("无法读取图片: %s", input_path)
            return {}
            
        # 2. 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 3. 边缘检测 (Canny 算法)
        # 这里的阈值(50, 150)可以根据实际车机界面的对比度微调
        edges = cv2.Canny(gray, 50, 150)
        
        # 4. 膨胀操作，让边缘连成完整的轮廓
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # 5. 寻找轮廓
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        mark_dict = {}
        mark_id = 1
        
        for contour in contours:
            # 过滤掉太小（噪点）或太大（整个背景卡片）的轮廓
            area = cv2.contourArea(contour)
            if 500 < area < 50000:
                # 获取该轮廓的边界框 (Bounding Box)
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算中心点坐标
                center_x = x + w // 2
                center_y = y + h // 2
                
                # 记录 ID 和对应的中心坐标
                mark_dict[str(mark_id)] = (center_x, center_y)
                
                # 6. 在图片上绘制矩形框（绿色）和数字 ID（红色背景，白色文字）
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # 绘制数字底色框
                cv2.rectangle(img, (x, y - 20), (x + 30, y), (0, 0, 255), -1)
                # 绘制数字
                cv2.putText(img, str(mark_id), (x + 5, y - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                mark_id += 1
                
        # 7. 保存带有标记的图片
        cv2.imwrite(output_path, img)
        logger.info("SoM 标记图已生成，共识别出 %d 个潜在控件。路径: %s", mark_id - 1, output_path)
        
        return mark_dict