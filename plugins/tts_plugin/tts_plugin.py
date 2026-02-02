from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from src.application import Application
from plugins import Plugin
from .tts.tts_service import TTSService
import asyncio
import typing

if typing.TYPE_CHECKING:
    from src.application import Application

class TTSPlugin(Plugin):
    def __init__(self, name: str):
        super().__init__(name, desc="TTS，智能体回复时，提供发声能力")
        self.is_start = False

        self.tts = TTSService('longanhuan')
        self.current_id = ""
        self.tts.on_tts_end = self.tts_end
        self.asr_plugin: Plugin | None = None
    
    def on_app_before_initialize(self, app: "Application"):
        self.asr_plugin = app.plugin_manager["asr_plugin"]
        return super().on_app_before_initialize(app)
    
    def on_background_thread_start(self):
        self.tts.set_event_loop(asyncio.get_event_loop())
    
    def on_ai_reply_completed(self, finish_reason: str):
        self.current_id = ""
    
    def on_ai_reply(self, chunk: ChatCompletionChunk):
        if chunk.id and self.current_id != chunk.id:
            self.tts.about()
            self.current_id = chunk.id

        content = chunk.choices[0].delta.content
        if not self.is_start:
            self.is_start = True
            self.tts.start()
            if self.asr_plugin:
                self.asr_plugin.emit("stop", {})
        
        if content:
            words = content.strip()
            if words:
                self.tts.speack_text(words)
    
    def on_message_before_send(self, *message: ChatCompletionMessageParam):
        if self.is_start:
            self.tts.about()
            self.is_start = False
        return super().on_message_before_send(*message)
    
    def emit(self, name, arguments):
        if name == "about":
            self.tts.about()
    
    def tts_end(self):
        print("我靠: ", self.asr_plugin)
        if self.asr_plugin:
            self.asr_plugin.emit("continue", {})
