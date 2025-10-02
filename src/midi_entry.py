import mido


def midi_listener(midi_in_name, midi_queue):
    with mido.open_input(midi_in_name) as port:
        for msg in port:
            midi_queue.put(msg)