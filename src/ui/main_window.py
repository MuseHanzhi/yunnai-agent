from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QMainWindow,
    QLabel
)
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print(f"[{__name__}] 初始化客户端界面")
        print(f"[{__name__}] 初始化客户端界面 done")

