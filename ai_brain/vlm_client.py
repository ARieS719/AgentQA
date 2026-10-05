from openai import OpenAI
import base64
import os
import json
import re
import logging

# 配置该模块的专属 Logger
logger = logging.getLogger(__name__)

class VLMClient:
    def __init__(self, api_key):
        logger.info("初始化 VLM (视觉大模型) 客户端...")
        # 配置硅基流动的专属 API 网关地址
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        # 指定硅基流动平台上极其强大的视觉模型 Qwen/Qwen3-VL-32B-Instruct
        self.model_name = "Qwen/Qwen3-VL-32B-Instruct"

    def _encode_image_to_base64(self, image_path):
        """
        本地图片不能直接传网址，必须转成底层 Base64 字符串发给大模型
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_screen(self, image_path, prompt):
        """
        核心方法：向大模型发送图片和指令，并返回模型的回答
        """
        if not os.path.exists(image_path):
            logger.error("找不到图片: %s", image_path)
            raise FileNotFoundError(f"找不到图片: {image_path}")

        base64_image = self._encode_image_to_base64(image_path)
        
        # 构造多模态请求结构
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            # 拼接为 Data URI 格式
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        # 发送请求给硅基流动
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1024,
                temperature=0.1 # 测试场景下，temperature 设低一点，让 AI 的回答更确切、不发散
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("向 VLM 引擎发送请求失败: %s", str(e))
            raise

    def find_element_coordinates(self, image_path, target_name, width=1408, height=792):
        """
        进阶能力：寻找指定元素的精确坐标 (加入了防崩溃正则解析与边界限制)
        """
        # 优化 Prompt：明确告知最大边界，并要求使用更简单的 [x, y] 数组格式代替容易出错的 JSON
        prompt = f"""
        你是一个精准的UI自动化定位引擎。当前车机屏幕分辨率为：宽 {width}，高 {height}。
        任务：请在截图中寻找【{target_name}】的中心点像素坐标。
        注意：X 坐标绝对不能超过 {width}，Y 坐标绝对不能超过 {height}！
        
        要求：你的回答只能是一个坐标数组，格式必须严格为 [X, Y]。绝对不要包含任何其他说明文字！
        返回示例：[550, 750]
        """
        
        logger.info("请求 AI 寻找目标元素【%s】的坐标...", target_name)
        raw_response = self.analyze_screen(image_path, prompt)
        logger.debug("AI 原始回复: %s", raw_response)
        
        try:
            # 工程兜底：使用强大的正则表达式，不管 AI 穿什么马甲，强行抠出里面的数字！
            # \d+ 表示匹配连续的数字
            numbers = re.findall(r'\d+', raw_response)
            
            if len(numbers) >= 2:
                x = int(numbers[0])
                y = int(numbers[1])
                
                # 边界校验兜底：防止大模型胡说八道超出屏幕
                if x > width or y > height:
                    logger.warning("警告：AI 返回的坐标 (%d, %d) 超出屏幕边界！将尝试点击边缘。", x, y)
                    x = min(x, width - 10)
                    y = min(y, height - 10)
                    
                return x, y
            else:
                logger.error("解析坐标失败，AI 没有返回足够的数字。")
                return -1, -1
        except Exception as e:
            logger.error("坐标正则提取异常: %s", str(e))
            return -1, -1

    def find_element_by_som_id(self, som_image_path: str, target_name: str) -> str:
        """
        终极定位方案 (SoM)：让大模型看带有数字标签的图，只返回目标对应的数字 ID。
        """
        prompt = f"""
        你是一个精准的UI自动化定位引擎。请仔细观察这张【带有红色数字标签】的车机屏幕截图。
        任务：我需要点击【{target_name}】，请告诉我它上面标注的红色数字是几？
        
        严格要求：
        你的回答只能是一个纯数字，绝对不要包含任何标点符号、解释性文字或其他内容。
        示例回答：5
        """
        
        logger.info("请求 AI 寻找目标元素【%s】对应的数字标签...", target_name)
        raw_response = self.analyze_screen(som_image_path, prompt)
        logger.info("AI 原始回复 (目标 ID): %s", raw_response)
        
        try:
            # 同样使用正则进行防御性提取，只抓取里面的数字
            numbers = re.findall(r'\d+', raw_response)
            if numbers:
                # 返回提取到的第一个数字
                return str(numbers[0]) 
            else:
                logger.error("提取数字 ID 失败，AI 未返回有效数字。")
                return "-1"
        except Exception as e:
            logger.error("提取数字 ID 异常: %s", str(e))
            return "-1"

    def assert_screen_state(self, image_path: str, expected_state: str) -> bool:
        """
        基于视觉大模型的状态断言 (Assertion)。
        通过语义理解验证界面是否流转到了预期状态。
        """
        prompt = f"""
        你是一个严谨的自动化测试断言引擎。
        任务：请观察提供的屏幕截图，验证当前界面状态是否符合预期：【{expected_state}】。
        
        严格输出要求：
        1. 如果界面状态符合预期，请仅输出大写单词 "TRUE"。
        2. 如果界面状态不符合预期，请仅输出大写单词 "FALSE"。
        3. 绝对不要输出任何标点符号、解释性文字或其他字符。
        """
        
        logger.info("向 VLM 引擎发起状态断言请求，预期状态: [%s]", expected_state)
        raw_response = self.analyze_screen(image_path, prompt)
        
        try:
            # 清理字符串两端的空格和换行符，并转为大写比对
            result = raw_response.strip().upper()
            if "TRUE" in result:
                logger.info("视觉断言通过 (Pass)。")
                return True
            elif "FALSE" in result:
                logger.error("视觉断言失败 (Fail)。")
                return False
            else:
                logger.warning("视觉断言解析异常: VLM 返回了非标准结果 [%s]。", result)
                return False
        except Exception as e:
            logger.error("执行视觉断言处理时发生异常: %s", str(e))
            return False