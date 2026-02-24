import websockets
import asyncio
from typing import Callable
import src.components.logger as log
import time

logger = log.create(__name__)

class WebSocketServer:
    def __init__(self, host = "localhost", port: int = 8866, heartbeat_interval = 1000, interval = 2000):
        self.host = host
        self.port = port
        self._client: None | websockets.ServerConnection = None
        self._running = False
        self.event_loop: None | asyncio.AbstractEventLoop = None
        self.last_active_time = 0
        self.heartbeat_interval = heartbeat_interval / 1000
        self.interval = interval
        self.server_connect: None | websockets.Server = None

        self.on_message_handler: Callable[[websockets.Data], None] | None = None
        self.on_client_closed: Callable[[], None] | None = None
        self.on_client_connect: Callable[[], None] | None = None
        self.on_heart_timeout: Callable[[], None] | None = None
        
    
    async def active_check(self, interval = 1000):
        while self._client:
            await asyncio.sleep(self.heartbeat_interval)
            now_time = time.time()
            if (now_time - self.last_active_time) * 1000 >= interval:
                if self._client is not None:
                    await self._client.close(websockets.CloseCode.NORMAL_CLOSURE, "UnactiveConnection")
                self._client = None
                if self.on_heart_timeout:
                    self.on_heart_timeout()
    
    async def client_handler(self, conn: websockets.ServerConnection):
        if self._client is not None:
            logger.info("已有客户端连接")
            await conn.close(websockets.CloseCode.TRY_AGAIN_LATER, "ConnectIsFull")
            return
        if self.on_client_connect:
            self.on_client_connect()
            
        logger.info("客户端连接")
        self._client = conn

        self.last_active_time = time.time()
        if self.event_loop:
            self.event_loop.create_task(self.active_check(self.interval))

        try:

            async for message in conn:
                self.last_active_time = time.time()
                if self.on_message_handler:
                    self.on_message_handler(message)
        except (websockets.ConnectionClosed|
                websockets.ConnectionClosedError|
                websockets.ConnectionClosedOK
                ):
            if self.on_client_closed:
                self.on_client_closed()
            self._client = None
            logger.info("客户端连接关闭")
        except Exception as err:
            logger.error(f"出现未知异常: {err}", exc_info=err, stack_info=True)
    
    async def start(self, event_loop: asyncio.AbstractEventLoop):
        if self._running:
            logger.warning("此实例已是开启状态")
            return
        
        if self.event_loop is None:
            self.event_loop = event_loop
        self._running = True
        self.server_connect = await websockets.serve(self.client_handler, self.host, self.port)
        self._running = False
        
    
    async def close(self, code: websockets.CloseCode | int = websockets.CloseCode.NORMAL_CLOSURE, reason = ""):
        self._running = False
        if self._client:
            await self._client.close(code, reason)
            self._client = None
        if self.server_connect:
            self.server_connect.close()
            self.server_connect = None
    
    async def send(self, data: bytes | str, text: bool | None = None):
        if self._client:
            await self._client.send(data, text)
    
    async def close_connect(self, code: websockets.CloseCode | int = websockets.CloseCode.NORMAL_CLOSURE, reason: str = ""):
        if self._client:
            await self._client.close(code, reason)
            self._client = None

    def bind_message_event(self, callback: Callable[[websockets.Data], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self.on_message_handler = callback

    def bind_close_event(self, callback: Callable[[], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self.on_client_closed = callback

    def bind_heart_timeout(self, callback: Callable[[], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self.on_heart_timeout = callback
