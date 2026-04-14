# IPC 接入指南

## 概述

YunNai-Kernel 作为独立进程运行，通过 WebSocket 与主应用进行 IPC（Inter-Process Communication）通信。

## 启动方式

内核以子进程方式启动，通过命令行参数 `ipc_uri` 指定 WebSocket 服务端地址：

```bash
python main.py --ipc_uri=ws://localhost:8080/ipc
```

或通过环境变量传递：

```bash
ipc_uri=ws://localhost:8080/ipc python main.py
```

## IPC 协议

### 消息类型

内核支持三种消息类型：

| 类型 | 标识 | 方向 | 说明 |
|------|------|------|------|
| 事件 | `event` | 双向 | 无响应的单向消息 |
| Invoke 请求 | `invoke-req` | 内核→服务端 | 请求调用服务端方法 |
| Invoke 响应 | `invoke-res` | 服务端→内核 | 返回调用结果 |

### 消息格式

#### 1. 事件消息（Event）

**用途**：单向状态通知、事件广播

```json
{
    "type": "event",
    "name": "event_name",
    "arguments": {
        "key1": "value1",
        "key2": "value2"
    }
}
```

**示例**：
```json
{
    "type": "event",
    "name": "message_received",
    "arguments": {
        "message_id": "msg-001",
        "content": "Hello World",
        "timestamp": 1699999999
    }
}
```

#### 2. Invoke 请求（Invoke Request）

**用途**：请求调用服务端方法并获取返回结果

```json
{
    "id": "1699999999:method_name:1",
    "name": "method_name",
    "type": "invoke-req",
    "arguments": {
        "param1": "value1"
    }
}
```

**字段说明**：
- `id`：唯一标识，格式为 `timestamp:method_name:sequence`
- `name`：要调用的方法名称
- `type`：固定为 `invoke-req`
- `arguments`：方法参数

#### 3. Invoke 响应（Invoke Response）

**用途**：返回 Invoke 请求的执行结果

```json
{
    "id": "1699999999:method_name:1",
    "name": "method_name",
    "type": "invoke-res",
    "data": {
        "result": "success"
    },
    "exceptMessage": null
}
```

**字段说明**：
- `id`：与请求对应的唯一标识
- `name`：方法名称
- `type`：固定为 `invoke-res`
- `data`：返回的数据（成功时）
- `exceptMessage`：错误信息（失败时）

### 心跳机制

内核内置心跳响应，自动回复服务端的 `ping` 事件：

```json
{
    "type": "event",
    "name": "ping",
    "arguments": {}
}
```

内核收到后回复字符串 `"pong"`。

## 协议特点

- **双向通信**：支持内核主动发送事件和调用服务端方法
- **请求超时**：Invoke 默认超时时间为 10 秒
- **异步支持**：支持同步和异步处理器
- **JSON 序列化**：所有消息均使用 JSON 格式

## 内置事件

| 事件名称 | 触发时机 | 参数 |
|----------|----------|------|
| `send-msg` | 发送消息 | `{"data": {...}, "options": {...}}` |
| `close-app` | 关闭应用 | 无 |
| `ping` | 心跳检测 | 无 |

## 代码示例

### 服务端接收事件

```python
# 监听内核发送的消息事件
def handle_send_msg(params):
    message = params["data"]
    options = params["options"]
    print(f"收到消息: {message['text']}")

ipc.on('send-msg', handle_send_msg)
```

### 服务端响应 Invoke

```python
# 注册供内核调用的方法
def get_server_info(params):
    return {
        "server_name": "Main Application",
        "version": "1.0.0"
    }

ipc.handle('get_server_info', get_server_info)
```