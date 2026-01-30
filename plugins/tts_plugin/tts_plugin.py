from openai.types.chat import ChatCompletionChunk
from plugins import Plugin
from .tts.tts_service import TTSService
import asyncio

class TTSPlugin(Plugin):
    def __init__(self):
        super().__init__('tts_plugin')
        self.is_start = False

        self.tts = TTSService('longanhuan')
        
    
    def on_background_thread_start(self):
        self.tts.set_event_loop(asyncio.get_event_loop())
    
    def on_ai_reply(self, chunk: ChatCompletionChunk):
        content = chunk.choices[0].delta.content
        if not self.is_start:
            self.is_start = True
            self.tts.start()
        
        if content:
            words = content.strip()
            if words:
                self.tts.speack_text(words)
    
    def on_ai_reply_completed(self, finish_reason: str):
        self.is_start = False
