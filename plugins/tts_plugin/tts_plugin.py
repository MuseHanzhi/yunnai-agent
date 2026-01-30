from openai.types.chat import ChatCompletionChunk
from plugins import Plugin
from .tts.tts_service import TTSService
import asyncio

class TTSPlugin(Plugin):
    def __init__(self, name: str):
        super().__init__(name)
        self.is_start = False

        self.tts = TTSService('longanhuan')
        self.current_id = ""
        
    
    def on_background_thread_start(self):
        self.tts.set_event_loop(asyncio.get_event_loop())
    
    def on_ai_reply(self, chunk: ChatCompletionChunk):
        if chunk.id and self.current_id != chunk.id:
            self.tts.about()
            self.current_id = chunk.id

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
    
    def emit(self, name, arguments):
        if name == "about":
            self.tts.about()
