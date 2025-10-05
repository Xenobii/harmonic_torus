import mido
import queue
import threading
from vispy import scene
import numpy as np

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QMainWindow

from src.midi_entry import midi_listener



# Main window
class MainWindow(QWidget):
    def __init__(self, settings, processor):
        super().__init__()

        self.settings   = settings
        self.processor  = processor

        self.setWindowTitle("Main Menu")
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        self.resize(settings['window']['width'],
                    settings['window']['height'])

        # RT Button
        btn_rt = QPushButton("Real Time")
        btn_rt.setObjectName("rtButton")
        btn_rt.clicked.connect(self.open_window_rt)
        layout.addWidget(btn_rt)
        btn_rt.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        # PB Button
        btn_pb = QPushButton("Playback File")
        btn_pb.setObjectName("pbButton")
        btn_pb.clicked.connect(self.open_window_pb)
        layout.addWidget(btn_pb)
        btn_pb.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.setLayout(layout)

        self.window_rt = None
        self.window_pb = None

    def open_window_rt(self):
        if self.window_rt is None:
            # Handle rt input
            midi_queue = queue.Queue()
            midi_ports = mido.get_input_names()
            if not midi_ports:
                print("No MIDI ports found!")
                return
            
            # Start MIDI listening thread
            midi_in_name = midi_ports[self.settings['midi']['port']]
            print(f"Using MIDI input {midi_in_name}")
            threading.Thread(target=midi_listener,
                             args=(midi_in_name, midi_queue),
                             daemon=True).start()

            # Launch RT window
            self.window_rt = WindowRT(self.settings, midi_queue, self.processor)
        self.window_rt.show()

    def open_window_pb(self):
        if self.window_pb is None:
            return


class WindowRT(QMainWindow):
    def __init__(self, settings, midi_queue, processor):
        super().__init__()
        self.settings   = settings
        self.midi_queue = midi_queue
        self.processor  = processor(settings)

        # VisPy canvas
        self.canvas = scene.SceneCanvas(keys='interactive',
                                        show=False,
                                        bgcolor=self.settings['canvas']['background_color'])
        self.setCentralWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'

        # Build torus wireframe
        vertices, lines = create_torus_wire(R=self.settings['torus']['outer_radius'],
                                            r=self.settings['torus']['inner_radius'],
                                            n_u=self.settings['torus']['n_u'],
                                            n_v=self.settings['torus']['n_v'])
        torus_wireframe = scene.visuals.Line(
            pos=vertices,
            connect=lines,
            color='white',
            width=1.0,
            method='gl'
        )
        self.view.add(torus_wireframe)

        # Note scatter
        self.note_scatter = scene.visuals.Markers(parent=self.view.scene)
        self.cntr_scatter = scene.visuals.Markers(parent=self.view.scene)

        # Polling
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)        # 30 ms

        # Init
        self.note_pitches = np.zeros(88)
        self.sust_pitches = np.zeros(88)

        self.pedal_on   = False
        self.cloud      = None

    def update(self):
        try:
            while True:
                # Fetch from queue
                msg = self.midi_queue.get_nowait()
                
                # Change note pitches every time there's an input
                if msg is not None:
                    if msg.type == 'note_on':
                        self.note_pitches[msg.note - 21] = msg.velocity
                        if self.pedal_on:
                            self.sust_pitches[msg.note - 21] = msg.velocity
                        
                    elif msg.type == 'note_off':
                        self.note_pitches[msg.note - 21] = 0

                    elif msg.type == 'control_change':
                        if msg.control == 64:
                            if msg.value > 64:
                                self.pedal_on = True
                            else:
                                self.pedal_on = False
                                self.sust_pitches = np.zeros(88)
                    
                    # Convert to cloud
                    if self.settings['midi']['use_pedal']:
                        active_notes = self.note_pitches + self.sust_pitches
                    else: 
                        active_notes = self.note_pitches

                    self.cloud = self.processor.process_torus(active_notes)
        
        except queue.Empty:
            pass
        
        if self.cloud is not None:
            self.note_scatter.set_data(
                pos=np.array(self.cloud['note_coords']),
                face_color=self.settings['canvas']['note_color'],
                size=self.settings['canvas']['note_size']
            )

            self.cntr_scatter.set_data(
                pos=np.array(self.cloud['cntr_coords']),
                face_color=self.settings['canvas']['cntr_color'],
                size=self.settings['canvas']['cntr_size']
            )
        else:
            self.cntr_scatter.set_data(pos=np.empty((0, 3)))
            self.note_scatter.set_data(pos=np.empty((0, 3)))


def create_torus_wire(R, r, n_u, n_v):
    u = np.linspace(0, 2*np.pi, n_u, endpoint=False)
    v = np.linspace(0, 2*np.pi, n_v, endpoint=False)
    u, v = np.meshgrid(u, v)

    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)

    vertices = np.stack((x, y, z), axis=-1).reshape(-1, 3)

    lines = []
    for i in range(n_v):
        for j in range(n_u):
            # wrap around in both directions
            next_j = (j + 1) % n_u
            next_i = (i + 1) % n_v

            # horizontal line
            lines.append([i * n_u + j, i * n_u + next_j])
            # vertical line
            lines.append([i * n_u + j, next_i * n_u + j])

    lines = np.array(lines)

    return vertices, lines