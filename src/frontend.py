import mido
import queue
import threading
from vispy import scene, color, visuals
import numpy as np

from vispy.geometry import MeshData
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QMainWindow

from src.midi_entry import midi_listener


# Main window
class MainWindow(QWidget):
    def __init__(self, processor):
        super().__init__()
        self.setWindowTitle("Main Menu")
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        self.resize(400, 300)

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

        self.processor = processor
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
            midi_in_name = midi_ports[0]
            print(f"Using MIDI input {midi_in_name}")
            threading.Thread(target=midi_listener,
                             args=(midi_in_name, midi_queue),
                             daemon=True).start()

            # Launch RT window
            self.window_rt = WindowRT(midi_queue, self.processor)
        self.window_rt.show()

    def open_window_pb(self):
        if self.window_pb is None:
            return


class WindowRT(QMainWindow):
    def __init__(self, midi_queue, processor):
        super().__init__()
        self.midi_queue = midi_queue
        self.processor  = processor

        # VisPy canvas
        self.canvas = scene.SceneCanvas(keys='interactive', show=False)
        self.setCentralWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'

        torus_mesh = create_torus(R=1.0, r=0.3)
        self.torus = scene.visuals.Mesh(meshdata=torus_mesh,
                                        color=(0.5, 0.8, 0.2, 0.1),
                                        parent=self.view.scene)

        # Scatter
        self.scatter = scene.visuals.Markers(parent=self.view.scene)

        # Polling
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)        # 30 ms

        self.data_points = []

    def update(self):
        # Fetch from queue
        try:
            while True:
                msg = self.midi_queue.get_nowait()
                points = self.processor(msg)
                if points is not None:
                    if points['type'] == 1:
                        self.data_points.append(points['coords'])
                    elif points['type'] == 0:
                        for i, p in enumerate(self.data_points):
                            if np.allclose(p, points['coords']):
                                self.data_points.pop(i)
                                break

        except queue.Empty:
            pass
            
        if self.data_points:
            self.scatter.set_data(
                pos=np.array(self.data_points),
                face_color='red',
                size=10
            )
        self.scatter.update()


def create_torus(R=1.0, r=0.3, rows=30, cols=60):
    u = np.linspace(0, 2*np.pi, rows, endpoint=False)
    v = np.linspace(0, 2*np.pi, cols, endpoint=False)
    u, v = np.meshgrid(u, v, indexing='ij')

    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)

    # Flatten
    vertices = np.column_stack([x.ravel(), y.ravel(), z.ravel()])

    # Create faces (quads -> triangles)
    faces = []
    for i in range(rows):
        for j in range(cols):
            i_next = (i + 1) % rows
            j_next = (j + 1) % cols
            a = i * cols + j
            b = i_next * cols + j
            c = i_next * cols + j_next
            d = i * cols + j_next
            faces.append([a, b, c])
            faces.append([a, c, d])
    faces = np.array(faces)

    return MeshData(vertices=vertices, faces=faces)
