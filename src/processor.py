import numpy as np
from mido import Message
from math import gcd


class Torus_Note():
    def __init__(self, msg):
        R = 1.0
        r = 0.3

        self.pitch      = msg.note
        self.note       = msg.note % 12
        self.type       = msg.type
        self.velocity   = msg.velocity

        # Map to tonnetz
        self.theta  = (self.note * 7 % 12 / 12) * 2 * np.pi
        self.phi    = (self.note * 7 % 12 / 12) * 2 * np.pi

        self.x = (R + r * np.cos(self.theta)) * np.cos(self.phi)
        self.z = (R + r * np.cos(self.theta)) * np.sin(self.phi)
        self.y = r * np.sin(self.theta)

    @classmethod
    def msg2torus(cls, msg):
        return cls(msg)

class Note_Cloud():
    def __init__(self, notes):
        return 0
    


# Placeholder processor
def midi_processor(msg):
    if not isinstance(msg, Message):
        return None
    
    note = Torus_Note(msg)
    if note.type == 'note_on' and note.velocity > 0:
        x = note.x
        y = note.z
        z = note.y

        return {'coords': np.array([x, y, z], dtype=np.float32),
                'type'  : 1}

    if note.type == 'note_off':
        x = note.x
        y = note.z
        z = note.y

        return {'coords': np.array([x, y, z], dtype=np.float32),
                'type'  : 0}

    return None