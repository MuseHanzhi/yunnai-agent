# 插件开发指南

## 概述

YunNai-Kernel 提供了强大的插件系统，允许开发者通过插件扩展系统功能。插件可以监听应用生命周期的关键节点，并在这些节点注入自定义逻辑。

## 插件结构

### 目录结构

```
src/plugins/
├── your_plugin/           # 插件目录（建议使用小写+下划线命名）
│   ├── __init__.py        # 可选，用于模块导出
│   ├── your_plugin.py     # 插件主类文件
│   ├── services/          # 服务类目录（可选）
│   ├── utils/             # 工具函数目录（可选）
│   └── config.yaml        # 插件配置文件（可选）
└── plugin.py              # 插件基类
```

### 插件基类

所有插件必须继承自 `Plugin` 基类：

```python
from src.plugins.plugin import Plugin
from src.types.lfecycle_hooks import Hooks

class YourPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="your-plugin",    # 插件名称，唯一标识
            version="1.0",         # 版本号
            desc="插件描述"        # 插件描述
        )
        # 注册需要监听的钩子
        self.hook_registry = [
            "on_app_before_initialize",
            "on_ready",
            "on_message_before_send"
        ]
```

## 生命周期钩子

### 钩子列表

| 钩子名称                       | 触发时机   | 参数                  | 用途             |
| -------------------------- | ------ | ------------------- | -------------- |
| `on_app_before_initialize` | 应用初始化前 | `app`, `event_loop` | 获取应用实例，初始化插件资源 |
| `on_app_after_initialized` | 应用初始化后 | `event_loop`        | 启动插件服务         |
| `on_ready`                 | 应用就绪   | 无                   | 执行最终初始化        |
| `on_message_before_send`   | 消息发送前  | `state`             | 消息预处理、拦截、修改    |
| `on_message_after_sended`  | 消息发送后  | `state`             | 消息后处理、记录       |
| `on_llm_response`          | LLM响应时 | `chat_completion`   | 处理流式响应         |
| `on_app_will_close`        | 应用关闭前  | 无                   | 资源清理           |

### 钩子实现示例

```python
from typing import TYPE_CHECKING
import asyncio

from src.components.ai_chat.chat_state import ChatState
from src.plugins.plugin import Plugin

if TYPE_CHECKING:
    from src.application import Application

class ExamplePlugin(Plugin):
    def __init__(self):
        super().__init__("example-plugin", desc="示例插件")
        self.app: "Application | None" = None
        self.hook_registry = [
            "on_app_before_initialize",
            "on_message_before_send",
            "on_llm_response",
            "on_app_will_close"
        ]
    
    def on_app_before_initialize(self, app: "Application", event_loop: asyncio.AbstractEventLoop):
        """应用初始化前，获取应用实例"""
        self.app = app
        # 初始化插件资源
        self._init_resources()
    
    def on_message_before_send(self, state: ChatState):
        """消息发送前，可以修改消息内容"""
        # 添加自定义系统提示
        if state.dynamic_sys_prompt:
            state.dynamic_sys_prompt += "\n" + self._get_custom_prompt()
        else:
            state.dynamic_sys_prompt = self._get_custom_prompt()
    
    def on_llm_response(self, chat_completion):
        """处理LLM响应"""
        if isinstance(chat_completion, ChatCompletionChunk):
            content = chat_completion.choices[0].delta.content
            # 处理流式响应
            self._handle_stream_content(content)
        else:
            content = chat_completion.choices[0].message.content
            # 处理完整响应
            self._handle_complete_content(content)
    
    def on_app_will_close(self):
        """应用关闭前，清理资源"""
        self._cleanup_resources()
    
    def _init_resources(self):
        """初始化插件资源"""
        pass
    
    def _get_custom_prompt(self) -> str:
        """获取自定义系统提示"""
        return "你是一个示例插件添加的提示"
    
    def _handle_stream_content(self, content: str):
        """处理流式响应内容"""
        pass
    
    def _handle_complete_content(self, content: str):
        """处理完整响应内容"""
        pass
    
    def _cleanup_resources(self):
        """清理插件资源"""
        pass
```

## 插件通信

### 插件间通信

插件可以通过 `emit` 方法与其他插件通信：

```python
# 在插件A中定义可被调用的方法
def emit(self, name: str, arguments: dict) -> Any:
    if name == "get_data":
        return self._get_internal_data()
    if name == "set_config":
        self._update_config(arguments)
        return {"status": "success"}
```

```python
# 在插件B中调用插件A的方法
result = self.app.plugin_manager.emit("plugin-a", "get_data", {})
```

### 访问应用实例

通过 `on_app_before_initialize` 钩子获取应用实例后，可以访问应用的核心组件：

```python
def on_app_before_initialize(self, app: "Application", event_loop):
    self.app = app
    
    # 访问AI聊天客户端
    ai_client = app.ai_client
    
    # 访问MCP管理器
    mcp_manager = app.mcp_manager
    
    # 访问插件管理器
    plugin_manager = app.plugin_manager
    
    # 访问IPC服务器
    ipc_server = app.ipc
    
    # 访问事件循环
    self.event_loop = event_loop
```

## 配置与加载

### 配置文件

在 `app_config.yaml` 中配置插件：

```yaml
plugin_config:
  base_module: "src.plugins"  # 插件基础模块路径
  plugins:
    - 
      module_path: "your_plugin.your_plugin"  # 插件模块路径
      class_name: "YourPlugin"                # 插件类名（可选）
    - 
      module_path: "another_plugin.another_plugin"
```

### 自动类名推断

如果不指定 `class_name`，系统会自动根据模块路径推断类名：

