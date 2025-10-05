import sys
import json

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication

from src.frontend import MainWindow
from src.processor import Processor


SETTINGS_PATH = "src/settings.json"


if __name__ == "__main__":
    with open(SETTINGS_PATH) as f:
        settings = json.load(f)

    app = QApplication(sys.argv)
    
    # Set global styling
    app.setWindowIcon(QtGui.QIcon("res/icons/icon.png"))
    with open("res/qss/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    # processor = processor
    main_win = MainWindow(settings, Processor)
    main_win.show()
    sys.exit(app.exec_())