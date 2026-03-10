# 云奈智能助手 (Yunnai Agent)

一个基于大语言模型的智能桌面助手应用，支持语音唤醒、语音识别、文本转语音等功能。

## 项目架构

项目采用前后端分离架构：

- **后端**：Python + 异步I/O
- **前端**：Vue 3 + TypeScript + Tauri 2
- **通信**：WebSocket IPC 服务

```
yunnai-agent/
├── src/                      # Python 后端源码
│   ├── application.py       # 应用核心类
│   ├── application_tools/   # 应用工具集
│   ├── components/          # 基础组件
│   │   ├── logger/          # 日志组件
│   │   └── ipc_handlers/    # IPC 处理器
│   ├── core/                # 核心模块
│   │   ├── ai_chat/         # AI 聊天模块
│   │   ├── ipc/             # IPC 通信模块
│   │   ├── plugin_manager.py # 插件管理器
│   │   └── ui_process.py    # UI 进程管理
│   ├── plugins/             # 插件模块
│   │   ├── wakeup_plugin/   # 语音唤醒插件
│   │   ├── asr_plugin/      # 语音识别插件
│   │   ├── tts_plugin/      # 文本转语音插件
│   │   └── tools_plugin/    # 工具插件
│   └── types/               # 类型定义
├── yunnai-ui/               # Vue 3 前端项目
│   ├── src/                 # 前端源码
│   └── src-tauri/           # Tauri Rust 代码
├── tools/                   # 工具模块
├── main.py                  # 程序入口
├── app_config.json          # 应用配置
└── tools.json               # 工具配置
```

## 功能特性

- **语音唤醒**：使用 Porcupine 引擎实现关键词唤醒
- **语音识别**：实时语音转文字
- **文本转语音**：自然流畅的语音合成
- **AI 对话**：集成大语言模型进行智能对话
- **插件系统**：可扩展的插件架构
- **工具调用**：支持文件操作、音乐播放等工具
- **桌面界面**：基于 Tauri + Vue 3 的现代 GUI

## 环境要求

- Python 3.8+
- Node.js 18+
- Rust 1.70+ (用于 Tauri)
- pnpm (推荐的包管理器)

## 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# 大语言模型 API 配置
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 语音唤醒配置
PORCUPINE_ACCESSKEY=your_porcupine_access_key

# IPC 服务配置
IPC_HOST=127.0.0.1
IPC_PORT=8765

# UI 配置
UI_COMMAND=npm run tauri dev
UI_CWD=yunnai-ui
UI_PORT=5173
```

## 安装与运行

### 1. 克隆项目

```bash
git clone https://github.com/MuseHanzhi/yunnai-agent.git
cd yunnai-agent
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd yunnai-ui
pnpm install
cd ..
```

### 4. 运行项目

```bash
python main.py
```

## 插件系统

项目支持多种插件，默认包含以下插件：

### WakeupPlugin (语音唤醒)
使用 Porcupine 引擎监听关键词唤醒。

### ASRPlugin (语音识别)
自动语音识别，将语音转换为文本。

### TTSPlugin (文本转语音)
将文本转换为自然语音输出。

### ToolsPlugin (工具插件)
提供各种工具调用能力，如文件操作、音乐播放等。

## 核心类说明

### Application (src/application.py:17)
应用核心类，负责：
- 事件循环管理
- 插件管理与触发
- IPC 服务端
- UI 进程管理
- LLM 会话管理

### PluginManager (src/core/plugin_manager.py:22)
插件管理器，提供：
- 插件注册与移除
- 插件生命周期管理
- 事件触发机制

## 开发指南

### 添加新插件

1. 在 `src/plugins/` 目录下创建新插件目录
2. 继承 `Plugin` 基类
3. 实现需要的生命周期方法
4. 在 `main.py` 中注册插件

### 添加新工具

1. 在 `tools/` 目录下添加工具模块
2. 在 `tools.json` 中配置工具定义
3. 在 `ToolsPlugin` 中注册工具

## 技术栈

### 后端
- Python 3.8+
- asyncio (异步编程)
- OpenAI SDK (LLM 交互)
- Porcupine (语音唤醒)

### 前端
- Vue 3
- TypeScript
- Tauri 2
- Vite
- Naive UI
- Pinia (状态管理)
- Vue Router

## 许可证

本项目采用 MIT 许可证。
