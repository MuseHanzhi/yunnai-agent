from typing import Callable, Any, Optional, TypedDict
import asyncio
import json
import time

from .types import (
    IPCData,
    Event, 
    InvokeRequest,
    InvokeResponse
)
from src.types.lfecycle_hooks import Hooks
from .transports.base_transport import BaseTransport
from .transports.ws_transport import WebSocketTransport
from src.components.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)

class InvokeSession(TypedDict):
    future: asyncio.Future
    timer: asyncio.TimerHandle

class IPCServer:
    def __init__(self, uri: str | None = None):
        self.websocket_conn: BaseTransport = WebSocketTransport()
        self.ipc_uri = uri
        
        # 事件处理器: name -> list[handler]
        self.event_handlers: dict[str, list[Callable[[dict], None]]] = {}
        
        # Invoke 处理器: name -> handler (客户端提供的能力)
        self.invoke_handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}
        
        self.invoke_sessions: dict[str, InvokeSession] = {}
        
        # Invoke 超时时间(毫秒)
        self.invoke_timeout = 30000

        self.invoke_num = 0
        
        self._setup_handlers()
        self.on_ipc_ready: Callable | None = None
        self.on_ipc_error: Callable[[Exception], None] | None = None
    
    def initialize(self, uri: str | None = None):
        self.ipc_uri = uri if uri else self.ipc_uri
        self.websocket_conn.config({
            "uri": self.ipc_uri
        })

    def _setup_handlers(self):
        """设置 WebSocket 服务器的事件处理器"""
        self.websocket_conn.event_bind_disconnect(self._handle_close)
        self.websocket_conn.event_bind_connected(self._connected_handler)
        
        # 注册内置的 ping 处理器，自动响应心跳
        self.handle("ping", self._handle_ping)
    
    def _connected_handler(self):
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(self.websocket_conn.listen(self._handle_raw_message))
        if self.on_ipc_ready:
            self.on_ipc_ready()

    def _handle_ping(self, data: dict):
        """处理心跳，自动回复 pong"""
        return "pong"
    
    async def _handle_raw_message(self, raw_bytes: bytes):
        event_loop = asyncio.get_event_loop()
        await event_loop.run_in_executor(None,self._handle_message, (raw_bytes.decode("utf-8")))

    def _handle_message(self, message: str):
        """处理接收到的消息"""
        try:
            # 解析消息
            ipc_data: IPCData = json.loads(message)
            
            if "id" not in ipc_data:
                # 事件类型 - 触发本地事件处理器
                self._handle_event(ipc_data)
            elif ipc_data['type'] == 'invoke-req':
                # 服务端请求调用客户端方法
                asyncio.get_event_loop().create_task(self._handle_invoke_request(ipc_data))
            elif ['type'] == 'invoke-res':
                # 服务端响应客户端的 invoke 请求
                self._handle_invoke_response(ipc_data)
                
            else:
                logger.warning(f"未知的消息类型: {ipc_data['type']}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, 原数据: {message}")
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}", exc_info=e)

    def _handle_event(self, data: Event):
        """处理事件类型消息"""
        event_name = data['name']
        arguments = data.get('arguments', {}) or {}
        
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(arguments)
                except Exception as e:
                    logger.error(f"事件处理器执行失败 ({event_name}): {e}", exc_info=True)
        else:
            logger.debug(f"未注册的事件: {event_name}")

    async def _handle_invoke_request(self, data: InvokeRequest):
        """处理服务端的 invoke 请求 (服务端 -> 客户端)"""
        arguments = data.get('arguments', {}) or {}

        result_data: InvokeResponse = {
            'id': data['id'],
            'name': data['name'],
            'type': 'invoke-res',
            'data': None,
            'exceptMessage': None
        }
        
        handler = self.invoke_handlers.get(data["id"])
        
        if not handler:
            result_data['exceptMessage'] = f"NoHandler: '{data['name']}' 该invokeIPC客户端未注册"
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
            logger.error(f"Invoke 处理器执行失败 ({data['name']}): {e}", exc_info=True)
            result_data['exceptMessage'] = str(e)
        
        await self._send(result_data)

    def _handle_invoke_response(self, data: InvokeResponse):
        """处理服务端对客户端 invoke 的响应"""
        invoke_name = data.get('name')
        if not invoke_name or invoke_name not in self.invoke_sessions:
            logger.warning(f"收到未知的 invoke 响应: {invoke_name}")
            return
        
        session = self.invoke_sessions.pop(invoke_name)
        
        # 清除超时定时器
        if 'timer' in session:
            session['timer'].cancel()
        
        except_msg = data.get('exceptMessage')
        future = session['future']
        if except_msg:
            future.set_exception(Exception(except_msg))
        else:
            future.set_result(data.get('data'))
        

    def _handle_close(self):
        """处理连接关闭"""
        # 清理所有待处理的 invoke
        for session in list(self.invoke_sessions.values()):
            if 'timer' in session:
                session['timer'].cancel()
            session['future'].set_exception(Exception("连接已关闭"))
        self.invoke_sessions.clear()

    async def _send(self, data: Any):
        """
        发送数据到服务端
        
        :param data: 需要发送的数据
        """
        try:
            await self.websocket_conn.send(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            raise

    # ==================== 公共 API ====================

    def on(self, name: str, callback: Callable[[dict], None]):
        """注册事件监听器 (接收服务端发送的事件)
        
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
        """注册 Invoke 处理器 (提供可被服务端调用的方法)
        
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

    async def emit(self, name: str | Hooks, **arguments):
        """发送事件到服务端 (单向通信)
        
        Args:
            name: 事件名称
            **arguments: 事件参数
        """
        if not self.is_connected:
            logger.warning("没有服务端连接")
            return
        
        command: Event = {
            'name': name,
            'type': 'event',
            'arguments': arguments
        }
        await self._send(command)

    async def invoke(self, name: str, **arguments) -> Any:
        """调用服务端方法并等待响应 (请求/响应模式)
        Args:
            name: 方法名称
            **arguments: 调用参数
            
        Returns:
            服务端返回的数据
            
        Raises:
            Exception: 调用失败、超时或连接关闭时抛出
        """
        
        if not self.is_connected:
            logger.warning("没有服务端连接")
            return
        
        self.invoke_num += 1

        if self.invoke_num >= 1000:     
            self.invoke_num = 0

        invoke_id: str = f"{time.time()}:{name}:{self.invoke_num}"

        if invoke_id in self.invoke_sessions:
            old_session = self.invoke_sessions.pop(invoke_id)
            if 'timer' in old_session:
                old_session['timer'].cancel()
            old_session['future'].set_exception(Exception("被新的同名 invoke 覆盖"))

        command: InvokeRequest = {
            'id': invoke_id,
            'name': name,
            'type': 'invoke-req',
            'arguments': arguments
        }
        
        # 创建 Future 等待响应
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        def timeout_handler():
            if invoke_id in self.invoke_sessions:
                self.invoke_sessions.pop(invoke_id)
                if not future.done():
                    future.set_exception(TimeoutError(f"Invoke '{invoke_id}' 超时"))
        
        # 设置超时
        timer = loop.call_later(
            self.invoke_timeout / 1000, 
            timeout_handler
        )
        
        self.invoke_sessions[invoke_id] = {
            'timer': timer,
            'future': future
        }
        
        try:
            await self._send(command)
            return await future
        except Exception:
            # 发送失败时清理
            if invoke_id in self.invoke_sessions:
                self.invoke_sessions.pop(invoke_id)
                timer.cancel()
            raise

    async def start(self):
        """启动 IPC 服务器"""
        try:
            await self.websocket_conn.connect()
        except Exception as ex:
            if self.on_ipc_error:
                self.on_ipc_error(ex)
        

    async def close(self):
        """关闭服务器"""
        # 拒绝所有待处理的 invoke
        for session in list(self.invoke_sessions.values()):
            if 'timer' in session:
                session['timer'].cancel()
            session['future'].set_exception(Exception("服务器关闭"))
        self.invoke_sessions.clear()
        
        await self.websocket_conn.disconnect()
        logger.debug("IPC 服务器已关闭")

    @property
    def is_connected(self) -> bool:
        return self.websocket_conn.is_connected