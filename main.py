import sys
from pathlib import Path
# from PyQt6.QtWidgets import *
# from PyQt6.QtGui import *
# from PyQt6.QtCore import *
from PySide6.QtWidgets import QApplication, QMainWindow
from ui_form import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    widget.setWindowTitle("BaSlicer")
    sys.exit(app.exec()) 
