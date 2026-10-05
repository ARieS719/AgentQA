import subprocess
import os
import logging
import threading
import time

logger = logging.getLogger(__name__)

class AdbController:
    def __init__(self):
        logger.info("初始化 ADB 控制器...")
        try:
            self.run_adb_cmd(["version"])
        except Exception as e:
            logger.error("ADB 初始化失败: %s", str(e))
            
        self.record_process = None

    def run_adb_cmd(self, args: list) -> str:
        cmd = ["adb"] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error("ADB 命令执行失败: %s", e.stderr)
            raise

    def get_screenshot(self, save_path: str) -> bool:
        try:
            self.run_adb_cmd(["shell", "screencap", "-p", "/sdcard/temp_screen.png"])
            self.run_adb_cmd(["pull", "/sdcard/temp_screen.png", save_path])
            self.run_adb_cmd(["shell", "rm", "/sdcard/temp_screen.png"])
            logger.debug("截图已成功采集并保存至: %s", save_path)
            return True
        except Exception as e:
            logger.error("屏幕截图采集失败: %s", str(e))
            return False

    def tap(self, x: int, y: int) -> None:
        logger.info("执行硬件级点击动作，坐标：(%d, %d)", x, y)
        self.run_adb_cmd(["shell", "input", "tap", str(x), str(y)])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> None:
        logger.info("执行硬件级滑动动作: 起点(%d, %d) -> 终点(%d, %d), 耗时: %dms", x1, y1, x2, y2, duration)
        self.run_adb_cmd(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])

    # ================= 新增：多线程高能录屏支持 =================
    def start_screen_record(self, remote_path: str = "/sdcard/perf_record.mp4") -> None:
        """
        开启子线程在后台默默录屏。
        增加延时，确保录屏服务在车机端完全拉起。
        """
        logger.info(" 启动后台录屏守护线程...")
        cmd = ["adb", "shell", "screenrecord", "--bit-rate", "4000000", remote_path]
        
        # 使用 Popen 启动异步进程，不阻塞主线程
        self.record_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 给车机底层一点时间启动 MediaCodec
        time.sleep(2) 

    def stop_and_pull_record(self, local_path: str, remote_path: str = "/sdcard/perf_record.mp4") -> bool:
        """
        终止录屏并将视频拉取到本地用于性能分析
        """
        logger.info(" 发送终止录屏信号 (SIGINT)...")
        if self.record_process:
            # 优雅地杀死 screenrecord 进程，让它保存 MP4 的尾部结构 (moov atom)
            self.run_adb_cmd(["shell", "pkill", "-2", "screenrecord"])
            self.record_process = None
            
            # 视频编码落盘需要一点时间
            time.sleep(2)
            
            try:
                logger.info(" 正在将性能监控视频拉取至本地分析引擎...")
                self.run_adb_cmd(["pull", remote_path, local_path])
                self.run_adb_cmd(["shell", "rm", remote_path])
                logger.info("视频拉取成功: %s", local_path)
                return True
            except Exception as e:
                logger.error("拉取性能监控视频失败: %s", str(e))
                return False
        return False