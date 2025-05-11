import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon
from ui_form import Ui_MainWindow




class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("BaSlicer")
        if getattr(sys, 'frozen', False):
            icon = QIcon(os.path.join(sys._MEIPASS, "icon.ico"))
        else:
            icon = QIcon("icon.ico")
        self.setWindowIcon(icon)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    if getattr(sys, 'frozen', False):
        icon = QIcon(os.path.join(sys._MEIPASS, "icon.ico"))
    else:
        icon = QIcon("icon.ico")
    widget.setWindowTitle("BaSlicer")
    # widget.setWindowIcon(QIcon(resource_path("icon.ico")))
    widget.setWindowIcon(icon)  # Use the icon directly for the window icon
    sys.exit(app.exec())
