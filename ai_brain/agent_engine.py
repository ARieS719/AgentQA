import os
import time
import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AgentEngine:
    """
    基于 ReAct 架构与视觉锚点 (Anchor-based) 的全自主运行引擎
    """
    def __init__(self, adb_controller, vlm_client, image_processor, max_steps=8):
        self.adb = adb_controller
        self.vlm = vlm_client
        self.processor = image_processor
        self.max_steps = max_steps
        
        self.raw_path = "temp_engine_raw.png"
        self.som_path = "temp_engine_som.png"

    def _parse_llm_json(self, raw_response: str) -> dict:
        try:
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {}
        except Exception as e:
            logger.error("JSON 解析异常: %s", str(e))
            return {}

    def execute_task(self, goal: str, screen_width: int = 1408, screen_height: int = 792) -> bool:
        logger.info("===========================================")
        logger.info(" 启动全自主 Agent 任务: [%s]", goal)
        logger.info("===========================================")

        for step in range(1, self.max_steps + 1):
            logger.info("--- 开始执行第 [%d/%d] 步循环 ---", step, self.max_steps)
            
            if not self.adb.get_screenshot(self.raw_path):
                logger.error("无法获取屏幕状态，任务中止。")
                return False
                
            mark_dict = self.processor.generate_som_image(self.raw_path, self.som_path)
            if not mark_dict:
                logger.warning("当前屏幕未识别到任何控件。")
                continue

            # ================= 核心 Prompt 升级：注入潜意识防御系统 =================
            prompt = f"""
            你是一个完全自主的 GUI UI测试 Agent，具备强大的异常自愈能力。
            你的终极任务目标：【{goal}】。
            
            请观察当前屏幕截图（已附加红色数字标签）。当前可点击的控件 ID 列表：{list(mark_dict.keys())}。
            
            【你的心智模型与操作优先级】
            Priority 1 (异常检测与自愈): 
            首先扫描全局屏幕，检查是否有突发的、阻挡主界面的模态弹窗（如“低电量警告”、“权限申请(Allow/Deny)”、“应用崩溃提示”、“系统更新”、“广告遮挡”等）。
            如果发现这类干扰物，你的【最高优先级】是消除它！此时你需要去点击弹窗上的“关闭/取消/拒绝/Allow/稍后”等按钮。
            
            Priority 2 (主线任务): 
            如果屏幕干净，没有干扰弹窗，请继续推理如何推进你的终极任务目标。
            
            【你的可用动作 (Action)】
            1. TAP: 点击某个具体的控件（不管是点主线目标，还是点关闭弹窗的按钮，都用这个）。
            2. SWIPE_DOWN: 向下滚动页面 (手指从下往上划)。必须提供你要滑动的区域内的一个控件 ID 作为锚点。
            3. SWIPE_UP: 向上滚动页面 (手指从上往下划)。锚点规则同上。
            4. DONE: 终极目标已完全达成。
            5. FAIL: 尝试了所有办法仍无法达成任务，主动放弃。
            
            【严格输出要求】
            必须且只能返回一个 JSON 格式数据：
            {{
                "anomaly_detected": true 或 false (布尔值，代表你是否发现了阻碍主线的突发弹窗),
                "thought": "你的思考过程。描述你看到了什么，有没有异常？为了自愈或推进主线，你要干什么？",
                "action": "TAP 或 SWIPE_DOWN 或 SWIPE_UP 或 DONE 或 FAIL",
                "target_id": "对应的数字标签 (TAP 和 SWIPE 动作都必须填入！)"
            }}
            """
            # ===================================================
            
            logger.info("向大脑发送环境上下文，请求动作决策...")
            raw_response = self.vlm.analyze_screen(self.som_path, prompt)
            decision = self._parse_llm_json(raw_response)
            
            if not decision:
                logger.error("决策数据解析异常，原始回复: %s", raw_response)
                continue

            # 解析新增的潜意识防御字段
            has_anomaly = decision.get("anomaly_detected", False)
            thought = decision.get("thought", "无思考过程")
            action = decision.get("action", "")
            target_id = str(decision.get("target_id", ""))

            if has_anomaly:
                logger.warning(" [警报] AI 潜意识检测到异常干扰物！触发自愈逻辑！")
                
            logger.info(" AI 思考过程: %s", thought)
            logger.info(" AI 决定动作: %s %s", action, f"(锚点/目标 ID: {target_id})" if target_id else "")

            # 3. 执行动作
            if action == "DONE":
                logger.info(" AI 判定任务成功闭环！")
                return True
            elif action == "FAIL":
                logger.warning(" AI 判定任务无法完成。")
                return False
            elif action == "TAP":
                if target_id in mark_dict:
                    x, y = mark_dict[target_id]
                    logger.info("执行精准点击，坐标: (X:%d, Y:%d)", x, y)
                    self.adb.tap(x, y)
                    time.sleep(3)
                else:
                    logger.error("无效的 ID [%s]", target_id)
            
            # ================= 滑动动作的智能改造 =================
            elif action in ["SWIPE_DOWN", "SWIPE_UP"]:
                if target_id in mark_dict:
                    # 获取 AI 指定的锚点坐标
                    anchor_x, anchor_y = mark_dict[target_id]
                    logger.info(" AI 聪明地选择了 ID [%s] 作为滑动区域锚点，已锁定 X 轴为: %d", target_id, anchor_x)
                    
                    # 以锚点的 X 轴为中心进行滑动，Y 轴跨度保持屏幕的 75% 到 25% 
                    # 这样就完美实现了“指哪列，滑哪列”
                    y_start = int(screen_height * 0.75) if action == "SWIPE_DOWN" else int(screen_height * 0.25)
                    y_end = int(screen_height * 0.25) if action == "SWIPE_DOWN" else int(screen_height * 0.75)
                    
                    self.adb.swipe(anchor_x, y_start, anchor_x, y_end, duration=800)
                    time.sleep(3) 
                else:
                    logger.error("AI 想要滑动，但提供的区域锚点 ID [%s] 无效！", target_id)
            # ===================================================
            else:
                logger.error("不受支持的动作指令: %s", action)
                
        logger.error("触达引擎最大步数阈值 (%d)，防死循环熔断触发。", self.max_steps)
        return False