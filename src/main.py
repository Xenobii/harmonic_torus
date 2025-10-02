import sys
import queue
import mido
import threading
from PyQt5 import QtWidgets, QtCore

from midi_entry import midi_listener
from processor import processor
from front_end import VisWindow


def main():
    midi_queue = queue.Queue()

    midi_ports = mido.get_input_names()
    if not midi_ports:
        print("No MIDI Ports :(")
        sys.exit(1)

    # Start MIDI listener thread
    midi_in_name = midi_ports[0]
    print(f"Using MIDI input {midi_in_name}")
    threading.Thread(target=midi_listener, args=(midi_in_name, midi_queue), daemon=True).start()

    # Start Qt app
    app = QtWidgets.QApplication(sys.argv)
    win = VisWindow(midi_queue, processor)
    win.show()
    sys.exit(app.exec())


if __name__=="__main__":
    main()