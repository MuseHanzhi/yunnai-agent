from dashscope.audio.asr import (
    RecognitionResult,
    RecognitionCallback,
    Recognition
)
from src.application import Application
from plugins import Plugin
from pyaudio import PyAudio
import asyncio
import pyaudio
import logging
import typing

if typing.TYPE_CHECKING:
    from src.application import Application


class ASRPlugin(Plugin, RecognitionCallback):
    def __init__(self, name: str, is_open: bool=False, channels=1, sample_rate=16000, block_size = 3200):
        super().__init__(name)
        self.logger = logging.Logger(__name__)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(console_handler)

        self.channels = channels
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.micro_phone = PyAudio()
        self.micro_phone_stream: pyaudio._Stream | None = None
        self.app: "Application | None" = None
        self.event_loop: asyncio.AbstractEventLoop | None = None
        self.micro_phone_task = None

        self.recognition = Recognition(
            model="fun-asr-realtime",
            format="pcm",
            sample_rate=sample_rate,
            semantic_punctuation_enabled=False,
            callback=self,
        )

        self.words = ""
        self.is_open = is_open
        self.replying = False
    
    def on_open(self):
        self.logger.info(f"接收麦克风音频")
        self.micro_phone_stream = self.micro_phone.open(
                                                        format=pyaudio.paInt16,
                                                        channels=self.channels,
                                                        rate=self.sample_rate,
                                                        input=True)
    
    def on_close(self):
        if self.micro_phone_stream:
            self.micro_phone_stream.stop_stream()
            self.micro_phone_stream.close()
        
        self.micro_phone.terminate()
        self.micro_phone_stream = None

    def on_event(self, result: RecognitionResult):
        sentence = result.get_sentence()
        if 'text' in sentence:
            if isinstance(sentence, dict) and self.app:
                text = sentence.get('text', "")
                self.logger.info(f"mic -> {text}")
                self.app.main_window.set_input(text)

                tts = self.app.plugins_map.get('tts_plugin')
                if tts:
                    tts.emit('about', {})

                if RecognitionResult.is_sentence_end(sentence):
                    self.app.send_message({
                        'role': 'user',
                        'content': text
                    })
                    self.app.main_window.set_input("")
                    self.replying = True
    
    def on_error(self, result: RecognitionResult) -> None:
        self.logger.error(f"出现错误 - id: {result.request_id} - error: {result.message}")
        if self.micro_phone_stream:
            self.micro_phone_stream.stop_stream()
            self.micro_phone_stream.close()
    
    def on_app_before_initialize(self, app: Application):
        self.app = app

    async def start_stream(self):
        try:
            self.logger.info(f"准备接收音频流")
            self.recognition.start()
            self.logger.info(f"开始接收音频流")
            while self.micro_phone_task and self.micro_phone_stream:
                if not self.replying:
                    data = self.micro_phone_stream.read(self.block_size, False)
                    self.recognition.send_audio_frame(data)
                await asyncio.sleep(0.01)
        except Exception as e:
            self.logger.error(f"出现异常: {e}")
            return

        self.logger.info(f"准备结束接收音频流")
        self.recognition.stop()
        self.logger.info(f"结束接收音频流")


    def on_background_thread_start(self):
        self.event_loop = asyncio.get_event_loop()
        if self.is_open:
            self.micro_phone_task = self.event_loop.create_task(self.start_stream())
    
    def emit(self, name, arguments):
        self.logger.info(f"设置插件状态: {name}")
        if name == "start" and self.event_loop:
            self.micro_phone_task = self.event_loop.create_task(self.start_stream())
        if name == "stop":
            self.micro_phone_task = None
    
    def on_ai_reply_completed(self, finish_reason: str):
        self.replying = False