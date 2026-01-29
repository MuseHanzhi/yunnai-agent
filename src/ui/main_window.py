from PyQt6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print(f"[{__name__}] 初始化客户端界面")
        print(f"[{__name__}] 初始化客户端界面 done")
        
        container = QWidget()
        vbox = QVBoxLayout(container)
        self.__label = QLabel("0")
        vbox.addWidget(self.__label)
        
        self.setCentralWidget(container)
    
    def set_label(self, text):
        self.__label.setText(text)
