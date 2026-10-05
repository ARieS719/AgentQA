import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """
    企业级 E2E 性能分析引擎。
    通过处理录屏视频流，分析应用冷启动、热启动及转场动画的精确耗时。
    """
    def __init__(self, similarity_threshold=0.99):
        # 相似度阈值，大于 0.99 认为两帧画面完全静止（渲染结束）
        self.similarity_threshold = similarity_threshold

    def _calculate_image_similarity(self, img1, img2) -> float:
        """
        使用直方图比对法，极速计算两帧图片的相似度
        """
        # 转为灰度图以加速计算
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        
        # 使用巴氏距离 (Bhattacharyya distance)
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return similarity

    def analyze_transition_time(self, video_path: str, fps: int = 30) -> float:
        """
        分析转场耗时
        返回：从画面开始变化，到画面彻底静止所经历的时间（秒）
        """
        logger.info(" 启动视频流分析引擎，解析目标文件: %s", video_path)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("无法打开视频文件，请检查路径。")
            return -1.0

        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        # 如果读取不到正常帧率，使用经验值兜底
        if actual_fps <= 0 or actual_fps > 120:
            actual_fps = fps 
            
        logger.info("视频实际帧率: %.2f FPS", actual_fps)

        frame_count = 0
        prev_frame = None
        
        start_change_frame = -1
        stable_frame = -1
        
        # 连续稳定帧计数器 (容错机制：连续 5 帧相似才算彻底静止)
        continuous_stable_count = 0 
        required_stable_frames = 5 

        while True:
            ret, current_frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            if prev_frame is not None:
                similarity = self._calculate_image_similarity(prev_frame, current_frame)
                
                # 状态机：寻找画面【开始变化】的第一帧
                if start_change_frame == -1 and similarity < self.similarity_threshold:
                    start_change_frame = frame_count
                    logger.debug("检测到界面开始变化，起始帧: %d", start_change_frame)
                
                # 状态机：在画面变化后，寻找画面【重新归于平静】的那一帧
                if start_change_frame != -1 and stable_frame == -1:
                    if similarity >= self.similarity_threshold:
                        continuous_stable_count += 1
                        if continuous_stable_count >= required_stable_frames:
                            # 减去为了容错多算的这几帧
                            stable_frame = frame_count - required_stable_frames 
                            logger.debug("检测到界面渲染彻底完成，稳定帧: %d", stable_frame)
                            break # 找到了，提前结束循环
                    else:
                        continuous_stable_count = 0 # 动画还在动，计数器重置

            prev_frame = current_frame

        cap.release()

        if start_change_frame != -1 and stable_frame != -1:
            frames_elapsed = stable_frame - start_change_frame
            time_elapsed = frames_elapsed / actual_fps
            logger.info(" 性能解析完成！转场动画总耗时: [%.3f 秒] (历经 %d 帧)", time_elapsed, frames_elapsed)
            return time_elapsed
        else:
            logger.warning("未能在这段视频中检测到完整的转场生命周期（可能画面一直静止，或者动画一直没结束）。")
            return -1.0