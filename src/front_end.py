import queue
from PyQt5 import QtWidgets, QtCore
from vispy import scene


class VisWindow(QtWidgets.QMainWindow):
    def __init__(self, midi_queue, processor):
        super().__init__()
        self.midi_queue = midi_queue
        self.processor  = processor

        # VisPy canvas
        self.canvas = scene.SceneCanvas(keys='interactive', show=True)
        self.setCentralWidget(self.canvas.native)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'turntable'

        # Placeholder scatter
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
                if points:
                    self.data_points.append(points)

        except queue.Empty:
            pass
            
        if self.data_points:
            self.scatter.set_data(
                pos=self.data_points,
                face_color='red',
                size=10
            )