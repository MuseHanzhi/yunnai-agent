from dashscope.audio.tts_v2 import ResultCallback
import pyaudio

class Callback(ResultCallback):
    _player = None
    _stream = None

    def on_open(self):
        self._player = pyaudio.PyAudio()
        self._stream = self._player.open(
            format=pyaudio.paInt16, channels=1, rate=22050, output=True
        )

    def on_complete(self):
        pass

    def on_error(self, message: str):
        print(f"语音合成出现异常：{message}")

    def on_close(self):
        # 停止播放器
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._player:
            self._player.terminate()

    def on_event(self, message):
        ...

    def on_data(self, data: bytes) -> None:
        if self._stream:
            self._stream.write(data)
