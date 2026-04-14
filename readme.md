# YunNai-Kernel

云奈内核是一个基于 Python 的智能代理系统框架，提供 **IPC 通信**、**AI 聊天**、**插件扩展**、**MCP 能力集成**等核心功能，适用于自动化任务处理和智能交互场景。

---

## 设计亮点

### 1. 模块化架构设计

项目采用**组件化架构**，将核心功能分解为独立模块，每个模块职责清晰，便于维护和扩展：

```
src/
├── components/     # 核心组件层
│   ├── ai_chat/     # AI聊天组件
│   ├── ipc/         # 进程间通信
│   ├── mcp/         # MCP管理器
│   ├── logger/      # 日志系统
│   └── plugin_manager.py  # 插件管理器
├── model_adapters/  # 多模型适配器
├── plugins/         # 插件目录
└── types/           # 类型定义
```

**设计优势**：
- 模块间低耦合、高内聚
- 易于单元测试和集成测试
- 支持独立模块的热更新和替换

---

### 2. 插件化架构与生命周期钩子

#### 插件系统设计

```python
class PluginManager:
    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self.hook_registry_map: dict[Hooks, list[Plugin]] = {}
```

**核心特性**：
- **动态加载**：插件通过配置文件声明，运行时自动加载
- **Hook 机制**：支持在应用生命周期的关键节点注入逻辑
- **命名冲突处理**：同名插件自动检测和警告

#### 生命周期钩子定义

| Hook 名称 | 触发时机 | 用途 |
|-----------|----------|------|
| `on_app_before_initialize` | 应用初始化前 | 插件初始化准备 |
| `on_app_after_initialized` | 应用初始化后 | 插件启动逻辑 |
| `on_message_before_send` | 消息发送前 | 消息预处理、拦截 |
| `on_message_after_sended` | 消息发送后 | 消息后处理 |
| `on_llm_response` | LLM响应时 | 响应流处理 |
| `on_app_will_close` | 应用关闭前 | 资源清理 |

---

### 3. MCP（Model Context Protocol）集成

**设计亮点**：

#### 多 MCP 服务管理
```python
class MCPManager:
    def __init__(self):
        self.mcp_infos: dict[str, MCPInfo] = {}  # MCP信息注册表
        self.tools: dict[str, list[Tool]] = {}    # 工具缓存
```

#### 动态激活机制
- **按需激活**：MCP服务在首次使用时激活，减少启动时间
- **会话管理**：每个MCP维护独立会话，支持连接复用
- **错误隔离**：单个MCP失败不影响其他服务

#### 支持多种 MCP 类型
| 类型 | 配置方式 | 示例 |
|------|----------|------|
| 本地进程 | `cmd` + `args` | 微信机器人 MCP |
| 远程 HTTP | `url` + `headers` | WebSearch MCP |

---

### 4. IPC 通信机制

#### 双模式通信设计

**事件模式（Event）** - 单向通知：
```python
async def emit(self, name: str, **arguments):
    """发送事件到服务端（单向通信）"""
```

**调用模式（Invoke）** - 请求/响应：
```python
async def invoke(self, name: str, **arguments) -> dict:
    """调用服务端方法并等待响应"""
```

#### 高级特性

- **超时机制**：默认 10 秒超时，自动清理过期请求
- **心跳检测**：内置 `ping/pong` 心跳，保持连接活性
- **异步处理**：支持同步和异步处理器，自动识别协程

---

### 5. AI 聊天系统

#### 多模型适配

项目支持多种主流大语言模型的无缝切换：

| 模型 | API 提供商 | 配置名称 |
|------|------------|----------|
| Qwen3.6-plus | 阿里云通义千问 | `Qwen3.6-plus` |
| Kimi K2 | Moonshot | `kimi-k2-thinking` |
| Doubao 1.5 Pro | 字节跳动豆包 | `doubao-1-5-pro-32k` |

#### 双响应模式

