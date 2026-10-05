import sys
import os

# 将项目根目录加入环境路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from ai_brain.vlm_client import VLMClient

def main():
    # 安全实践：优先从环境变量读取，如果没有则提示用户填入
    SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your_api_key_here")
    
    # 检查是否真的获取到了有效的 Key，如果没有则阻断运行并提醒
    if SILICONFLOW_API_KEY == "your_api_key_here":
        print("错误：未检测到 API Key！")
        print("请在环境变量中配置 SILICONFLOW_API_KEY，或在此代码中临时填入。")
        return

    # 1. 实例化 AI 大脑
    vlm = VLMClient(api_key=SILICONFLOW_API_KEY)

    # 2. 读取第一阶段我们截取的车机屏幕
    image_path = os.path.join(project_root, "screen_before.png")
    
    # 确保图片文件存在，避免报错
    if not os.path.exists(image_path):
        print(f"错误：找不到图片文件 {image_path}，请确认是否已成功截图。")
        return

    # 3. 设定我们的测试提问 (Prompt)
    prompt = "你现在是一个资深的汽车测试工程师。请仔细观察这张车机屏幕截图，告诉我屏幕上都有哪些主要的应用图标或可点击的控件？请用简练的列表形式回答。"

    print(f"\n正在向云端大模型发送截图并提问...")
    print(f"提问内容: {prompt}\n")
    
    try:
        # 4. 获取并打印结果
        answer = vlm.analyze_screen(image_path, prompt)
        print("=== AI 大脑的观察结果 ===")
        print(answer)
        print("========================")
    except Exception as e:
        print(f"请求失败，错误信息: {e}")

if __name__ == "__main__":
    main()