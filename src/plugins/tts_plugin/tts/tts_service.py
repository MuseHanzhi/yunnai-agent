from .callback import Callback
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat
import asyncio
import logging

class TTSService:
    __voice: str
    __model: str
    __callback: Callback
    __speacker: SpeechSynthesizer | None

    def __init__(self, voice: str, model: str = "cosyvoice-v3-flash"):
        self.logger = logging.Logger(__name__)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(console_handler)

        self.__voice = voice
        self.__model = model
        self.__callback = Callback()
        self.__speacker = None
        self.__wait_speacker = []
        self.__speacker_task = None
        self.__event_loop: asyncio.AbstractEventLoop | None = None
    
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
            await asyncio.sleep(0.1)
            try:
                word = self.__wait_speacker.pop(0)
                if word:
                    self.__speacker.streaming_call(word)
            except IndexError:
                break
            except Exception as e:
                self.logger.error(f"出现异常: {e}")
        if self.__speacker:
            self.__speacker.streaming_complete()
        self.__speacker = None
        self.__speacker_task = None
        self.logger.info("TTS合成结束")
        self.on_tts_end()
    
    def speack_text(self, text: str | None):
        self.__wait_speacker.append(text)
        if self.__event_loop and self.__speacker_task == None:
            self.__speacker_task = self.__event_loop.create_task(self.speack())
    
    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop):
        self.__event_loop = event_loop
    
    def abort(self):
        if self.__speacker:
            try:
                self.__speacker.streaming_complete()
                self.__speacker.close()
            except:
                ...
        self.__wait_speacker.clear()
        self.__speacker_task = None
    
    def on_tts_end(self):
        ...