```python
async def stream_response(self, state: ChatState):
    """流式响应 - 实时返回token"""

async def non_stream_response(self, state: ChatState) -> ChatCompletion:
    """非流式响应 - 等待完整结果"""
```

#### 双层 Prompt 架构

```python
params = {
    "messages": [
        {"role": "system", "content": state.fixed_sys_prompt},   # 固定系统提示
        *state.messages,
        {"role": "system", "content": state.dynamic_sys_prompt}  # 动态上下文提示
    ]
}
```

**设计意图**：
- **固定 Prompt**：定义角色定位和基础规则
- **动态 Prompt**：注入 MCP 工具列表、系统信息、时间等运行时数据

---

### 6. 异步事件循环架构

```python
class Application:
    def __init__(self):
        self.thread_executor = ThreadPoolExecutor(workers)  # CPU密集型任务
        self.event_loop = asyncio.new_event_loop()          # 异步事件循环
```

**并发模型**：
- **异步 I/O**：网络请求、IPC通信使用 asyncio
- **线程池**：CPU密集型任务提交到线程池执行
- **任务调度**：通过 `run_in_executor` 实现同步/异步协作

---

### 7. 配置化管理

#### YAML 配置结构

```yaml
system:
  thread_workers: 4              # 线程池大小
  ipc_option:
    protocol: "ws"
    host: "192.168.1.102"
    port: 6600

llm:
  default: "Qwen3.6-plus"
  models:
    "Qwen3.6-plus":
      base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
      key_name: "DASHSCOPE_API_KEY"

capabilities:
  mcp:
    enable: true
    servers:
      "wxauto":
        enable: true
        cmd: "python.exe"
        args: ["-m", "wxauto_mcp.server"]
```

**配置特点**：
- **环境变量注入**：API Key 通过 `.env` 文件管理
- **模板引用**：支持 YAML 锚点复用配置片段
- **分层覆盖**：支持命令行参数覆盖配置文件

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
DASHSCOPE_API_KEY=your_dashscope_key
KIMI_API_KEY=your_kimi_key
DOUAO_API_KEY=your_doubao_key
```

### 启动应用

```bash
python main.py ipc_uri=ws://localhost:6600
```

---

## 项目结构

```
yunnai-kernel/
├── .vscode/              # VSCode 配置
├── prompts/              # 提示词模板
│   ├── agent.md          # 代理角色提示
│   └── chat_neko_girl.md # 角色示例
├── src/
│   ├── common/           # 公共工具
│   ├── components/       # 核心组件
│   │   ├── ai_chat/      # AI聊天模块
│   │   ├── app_config/   # 配置管理
│   │   ├── ipc/          # IPC通信
│   │   ├── ipc_handlers/ # IPC处理器
│   │   ├── logger/       # 日志系统
│   │   ├── mcp/          # MCP管理器
│   │   └── plugin_manager.py
│   ├── model_adapters/   # 模型适配器
│   ├── plugins/          # 插件目录
│   │   ├── session_plugin/
│   │   └── wxauto_plugin/
│   ├── types/            # 类型定义
│   ├── utils/            # 工具函数
│   └── application.py    # 应用入口
├── .gitignore
├── app_config.yaml       # 应用配置
├── main.py               # 启动脚本
└── readme.md             # 项目文档
```

---

## 核心组件说明

| 组件 | 职责 | 完成度 |
|------|------|--------|
| 异步事件循环 | 协程调度 | 100% |
| IPC 服务 | 进程间通信 | 100% |
| LLM 客户端 | 多模型适配 | 100% |
| MCP 管理器 | 能力扩展 | 90% |
| 插件系统 | 生命周期钩子 | 100% |

---

## 开发规范

- **类型注解**：所有函数和方法必须添加类型注解
- **错误处理**：使用 try-except 包裹可能抛出异常的代码
- **日志记录**：关键流程必须记录日志（info/debug/error）
- **异步优先**：I/O 操作优先使用异步实现

---

## 许可证

MIT License