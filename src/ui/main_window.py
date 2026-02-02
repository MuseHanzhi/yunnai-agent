from PyQt6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
)

from PyQt6.QtCore import (
    pyqtSignal,
    Qt
)

class MainWindow(QMainWindow):

    send_btn_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        container = QWidget()
        vbox = QVBoxLayout(container)
        hbox = QHBoxLayout()

        self.input = QLineEdit()
        hbox.addWidget(self.input)

        self.label: QLabel | None = QLabel()
        self.set_label_config(self.label)

        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self._send_btn_trigger)
        hbox.addWidget(self.send_btn)
        vbox.addLayout(hbox)
        vbox.addWidget(self.label)
        self.vbox = vbox
        self.setCentralWidget(container)
    
    def set_label(self, text):
        if self.label:
            self.label.setText(text)
    
    def set_input(self, text: str):
        self.input.setText(text)
    
    def set_label_config(self, label: QLabel):
        font = label.font()
        font.setPointSize(16)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # def set_current_label(self, label: QLabel):
    #     self.label = label
    
    def _send_btn_trigger(self):
        self.send_btn_clicked.emit(self.input.text())
    
    # def new_line(self):
    #     label = QLabel()
    #     self.set_label_config(label)
    #     self.vbox.addWidget(label)
    #     self.label = label

    def clear_text(self):
        ...
        # labels = self.vbox.
        # for label in labels:
        #     label.destroy()
        #     self.vbox.removeWidget(label)
