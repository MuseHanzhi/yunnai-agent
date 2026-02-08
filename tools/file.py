import os

def write_file(file_path: str, content: str):
    print(f"写入文件'{file_path}'")
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"写入文件'{file_path}'成功")
        return {
            "message": "success",
            "data": None
        }
    except Exception as e:
        print(f"写入文件'{file_path}'出现异常")
        return {
            "message": f"出现异常: {e}"
        }

def read_file(file_path: str, encode: str = 'utf-8'):
    print(f"读取文件'{file_path}'内容")
    try:
        file_content = ""
        with open(file_path, 'r', encoding=encode) as f:
            file_content = f.read()
        print(f"读取文件'{file_path}'内容成功")
        return {
                "message": "success",
                "data": file_content
            }
    except Exception as e:
        print(f"读取文件'{file_path}'内容 出现异常")
        return {
            "message": f"出现异常: {e}"
        }

def get_dir_content(path: str = "."):
    print(f"读取文件夹'{path}'内容")
    try:
        return {
            "message": "success",
            "data": os.listdir(path)
        }
    except Exception as e:
        print(f"读取文件夹'{path}'内容 出现异常")
        return {
            "message": f"出现异常: {e}"
        }

def mkdir(paths: list[str]):
    print(f"开始创建文件夹")
    try:
        for path in paths:
            print(f"创建文件夹: {path}")
            os.makedirs(path)
            print(f"创建文件夹: {path} 成功")
        print(f"文件夹全部创建完毕")
        return {
            "message": "success"
        }
    except Exception as e:
        print("创建文件夹出现异常")
        return {
            "message": f"出现异常: {e}"
        }
    
