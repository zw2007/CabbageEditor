from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow


class CustomWindow(QMainWindow):
    def __init__(self, parent: Optional[QMainWindow] = None):
        super(CustomWindow, self).__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
