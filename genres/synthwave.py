# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class SynthwaveGenerator(GenrePatternGenerator):
    GENRE = "synthwave"
    DEFAULT_BPM = 100
    DEFAULT_MODE = "minor"
    SWING = 0.5
    HUMANIZE_TICKS = 1
    VELOCITY_JITTER = 3

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        for i in range(8):
            t = bar_start + i * EIGHTH
            n = root + (12 if i in (3, 7) else 0)
            self.event_note(ev, t, int(EIGHTH * 0.7), n,
                            self.human_vel(98, 6 if i % 2 == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = [n + 12 for n in self.chord_at(ci)]
        if section in ("intro", "outro"):
            for n in chord:
                self.event_note(ev, bar_start, BAR - 1, n,
                                self.human_vel(72), 1)
            return
        for i in range(16):
            t = bar_start + i * SIXTEENTH
            self.event_note(ev, t, SIXTEENTH - 1, chord[i % len(chord)],
                            self.human_vel(80), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 24
        pos = [i * 0.5 for i in range(8)]
        off = [0, 3, 5, 7, 5, 3, 0, -2]
        for i, p in enumerate(pos):
            t = bar_start + int(p * BEAT)
            self.event_note(ev, t, int(EIGHTH * 0.8), root + off[i % len(off)],
                            self.human_vel(92), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        for pos in [0.0, 1.0, 2.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, KICK,
                            self.human_vel(114), 9)
        for pos in [1.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, CLAP,
                            self.human_vel(102), 9)
        for pos in [0.5, 1.5, 2.5, 3.5]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, OHH,
                            self.human_vel(84), 9)
