from wxautox4 import WeChat
from .wechat_event import WeChatEvent

class WeChatClient(WeChat):
    def __init__(self):
        super().__init__()
        self.wechat_event = WeChatEvent(self)
    
    # async def run(self):
    #     self.
    #     await asyncio.threads.to_thread(self.KeepRunning)


