import websockets
import asyncio
from typing import Callable, TypedDict
from src.components.logger.logger import LogCreator
import time
from urllib import parse as urlparser

logger = LogCreator.instance.create(__name__)

class ConnectUnit(TypedDict):
    conn: websockets.ServerConnection
    last_active_time: float

class WebSocketServer:
    def __init__(self, host: str, port: int, timeout: float = 3000, check_interval = 500):
        self.host = host
        self.port = port

        self._clients: dict[str, ConnectUnit] = {}
        self._server_connect: None | websockets.Server = None
        self._running = False
        self._event_loop: None | asyncio.AbstractEventLoop = None
        self._interval = check_interval / 1000
        self._timeout = timeout

        self._on_message_handler: Callable[[str, websockets.Data], None] | None = None
        self._on_client_closed: Callable[[str], None] | None = None
        self._on_client_connect: Callable[[str], None] | None = None
        self._on_died_timeout: Callable[[str], None] | None = None
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    async def active_check(self, timeout: float):
        while self._running:
            await asyncio.sleep(self._interval)
            now_time = time.time()
            for c_id in list(self._clients.keys()):
                conn = self._clients[c_id]
                t = now_time - conn['last_active_time']
                if t > timeout:
                    try:
                        await conn["conn"].close(websockets.CloseCode.NORMAL_CLOSURE, "ActiveTimeout")
                    finally:
                        del self._clients[c_id]    
                
                    if self._on_died_timeout:
                        self._on_died_timeout(c_id)

    
    async def client_handler(self, conn: websockets.ServerConnection):
        # 接收连接
        if not conn.request:
            await conn.close(websockets.CloseCode.INVALID_DATA)
            return
        
        path = conn.request.path
        parsed = urlparser.urlparse(path)
        params = urlparser.parse_qs(parsed.query)
        
        conn_id_optional = params.get("id")
        conn_id = ((conn_id_optional[0] if conn_id_optional[0] else "") if conn_id_optional else "")
        if conn_id == "":
            await conn.close(websockets.CloseCode.INVALID_DATA)
            return
        
        conn_unit: ConnectUnit = {
            "last_active_time": time.time(),
            "conn": conn
        }
        self._clients[conn_id] = conn_unit

        if self._on_client_connect:
            self._on_client_connect(conn_id)
            
        logger.info(f"客户端'{conn_id}'连接")

        # 接收连接数据
        try:
            async for message in conn:
                conn_unit["last_active_time"] = time.time()
                if self._on_message_handler:
                    self._on_message_handler(conn_id, message)
        except (websockets.ConnectionClosed|
                websockets.ConnectionClosedError|
                websockets.ConnectionClosedOK
                ):
            if self._on_client_closed:
                self._on_client_closed(conn_id)
            logger.info("客户端连接关闭")
        except Exception as err:
            logger.error(f"出现未知异常: {err}", exc_info=err, stack_info=True)
    
    async def start(self):
        if self._running:
            logger.warning("此实例已是开启状态")
            return
        
        self._event_loop = asyncio.get_event_loop()
        self._running = True
        self._event_loop.create_task(self.active_check(self._timeout))
        self._server_connect = await websockets.serve(self.client_handler, self.host, self.port)
        self._running = False
    
    async def clear_clients(self):
        for conn_id in list(self._clients.keys()):
            unit = self._clients[conn_id]
            if unit["conn"].state == websockets.State.OPEN:
                try:
                    await unit["conn"].close(websockets.CloseCode.NORMAL_CLOSURE, "ServerExit")
                finally:
                    ...
            del self._clients[conn_id]
    
    async def close(self):
        self._running = False
        await self.clear_clients()
        if self._server_connect:
            self._server_connect.close()
            self._server_connect = None
    
    async def send(self, data: bytes | str, text: bool = True, id: str | None = None):
        """
        发送数据
        Args:
            data: 需要发送的数据
            text: 是否为文本数据
            id: 客户端Id，空为广播模式
        """
        if id is None:
            for (c_id, unit) in self._clients.items():
                await unit["conn"].send(data, text)
            return
        conn = self._clients.get(id)
        if conn:
            await conn["conn"].send(data, text)
    
    async def close_connect(self, id: str, code: websockets.CloseCode | int = websockets.CloseCode.NORMAL_CLOSURE, reason: str = ""):
        conn = self._clients[id]["conn"]
        await conn.close(code, reason)

    def bind_message_event(self, callback: Callable[[str, websockets.Data], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self._on_message_handler = callback

    def bind_close_event(self, callback: Callable[[str], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self._on_client_closed = callback

    def bind_died_timeout(self, callback: Callable[[str], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self._on_died_timeout = callback
