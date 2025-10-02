import sys

from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication

from src.frontend import MainWindow
from src.processor import midi_processor


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set global styling
    app.setWindowIcon(QtGui.QIcon("res/icons/icon.png"))
    with open("res/qss/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    processor = midi_processor
    main_win = MainWindow(processor)
    main_win.show()
    sys.exit(app.exec_())