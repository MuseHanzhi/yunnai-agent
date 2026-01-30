from .callback import Callback
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat
import asyncio
import threading

class TTSService:
    __voice: str
    __model: str
    __callback: Callback
    __speacker: SpeechSynthesizer | None

    def __init__(self, voice: str, model: str = "cosyvoice-v3-flash"):
        print(f"[{__name__}] 初始化TTS服务")
        self.__voice = voice
        self.__model = model
        self.__callback = Callback()
        self.__speacker = None
        self.__wait_speacker = []
        self.__speacker_task = None
        self.__event_loop: asyncio.AbstractEventLoop | None = None
        print(f"[{__name__}] 初始化TTS服务 done")
    
    @property
    def state(self):
        if not self.__speacker_task and not self.__speacker:
            return "NoReady"
        elif self.__speacker and not self.__speacker_task:
            return "Ready"
        return "Speacking"
    
    def start(self):
        self.__speacker = SpeechSynthesizer(
            model=self.__model,
            voice=self.__voice,
            format=AudioFormat.PCM_22050HZ_MONO_16BIT,
            callback=self.__callback
        )
    
    async def speack(self):
        while self.__wait_speacker and self.__speacker:
            await asyncio.sleep(0.01)
            word = self.__wait_speacker.pop(0)
            if word:
                self.__speacker.streaming_call(word)
        if self.__speacker:
            self.__speacker.streaming_complete()
        self.__speacker = None
        self.__speacker_task = None
    
    def speack_text(self, text: str | None):
        self.__wait_speacker.append(text)
        if self.__speacker_task == None and self.__event_loop:
            self.__speacker_task = self.__event_loop.create_task(self.speack())
    
    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop):
        self.__event_loop = event_loop
