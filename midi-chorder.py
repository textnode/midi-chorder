# Copyright 2026 Darren Elwood <darren@textnode.com> http://www.textnode.com @textnode
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at 
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mido

import time
import pprint
import itertools

chromatic_notes = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'G#', 'A', 'Bb', 'B']
chromatic_loop = itertools.cycle(chromatic_notes)

midi_notes = list(zip(range(128), chromatic_loop))

major_intervals = [2,2,1,2,2,2]

def select_using_intervals(interval_input):
    selector = [1] #tonic
    intervals = iter(itertools.chain(interval_input))
    for interval in intervals:
        for i in range(interval-1):
            selector.append(0)
        selector.append(1)
    return selector

def flatten_midi_note(midi_note_to_flatten):
    reversed_midi_notes = reversed(midi_notes)
    starting_point = itertools.dropwhile(lambda note: note != midi_note_to_flatten, reversed_midi_notes)
    next(starting_point)
    return(next(starting_point))

def sharpen_midi_note(midi_note_to_sharpen):
    starting_point = itertools.dropwhile(lambda note: note != midi_note_to_sharpen, midi_notes)
    next(starting_point)
    return(next(starting_point))

def build_scale(interval_input, tonic):
    selector = select_using_intervals(interval_input)
    starting_point = itertools.dropwhile(lambda note: note != tonic, chromatic_loop)
    diatonic_notes = list(itertools.compress(starting_point, selector))
    return diatonic_notes

def build_chord_from_midi_tonic(midi_tonic, notes):
    selector = select_using_intervals(major_intervals)
    starting_point = itertools.dropwhile(lambda note: note[0] != midi_tonic, iter(midi_notes))
    diatonic_notes = list(itertools.compress(starting_point, selector))

    notes_to_play = []
    for chord_note in notes:
        position = int(chord_note[-1])
        midi_note = (diatonic_notes[position-1])
        if chord_note[0] == 'b':
           notes_to_play.append(flatten_midi_note(midi_note))
        elif chord_note[0] == '#':
           notes_to_play.append(sharpen_midi_note(midi_note))
        else:
           notes_to_play.append(midi_note)

    return notes_to_play


def play_chord(port, midi_tonic, notes, veloc):
    notes_in_chord = build_chord_from_midi_tonic(midi_tonic, notes)
    print("%s, chord: %s notes:%s" % (midi_tonic, chord, notes_in_chord))
    for note_to_play in notes_in_chord:
        msg = mido.Message("note_on", note=note_to_play[0], velocity=veloc)
        outport.send(msg)


def stop_chord(port, midi_tonic, notes):
    notes_in_chord = build_chord_from_midi_tonic(midi_tonic, notes)
    for note_to_stop in notes_in_chord:
        msg = mido.Message("note_off", note=note_to_stop[0])
        outport.send(msg)

key_state = {}

channel_and_note_mapping = {
    (9, 40): "1",
    (9, 41): "2",
    (9, 42): "b3",
    (9, 43): "3",
    (9, 36): "4",
    (9, 37): "b5",
    (9, 38): "5",
    (9, 39): "#5"
}

with mido.open_input("Inp", virtual=True) as inport:
    with mido.open_output('Gen', virtual=True) as outport:
        while True:
            for msg in inport.iter_pending():
                print("msg: %s" % msg)
                key = (msg.channel, msg.note)
                if key in channel_and_note_mapping:
                    print("Maps to control key")
                    if msg.type == 'note_on':
                        key_state[key] = True
                    elif msg.type == 'note_off':
                        key_state[key] = False
                    pprint.pp(key_state)
                else:
                    chord = []
                    if msg.type == 'note_on':
                        for key in key_state:
                            if key_state[key] == True:
                                chord.append(channel_and_note_mapping[key])
                        play_chord(outport, msg.note, chord, msg.velocity)
                    elif msg.type == 'note_off':
                        for key in key_state:
                            if key_state[key] == True:
                                chord.append(channel_and_note_mapping[key])
                        pprint.pp(chord)
                        stop_chord(outport, msg.note, chord)

