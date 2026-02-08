import pvporcupine
from pvrecorder import PvRecorder

def main():
    # 创建Porcupine实例 - 需要替换为你的access_key
    porcupine = pvporcupine.create(
        access_key='[access_key]',  # 替换为你的Access Key
        keyword_paths=['wakeup_models/nihao-yunnai_zh_windows_v4_0_0.ppn'],
        model_path="wakeup_models/porcupine_params_zh.pv"
    )

    # 创建录音器
    recorder = PvRecorder(
        frame_length=porcupine.frame_length,
        device_index=-1  # -1表示使用默认麦克风
    )
    recorder.start()

    print('Listening ... (press Ctrl+C to exit)')

    try:
        while True:
            # 读取音频帧
            pcm = recorder.read()
            # 处理音频并检测唤醒词
            result = porcupine.process(pcm)

            # 如果检测到唤醒词
            if result >= 0:
                print(f'Detected keyword!')
    except KeyboardInterrupt:
        print('Stopping ...')
    finally:
        # 清理资源
        recorder.delete()
        porcupine.delete()


if __name__ == '__main__':
    main()

    main()
