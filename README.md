# AgentQA: 基于纯视觉与 VLM 的具身智能 UI 自动化中台

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Architecture](https://img.shields.io/badge/Architecture-ReAct-orange)
![CV](https://img.shields.io/badge/CV-OpenCV-green)

##  背景与痛点
传统的 UI 自动化测试（如 Appium/UIAutomator）长期受制于两大工程痛点：
1. **强依赖底层 DOM 树**：一旦前端重构或采用自渲染引擎（如 Flutter/游戏/某些车载车机系统），控件树提取将直接失效。
2. **脚本维护成本极高**：采用硬编码（Hardcode）的线性脚本，页面元素的微小变动或突发的系统弹窗都会导致测试链路熔断。

**AgentQA** 是一款摒弃底层控件依赖、完全基于“纯视觉感知”与“大模型推理”构建的无脚本（Scriptless）自动化测试中台。它通过赋予系统“独立心智”，实现了像人类一样的看图推理与容错操作。

##  核心架构与工程创新

本项目在架构上进行了严格的职责解耦，核心技术壁垒如下：

### 1. 动态状态机驱动 (ReAct Framework)
彻底废弃 `find_element().click()` 模式。以自然语言下发宏观目标，系统自主执行 `截图感知 -> 视觉打标 -> 推理规划 (Thought) -> 动作输出 (Action)` 的闭环状态机。测试用例完全自然语言化。

### 2. 零坐标幻觉的空间定位 (Set-of-Mark)
针对多模态大模型（VLM）普遍存在的坐标输出漂移问题，在视觉层引入 SoM 技术。利用 OpenCV 算法在渲染层识别有效交互区域并分配唯一标识 ID。VLM 仅输出逻辑 ID，物理引擎逆向映射绝对像素坐标，实现 **100% 像素级精准交互**。

### 3. 视觉锚点机制 (Anchor-based Interaction)
针对复杂多栏列表（如车载设置左右分屏）的滑动痛点，独创锚点滑动算法。Agent 可基于视觉感知，动态指定屏幕特定控件作为“锚点”，物理驱动层锁定对应 X/Y 轴执行局部滑动。

### 4. 潜意识异常自愈 (Self-Healing)
告别脆弱的 `try-catch` 穷举。在 Prompt 中抽象双优先级心智模型：系统在每次决策前进行环境安全扫描，遭遇突发干扰（如权限请求、低电量弹窗）时，自主挂起主线任务，执行弹窗消除后动态恢复上下文，大幅提升无人值守测试的鲁棒性。

### 5. 视频流 E2E 性能基准测试
不仅验证功能正确性，同时量化渲染性能。通过 ADB 守护进程开启多线程后台录屏，结合 OpenCV 巴氏距离 (Bhattacharyya distance) 与帧差分析，自动化提取冷热启动与转场动画的精确耗时（毫秒级）。

##  工程模块职责
- `ai_brain/`: 决策中枢，封装 VLM 交互与 ReAct 状态机推理逻辑。
- `vision_core/`: 视觉引擎，集成 OpenCV 落地 SoM 打标与 E2E 帧差耗时分析。
- `device_control/`: 硬件驱动层，实现异步 ADB 控制、锚点精准触控与录屏。
- `tests/`: 业务测试入口，包含主线业务探索流与性能打靶测试。

##  极速启动

1. **环境准备**：配置 Python 3.9+ 及有效连接的 ADB 设备。
2. **安装依赖**：`pip install opencv-python requests numpy`
3. **注入密钥**：在入口文件中配置环境变量 `SILICONFLOW_API_KEY`。
4. **触发执行**：运行 `python tests/test_agentic_workflow.py` 开启自动化探索。