from plugins import Plugin
import typing
import pvporcupine
from pvrecorder import PvRecorder
import asyncio
import os
import logging

if typing.TYPE_CHECKING:
    from src.application import Application

logger = logging.Logger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)

class WakeupPlugin(Plugin):
    def __init__(self,
                 name: str,
                 keyword_paths: list[str],
                 lang='zh',
                 text = "",
                 callback: None | typing.Callable = None
                 ) -> None:
        super().__init__(name, desc="唤醒词检测")
        access_key = os.environ.get("PORCUPINE_ACCESSKEY")
        if not access_key:
            raise Exception("请为'PORCUPINE_ACCESSKEY'设置环境变量，提供访问令牌")

        temp_keyword_paths = []
        for keyword_path in keyword_paths:
            temp_keyword_path = os.path.abspath(keyword_path)
            if not os.path.exists(temp_keyword_path):
                continue
            temp_keyword_paths.append(temp_keyword_path)

        if len(temp_keyword_paths) == 0:
            raise Exception("唤醒词没有有效的文件路径")

        model_path = os.path.abspath(os.path.join("wakeup_models", f'porcupine_params_{lang}.pv'))
        if not os.path.exists(model_path):
            raise Exception("模型文件不存在")

        self.text = text
        self.access_key = access_key
        self.keyword_paths = temp_keyword_paths
        self.model_path = model_path
        self.porcupine: pvporcupine.Porcupine | None = None
        self.recorder: None | PvRecorder = None
        self.listen_task: None | asyncio.Task = None
        self.app: "None | Application" = None
        self.event_loop: asyncio.AbstractEventLoop | None = None
        self.on_detect = callback
        self.is_listening = False  # 添加监听标志，防止重复启动

        # self.micro = pyaudio.PyAudio()
        # self.micro_stream: None | pyaudio._Stream = None

    def init(self):
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=self.keyword_paths,
            model_path=self.model_path
        )
        # print(self.porcupine.frame_length)
        self.recorder = PvRecorder(frame_length=self.porcupine.frame_length)

    def on_app_before_initialize(self, app: "Application"):
        self.app = app

    def on_ready(self):
        self.event_loop = asyncio.get_event_loop()
        self.listen_task = self.event_loop.create_task(self.start_listen())

    async def start_listen(self):
        # 防止重复启动
        if self.is_listening:
            logger.warning("已经在监听中，跳过重复启动")
            return

        self.is_listening = True
        self.init()
        if not (self.recorder and self.porcupine):
            logger.warning("麦克风或唤醒词模型未准备")
            self.is_listening = False
            return

        logger.info("开始唤醒词检测")
        self.recorder.start()
        detected = False
        while self.recorder and self.recorder.is_recording:
            try:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)
                if result >= 0:
                    logger.info("检测到唤醒词")
                    detected = True
                    break
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"出现异常: {e}")
                break

        if self.recorder:
            self.recorder.stop()

        # 在循环退出后再处理检测到唤醒词的逻辑
        if detected:
            self.detect_handler()

        # 清理资源
        self.deinit()
        self.is_listening = False
        self.listen_task = None

    def detect_handler(self):
        if not self.event_loop:
            logger.warning("没有事件循环实例")
            return
        if not self.app:
            logger.warning("没有主程序实例")
            return

        if self.text:
            self.event_loop.create_task(
                self.app.sync_send_message({
                    "role": "user",
                    "content": self.text
                })
            )
        if self.on_detect:
            self.on_detect()

    def deinit(self):
        if self.porcupine and self.recorder:
            if self.recorder.is_recording:
                self.recorder.stop()
            try:
                self.recorder.delete()
                self.porcupine.delete()
                self.porcupine = None
                self.recorder = None
            except Exception as e:
                logger.error(f"deinit 出现异常: {e}")

    def on_app_will_close(self, delay_request):
        self.deinit()
        if self.listen_task:
            self.listen_task.cancel()
            self.listen_task = None

    def emit(self, name: str, arguments: dict):
        if name == "stop":
            self.deinit()
        elif name == "start" and self.event_loop and not self.is_listening:
            self.listen_task = self.event_loop.create_task(self.start_listen())
