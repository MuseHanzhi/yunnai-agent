from dashscope.audio.asr import (
    RecognitionResult,
    RecognitionCallback,
    Recognition
)
from openai.types.chat import ChatCompletionChunk
from src.application import Application
from plugins import Plugin
from pyaudio import PyAudio
import asyncio
import pyaudio
import logging
import typing
import time

if typing.TYPE_CHECKING:
    from src.application import Application



#region 初始化日志输出
logger = logging.Logger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
logger.addHandler(console_handler)
#endregion

class ASRPlugin(Plugin, RecognitionCallback):
    def __init__(self, name: str, is_open: bool=False, channels=1, sample_rate=16000, block_size = 3200, model = "fun-asr-realtime", end_time = 1000):
        super().__init__(name, desc="语音识别功能，使用麦克风直接和智能体对话")

        self.channels = channels
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.is_open = is_open
        self.app: "Application | None" = None
        self.event_loop: asyncio.AbstractEventLoop | None = None
        self.micro_phone_task = None
        self.speak_end_callback: typing.Callable | None = None
        self.ended: typing.Callable | None = None
        self.end_speak_time = 0
        self.end_time = end_time / 1000
        self.started = False

        self.micro_phone = PyAudio()
        self.micro_phone_stream: pyaudio._Stream | None = None
        self.recognition = Recognition(
            model=model,
            format="pcm",
            sample_rate=sample_rate,
            semantic_punctuation_enabled=False,
            callback=self
        )
        
    
    def on_open(self):
        logger.info("开始语音转文字")
        self.start_micro()
    
    def start_micro(self):
        logger.info(f"打开麦克风")
        try:
            if not self.micro_phone_stream:
                self.micro_phone_stream = self.micro_phone.open(
                                                                format=pyaudio.paInt16,
                                                                channels=self.channels,
                                                                rate=self.sample_rate,
                                                                input=True)
        except Exception as e:
            logger.error(f"出现异常: {e}")
            
    
    # def on_ai_reply(self, chunk: ChatCompletionChunk):
    #     self.close()
    
    def on_close(self):
        self.close()
    
    def close(self):
        logger.info("关闭麦克风")
        self.micro_phone_task = None

        if self.micro_phone_stream:
            try:
                self.micro_phone_stream.stop_stream()
                self.micro_phone_stream.close()
            except Exception as e:
                logger.error(f"出现异常: {e}")

        logger.info("关闭语音识别")
        try:
            self.recognition.stop()
        except Exception as e:
            logger.error(f"出现异常: {e}")
        
        self.micro_phone_stream = None
        self.started = False

    def on_event(self, result: RecognitionResult):
        sentence = result.get_sentence()
        if 'text' in sentence:
            if isinstance(sentence, dict) and self.app:
                text: str = sentence.get('text', "")
                self.app.main_window.set_input(text)

                logger.info(f"mic -> {text}")
                self.end_speak_time = 0

                if RecognitionResult.is_sentence_end(sentence) and text.strip():    # VAD检测，说话结束
                    self.speak_end(text.strip())
    
    def speak_end(self, text_result: str):
        if self.event_loop and False:   # 暂时先禁用智能体响应
            self.event_loop.create_task(
                self.app.sync_send_message({
                    'role': 'user',
                    'content': text
                    })
                )
        logger.info("说话结束")
        self.close()
        if self.speak_end_callback:
            self.speak_end_callback(text_result)
    
    def on_error(self, result: RecognitionResult) -> None:
        logger.error(f"出现错误 - id: {result.request_id} - error: {result.message}")
        if self.micro_phone_stream:
            self.micro_phone_stream.close()
        #     self.micro_phone_stream.stop_stream()
    
    def on_app_before_initialize(self, app: Application):
        self.app = app

    async def start_stream(self):
        try:
            logger.info(f"准备接收音频流")
            self.recognition.start()
            logger.info(f"开始接收音频流")
            self.started = True
            # last_time = time.time()
            # l_time = 0
            while self.started:
                await asyncio.sleep(0.01)
                # if self.end_speak_time < l_time:
                #     last_time = time.time()
                # self.end_speak_time = time.time() - last_time
                # l_time = self.end_speak_time
                if not (self.micro_phone_task and self.micro_phone_stream): # or self.end_speak_time >= self.end_time:
                    break
                data = self.micro_phone_stream.read(self.block_size, False)
                self.recognition.send_audio_frame(data)
        except Exception as e:
            logger.error(f"语音识别出现异常: {e}")

        if self.started:
            self.started = False
            self.close()
        if self.ended:
            self.ended()

    def on_background_thread_start(self):
        self.event_loop = asyncio.get_event_loop()
        if self.is_open:
            self.start()
    
    def emit(self, name: str, arguments: dict):
        if name == "stop":
            self.close()
        elif name == "start" and self.event_loop:
            self.start()
    
    def start(self):
        if self.event_loop:
            self.micro_phone_task = self.event_loop.create_task(self.start_stream())

    def on_app_will_close(self, delay_request):
        self.close()
        self.micro_phone.terminate()

    def bind_speak_end(self, callback: typing.Callable):
        self.speak_end_callback = callback
    
    def bind_ended(self, callback: typing.Callable):
        self.ended = callback
