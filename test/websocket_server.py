import websockets
import asyncio
from typing import Callable
# import src.components.logger as log

TextMessage, BinaryMessage = 0, 1

class WebSocketServer:
    def __init__(self, host = "localhost", port: int = 8866):
        self.host = host
        self.port = port
        self._client: None | websockets.ServerConnection = None
        self._running = False
        self.event_loop: None | asyncio.AbstractEventLoop = None
        self.on_message_handler: Callable[[websockets.Data, int], None] | None = None
        self.geted_connect = False
    
    async def client_handler(self, conn: websockets.ServerConnection):
        if self._client is not None:
            print("已有客户端连接")
            await conn.close(1008, "已有客户端连接")
            return
        print("客户端连接")
        self._client = conn

        try:
            async for message in conn:
                if self.on_message_handler:
                    messageType = isinstance(message, str)
                    self.on_message_handler(message, TextMessage if messageType else BinaryMessage)
        except (websockets.ConnectionClosed|
                websockets.ConnectionClosedError|
                websockets.ConnectionClosedOK
                ):
            print("客户端连接关闭")
        except Exception as err:
            print(f"出现未知异常: {err}")
        print("end")
    
    async def start(self, event_loop: asyncio.AbstractEventLoop):
        if self._running:
            print("此实例已是开启状态")
            return
        
        if self.event_loop is None:
            self.event_loop = event_loop
        self._running = True
        print(f"开始监听: ws://{self.host}:{self.port}")
        async with websockets.serve(self.client_handler, self.host, self.port):
            await asyncio.Future()
        self._running = False
        
    
    async def close(self, code: websockets.CloseCode | int = websockets.CloseCode.NORMAL_CLOSURE, reason = ""):
        self._running = False
        if self._client:
            await self._client.close(code, reason)
            self._client = None
    
    async def send(self, data: bytes | str, text: bool | None = None):
        if self._client:
            await self._client.send(data, text)

    def on_message(self, callback: Callable[[websockets.Data, int], None]):
        if not callable(callback):
            raise ValueError("callback必须可调用")
        self.on_message_handler = callback


def message_handler(data: websockets.Data, msg_type: int):
    if msg_type == TextMessage:
        print(f"接收到文本信息: {data}")
    elif msg_type == BinaryMessage:
        print(f"接收到二进制信息: {data[:16]}")


import time

a = time.time()

while True:
    n = time.time()
    print(int(n - a) * 1000)
    time.sleep(1000 / 1000)
