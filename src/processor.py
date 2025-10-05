import numpy as np
from mido import Message


class Torus_Note():
    def __init__(self, pitch, velocity, R, r):
        if velocity == 0:
            return None

        self.pitch      = pitch
        self.note       = pitch % 12
        self.velocity   = velocity

        # Map to tonnetz
        self.theta  = (self.note * 7 % 12 / 12) * 2 * np.pi
        self.phi    = (self.note * 7 % 12 / 12) * 2 * np.pi

        self.x = (R + r * np.cos(self.theta)) * np.cos(self.phi)
        self.y = (R + r * np.cos(self.theta)) * np.sin(self.phi)
        self.z = r * np.sin(self.theta)

    def __repr__(self):
        return f"Note: x:{self.x}, y:{self.y}, z:{self.z}"
    
    @classmethod
    def from_array(cls, pitch, velocity, R, r):
        return cls(pitch, velocity, R, r)
    


class Note_Cloud():
    def __init__(self, active_notes, R, r):
        # Init
        self.note_coords = np.zeros((len(active_notes), 3), dtype=np.float32)

        phi     = 0
        theta   = 0

        for i in range(0, len(active_notes)):
            self.note_coords[i, :] = [active_notes[i].x,
                                      active_notes[i].y,
                                      active_notes[i].z]
            theta   += active_notes[i].theta
            phi     += active_notes[i].phi

        theta   = theta / len(active_notes)
        phi     = phi / len(active_notes)

        cntr_x = (R + r * np.cos(theta)) * np.cos(phi)
        cntr_y = (R + r * np.cos(theta)) * np.sin(phi)
        cntr_z = r * np.sin(theta)
        self.cntr_coords = np.array([[cntr_x, cntr_y, cntr_z]])

        self.diameter = 0


class Processor():
    def __init__(self, settings):
        self.R = settings['torus']['outer_radius']
        self.r = settings['torus']['inner_radius']
        
    def process_torus(self, note_pitches):
        # Get active notes
        active_notes = []
        for i in range(0, len(note_pitches)):
            if note_pitches[i] != 0:
                note = Torus_Note.from_array(i, note_pitches[i], self.R, self.r)
                active_notes.append(note)

        # # Get cloud params
        if len(active_notes) == 0:
            return None
        
        cloud = Note_Cloud(active_notes, self.R, self.r)

        # Notes     : 3 x N np array
        # Center    : 3 x 1 np array
        # Diameter  : float
        return {'note_coords'   : cloud.note_coords,
                'cntr_coords'   : cloud.cntr_coords,
                'diameter'      : cloud.diameter}