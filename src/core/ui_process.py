import subprocess
import time
import socket
import shutil
import os

from src.components.logger import logger as log

logger = log.create(__name__)

def is_port_open(port, host='localhost'):
    """检查端口是否已被占用（防止重复启动）"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, port)) == 0
    except Exception as ex:
        logger.error(f"检查端口出错: {ex}")

class UIProcess:
    def __init__(self):
        self.processes = {}  # 存 {name: Popen对象}
        self.cmd_white_list = ["pnpm tauri dev"]
    
    def start(self, name, cmd: str, cwd: str | None = None, port: int | None=None, env=None):
        """
        启动 UI 服务
        :param name: 服务标识（如 "sovits_ui", "llm_api"）
        :param cmd: 命令列表，如 ["streamlit", "run", "app.py", "--server.port", "8501"]
        :param cwd: 工作目录
        :param port: 如果指定，先检查端口占用
        """
        if port and is_port_open(port):
            raise RuntimeError(f"端口 {port} 已被占用，{name} 可能已在运行")
        
        if cwd and not os.path.exists(cwd):
            raise Exception(f"工作路径'{cwd}'不存在")
        
        if cmd not in self.cmd_white_list:
            raise Exception(f"'{cmd}' 不在白名单内")

        # 启动子进程，非阻塞

        proc: subprocess.Popen
        try:
            logger.info(f"execute: {cmd}")
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,      # 可选：捕获或丢弃
                stderr=subprocess.STDOUT,    # 合并错误输出
                start_new_session=True,       # Linux/Mac：脱离终端会话，防止 SIGHUP
                shell=True
            )
        except Exception as ex:
            logger.error(f"出现异常: {ex}")
            return None

        if proc.stderr:
            logger.info(f"命令输出: \n{proc.stderr.read()}")
        
        self.processes[name] = {
            'proc': proc,
            'cmd': cmd,
            'port': port
        }
        
        # 等待服务就绪（简单轮询）
        if port:
            for _ in range(30):  # 最多等 3 秒
                time.sleep(0.1)
                if is_port_open(port):
                    logger.info(f"✅ {name} 已启动在端口 {port} (PID: {proc.pid})")
                    return proc
            raise RuntimeError(f"{name} 启动超时，端口 {port} 未响应")
        
        logger.info(f"✅ {name} 已启动 (PID: {proc.pid})")
        return proc
    
    def stop(self, name):
        """优雅停止服务"""
        if name not in self.processes:
            return False
        
        proc_info = self.processes[name]
        proc = proc_info['proc']
        
        # 先尝试 SIGTERM（优雅退出）
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # 超时则强制杀死
            proc.kill()
            proc.wait()
        
        del self.processes[name]
        logger.info(f"🛑 {name} 已停止")
        return True
    
    def stop_all(self):
        """关闭所有管理的服务"""
        for name in list(self.processes.keys()):
            self.stop(name)
    
    def is_running(self, name):
        """检查服务是否还在运行"""
        if name not in self.processes:
            return False
        return self.processes[name]['proc'].poll() is None