```
模块路径: "wxauto_plugin.wxauto_plugin"
推断类名: "WxautoPlugin" (下划线转驼峰，首字母大写)
```

## 开发流程

### 1. 创建插件目录

```bash
mkdir -p src/plugins/your_plugin
```

### 2. 创建插件主文件

```python
# src/plugins/your_plugin/your_plugin.py

from typing import TYPE_CHECKING
from src.plugins.plugin import Plugin
from src.components.ai_chat.chat_state import ChatState

if TYPE_CHECKING:
    from src.application import Application

class YourPlugin(Plugin):
    def __init__(self):
        super().__init__("your-plugin", version="1.0", desc="你的插件描述")
        self.app: "Application | None" = None
        self.hook_registry = [
            "on_app_before_initialize",
            "on_ready",
            "on_app_will_close"
        ]
    
    def on_app_before_initialize(self, app: "Application", event_loop):
        self.app = app
        # 初始化逻辑
    
    def on_ready(self):
        # 就绪逻辑
        pass
    
    def on_app_will_close(self):
        # 清理逻辑
        pass
```

### 3. 配置插件

编辑 `app_config.yaml`，添加插件配置：

```yaml
plugin_config:
  plugins:
    - 
      module_path: "your_plugin.your_plugin"
      class_name: "YourPlugin"
```

### 4. 测试插件

启动应用，检查日志确认插件是否成功加载：

```bash
python main.py
```

日志输出示例：

```
INFO - 开始加载插件: src.plugins.your_plugin.your_plugin
INFO - 插件'src.plugins.your_plugin.your_plugin'加载完成
```

## 高级特性

### 异步钩子处理

所有钩子方法都支持异步实现：

```python
async def on_message_before_send(self, state: ChatState):
    # 异步操作
    result = await self._fetch_data()
    state.dynamic_sys_prompt = result
```

### 消息状态修改

在 `on_message_before_send` 钩子中可以修改消息状态：

```python
def on_message_before_send(self, state: ChatState):
    # 修改模型名称
    state.model_name = "custom-model"
    
    # 修改系统提示
    state.fixed_sys_prompt = "自定义系统提示"
    
    # 添加动态提示
    state.dynamic_sys_prompt = "动态上下文信息"
    
    # 取消消息发送
    state.canceled = True
```

### LLM 响应处理

处理流式和非流式响应：

```python
from openai.types.chat import ChatCompletionChunk, ChatCompletion

def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion):
    if not chat_completion.choices:
        return
    
    if isinstance(chat_completion, ChatCompletionChunk):
        # 流式响应 - 实时处理
        content = chat_completion.choices[0].delta.content
        if content:
            self._process_stream(content)
    else:
        # 非流式响应 - 完整处理
        content = chat_completion.choices[0].message.content
        self._process_complete(content)
    
    # 检查响应是否结束
    if chat_completion.choices[0].finish_reason:
        self._on_response_completed()
```

## 最佳实践

### 命名规范

- 插件目录：小写 + 下划线（如 `wxauto_plugin`）
- 插件类名：大驼峰命名（如 `WXAutoPlugin`）
- 插件名称：小写 + 连字符（如 `wechat-plugin`）

### 错误处理

```python
def on_llm_response(self, chat_completion):
    try:
        # 业务逻辑
        content = chat_completion.choices[0].delta.content
    except Exception as ex:
        # 记录日志但不抛出异常，避免影响其他插件
        logger.error(f"处理响应失败: {ex}", exc_info=True)
```

### 资源管理

```python
def on_app_before_initialize(self, app, event_loop):
    self._resource = SomeResource()

def on_app_will_close(self):
    if self._resource:
        self._resource.close()
        self._resource = None
```

### 日志记录

```python
from src.components.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)

class YourPlugin(Plugin):
    def on_ready(self):
        logger.info(f"插件 {self.name} 已就绪")
```

## 示例插件

### 会话管理插件

```python
class SessionPlugin(Plugin):
    def __init__(self):
        super().__init__("session-plugin", desc="管理会话")
        self.chat_records = []
        self.hook_registry = [
            "on_message_before_send",
            "on_message_after_sended",
            "on_llm_response"
        ]
    
    def on_message_before_send(self, state: ChatState):
        # 将历史记录注入到消息中
        state.messages = self.chat_records
    
    def on_message_after_sended(self, state: ChatState):
        # 记录用户消息
        self.chat_records.append(state.message)
    
    def on_llm_response(self, chat_completion):
        # 处理响应并记录
        if isinstance(chat_completion, ChatCompletion):
            content = chat_completion.choices[0].message.content
            self.chat_records.append({
                "role": "assistant",
                "content": content
            })
```

## 常见问题

### Q: 插件加载失败怎么办？

A: 检查以下几点：

1. 模块路径是否正确
2. 类名是否正确
3. 是否缺少依赖
4. 查看日志获取详细错误信息

### Q: 如何调试插件？

A: 使用日志记录关键步骤：

```python
logger.debug(f"参数: {arguments}")
logger.info(f"执行结果: {result}")
```

### Q: 插件间如何共享数据？

A: 通过应用实例或事件机制：

```python
# 使用应用实例存储共享数据
self.app.shared_data["key"] = value

# 使用 emit 方法调用其他插件
result = self.app.plugin_manager.emit("other-plugin", "method", args)
```

***

## 参考资料

- [插件基类源码](../src/plugins/plugin.py)
- [会话插件示例](../src/plugins/session_plugin/session_plugin.py)
- [微信插件示例](../src/plugins/wxauto_plugin/wxauto_plugin.py)
- [生命周期钩子定义](../src/types/lfecycle_hooks.py)

