from os import path
import os
import pyaudio

def get_list_from_user_music():
    files = os.listdir(music_path)
    music_files: list[str] = []
    for file in files:
        if file.split(".")[-1] in ["mp3", "wav", "ogg"]:
            music_files.append(file)

    return {
        "message": "OK",
        "datas": music_files
    }

def play_music(filename: str):
    target_path = path.join(music_path, filename)
    
    os.system(f"\"{target_path}\"")
    return {
        "message": "OK"
    }

audio = pyaudio.PyAudio()
user_home = path.join("C:", os.path.sep , "Users", os.getlogin())
music_path = path.join(user_home, "Music")
