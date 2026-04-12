from typing import Callable, Coroutine

from .base_transport import BaseTransport
import websockets
import asyncio

class WebSocketTransport(BaseTransport):
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc, tb):
        if self.close_signal:
            self.close_signal.set_exception(exc)

    def __init__(self, uri: str | None = None):
        self.uri = uri
        self.conn: websockets.ClientConnection | None = None
        self.close_signal: asyncio.Future | None = None
        self.connected_event_handler: Callable | None = None
        self.disconnect_event_handler: Callable | None = None
    
    def config(self, config: dict):
        self.uri = config.get("uri", self.uri)
    
    @property
    def is_connected(self) -> bool:
        return self.close_signal is not None and not self.close_signal.done() and self.conn is not None
    
    async def connect(self):
        if self.uri is None:
            raise ValueError("未设置uri")
        try:
            async with websockets.connect(self.uri) as conn:
                self.conn = conn
                self.close_signal = asyncio.Future()
                if self.connected_event_handler:
                    self.connected_event_handler()
                await self.close_signal
        except:
            raise
        finally:
            self.close_signal = None
            self.conn = None
            if self.disconnect_event_handler:
                self.disconnect_event_handler()
    
    def sync_disconnect(self):
        if self.close_signal:
            self.close_signal.set_result(None)
    
    async def disconnect(self):
        event_loop = asyncio.get_event_loop()
        await event_loop.run_in_executor(None, self.sync_disconnect)
    
    async def _receive(self):
        if self.conn is None or self.close_signal is None:
            raise ConnectionError("websocket未连接")
        try:
            return await self.conn.recv(False)
        except websockets.ConnectionClosed:
            raise
    
    async def listen(self, callback: Callable[[bytes], Coroutine]):
        if self.conn is None or self.close_signal is None:
            raise ConnectionError("websocket未连接")
        
        event_loop = asyncio.get_event_loop()
        while(self.conn.close_code == None and self.close_signal is not None):
            try:
                received_bytes = await self._receive()
                event_loop.create_task(callback(received_bytes))
            except ConnectionError:
                continue
            except websockets.ConnectionClosed:
                break
    
    async def send(self, data: bytes):
        if self.conn is None:
            raise ConnectionError("websocket未连接")
        try:
            await self.conn.send(data)
        except websockets.ConnectionClosed:
            raise ConnectionAbortedError("websocket连接已关闭")
    
    def event_bind_connected(self, callback: Callable):
        self.connected_event_handler = callback
    
    def event_bind_disconnect(self, callback: Callable):
        self.disconnect_event_handler = callback
        
