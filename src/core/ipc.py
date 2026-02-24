# ipc_server.py
import websockets
from typing import Callable, Any, Optional
import asyncio
import json
import time
from .websocket_server import WebSocketServer
import src.components.logger as log

logger = log.create(__name__)


class IPCServer:
    def __init__(self, host: str = "localhost", port: int = 8866):
        self.websocket_server = WebSocketServer(host, port, interval=500)
        
        # 事件处理器: name -> list[handler]
        self.event_handlers: dict[str, list[Callable[[dict], None]]] = {}
        
        # Invoke 处理器: name -> handler (服务端提供的能力)
        self.invoke_handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}
        
        # 等待客户端响应的 Promise: name -> (resolve, reject, timer)
        # 注意：同一时间只能有一个同名的 invoke 在等待响应
        self.pending_invokes: dict[str, dict] = {}
        
        # Invoke 超时时间(毫秒)
        self.invoke_timeout = 30000
        
        self._setup_handlers()
    
    def _unactive_handler(self):
        logger.warning("清理了不活跃的客户端连接")

    def _setup_handlers(self):
        """设置 WebSocket 服务器的事件处理器"""
        self.websocket_server.bind_message_event(self._handle_message)
        self.websocket_server.bind_close_event(self._handle_close)
        self.websocket_server.bind_heart_timeout(self._unactive_handler)
        
        # 注册内置的 ping 处理器，自动响应心跳
        self.on("ping", self._handle_ping)

    def _handle_ping(self, data: dict):
        """处理心跳，自动回复 pong"""
        _ = self.emit("pong", timestamp=time.time() * 1000)

    def _handle_message(self, message: websockets.Data):
        """处理接收到的消息"""
        try:
            # 解析消息
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            data = json.loads(message)
            
            msg_type = data.get('type')
            
            if msg_type == 'event':
                # 事件类型 - 触发本地事件处理器
                self._handle_event(data)
                
            elif msg_type == 'invoke-req':
                # 客户端请求调用服务端方法
                asyncio.create_task(self._handle_invoke_request(data))
                
            elif msg_type == 'invoke-res':
                # 客户端响应服务端的 invoke 请求
                self._handle_invoke_response(data)
                
            else:
                logger.warning(f"未知的消息类型: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}", exc_info=True)

    def _handle_event(self, data: dict):
        """处理事件类型消息"""
        event_name = data.get('name')
        arguments = data.get('arguments', {}) or {}
        
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(arguments)
                except Exception as e:
                    logger.error(f"事件处理器执行失败 ({event_name}): {e}", exc_info=True)
        else:
            logger.debug(f"未注册的事件: {event_name}")

    async def _handle_invoke_request(self, data: dict):
        """处理客户端的 invoke 请求 (客户端 -> 服务端)"""
        invoke_name: str = data.get('name', "")
        invoke_id: str = data.get("id", "")
        arguments = data.get('arguments', {}) or {}
        
        result_data = {
            'id': invoke_id,
            'name': invoke_name,
            'type': 'invoke-res',
            'data': None,
            'exceptMessage': None
        }
        
        handler = self.invoke_handlers.get(invoke_name)
        
        if not handler:
            result_data['exceptMessage'] = f"NoHandler: '{invoke_name}' 未注册"
            await self._send(result_data)
            return
        
        try:
            # 执行处理器
            result = handler(arguments)
            
            # 处理异步结果
            if asyncio.iscoroutine(result):
                result = await result
                
            result_data['data'] = result
            
        except Exception as e:
            logger.error(f"Invoke 处理器执行失败 ({invoke_name}): {e}", exc_info=True)
            result_data['exceptMessage'] = str(e)
        
        await self._send(result_data)

    def _handle_invoke_response(self, data: dict):
        """处理客户端对服务端 invoke 的响应"""
        invoke_name = data.get('name')
        if not invoke_name or invoke_name not in self.pending_invokes:
            logger.warning(f"收到未知的 invoke 响应: {invoke_name}")
            return
        
        pending = self.pending_invokes.pop(invoke_name)
        
        # 清除超时定时器
        if 'timer' in pending:
            pending['timer'].cancel()
        
        except_msg = data.get('exceptMessage')
        if except_msg:
            pending['reject'](Exception(except_msg))
        else:
            pending['resolve'](data.get('data'))

    def _handle_close(self):
        """处理连接关闭"""
        logger.info("客户端断开连接")
        # 清理所有待处理的 invoke
        for pending in list(self.pending_invokes.values()):
            if 'timer' in pending:
                pending['timer'].cancel()
            pending['reject'](Exception("连接已关闭"))
        self.pending_invokes.clear()

    async def _send(self, data: dict):
        """发送数据到客户端"""
        try:
            await self.websocket_server.send(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise

    # ==================== 公共 API ====================

    def on(self, name: str, callback: Callable[[dict], None]):
        """注册事件监听器 (接收客户端发送的事件)
        
        Args:
            name: 事件名称
            callback: 回调函数，接收参数字典
        """
        if not callable(callback):
            raise ValueError("callback 必须是可调用对象")
        
        if name not in self.event_handlers:
            self.event_handlers[name] = []
        self.event_handlers[name].append(callback)
        return self

    def off(self, name: str, callback: Optional[Callable[[dict], None]] = None):
        """移除事件监听器
        
        Args:
            name: 事件名称
            callback: 要移除的回调，为 None 则移除该事件所有处理器
        """
        if name not in self.event_handlers:
            return
        
        if callback is None:
            del self.event_handlers[name]
        elif callback in self.event_handlers[name]:
            self.event_handlers[name].remove(callback)
            if not self.event_handlers[name]:
                del self.event_handlers[name]
        return self

    def handle(self, name: str, callback: Callable[[dict[str, Any]], Any]):
        """注册 Invoke 处理器 (提供可被客户端调用的方法)
        
        Args:
            name: 方法名称
            callback: 处理函数，可返回普通值或协程
        """
        if not callable(callback):
            raise ValueError("callback 必须是可调用对象")
        self.invoke_handlers[name] = callback
        return self

    def unhandle(self, name: str):
        """移除 Invoke 处理器"""
        self.invoke_handlers.pop(name, None)
        return self

    async def emit(self, name: str, **arguments):
        """发送事件到客户端 (单向通信)
        
        Args:
            name: 事件名称
            **arguments: 事件参数
        """
        command = {
            'name': name,
            'type': 'event',
            'arguments': arguments
        }
        await self._send(command)

    async def invoke(self, name: str, **arguments) -> Any:
        """调用客户端方法并等待响应 (请求/响应模式)
        
        注意：同一时间只能有一个同名的 invoke 在等待响应，
        如果发起同名 invoke 时上一个还未完成，上一个会被拒绝。
        
        Args:
            name: 方法名称
            **arguments: 调用参数
            
        Returns:
            客户端返回的数据
            
        Raises:
            Exception: 调用失败、超时或连接关闭时抛出
        """
        # 如果已有同名的 invoke 在等待，先取消它
        if name in self.pending_invokes:
            old_pending = self.pending_invokes.pop(name)
            if 'timer' in old_pending:
                old_pending['timer'].cancel()
            old_pending['reject'](Exception("被新的同名 invoke 覆盖"))

        command = {
            'name': name,
            'type': 'invoke-req',
            'arguments': arguments
        }
        
        # 创建 Future 等待响应
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        def timeout_handler():
            if name in self.pending_invokes:
                self.pending_invokes.pop(name)
                if not future.done():
                    future.set_exception(TimeoutError(f"Invoke '{name}' 超时"))
        
        # 设置超时
        timer = loop.call_later(
            self.invoke_timeout / 1000, 
            timeout_handler
        )
        
        self.pending_invokes[name] = {
            'resolve': lambda x: future.set_result(x) if not future.done() else None,
            'reject': lambda x: future.set_exception(x) if not future.done() else None,
            'timer': timer
        }
        
        try:
            await self._send(command)
            return await future
        except Exception:
            # 发送失败时清理
            if name in self.pending_invokes:
                self.pending_invokes.pop(name)
                timer.cancel()
            raise

    async def start(self, event_loop: asyncio.AbstractEventLoop | None = None):
        """启动 IPC 服务器"""
        if event_loop is None:
            event_loop = asyncio.get_event_loop()
            
        logger.info(f"IPC 服务器启动: ws://{self.websocket_server.host}:{self.websocket_server.port}")
        await self.websocket_server.start(event_loop)

    async def close(self, code: int = 1000, reason: str = ""):
        """关闭服务器"""
        # 拒绝所有待处理的 invoke
        for pending in list(self.pending_invokes.values()):
            if 'timer' in pending:
                pending['timer'].cancel()
            pending['reject'](Exception("服务器关闭"))
        self.pending_invokes.clear()
        
        await self.websocket_server.close(code, reason)
        logger.info("IPC 服务器已关闭")

    @property
    def is_connected(self) -> bool:
        """检查是否有客户端连接"""
        return self.websocket_server._client is not None