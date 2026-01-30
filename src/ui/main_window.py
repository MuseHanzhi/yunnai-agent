from PyQt6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
)

from PyQt6.QtCore import pyqtSignal, Qt

class MainWindow(QMainWindow):

    send_btn_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print(f"[{__name__}] 初始化客户端界面")
        print(f"[{__name__}] 初始化客户端界面 done")
        
        container = QWidget()
        vbox = QVBoxLayout(container)
        hbox = QHBoxLayout()

        self.label = QLabel("0")
        font = self.label.font()
        font.setPointSize(19)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self.label)

        self.input = QLineEdit()
        hbox.addWidget(self.input)

        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self._send_btn_trigger)
        hbox.addWidget(self.send_btn)
        vbox.addLayout(hbox)
        self.setCentralWidget(container)
    
    def set_label(self, text):
        self.label.setText(text)
    
    def set_input(self, text: str):
        self.input.setText(text)
    
    def _send_btn_trigger(self):
        self.send_btn_clicked.emit(self.input.text())
