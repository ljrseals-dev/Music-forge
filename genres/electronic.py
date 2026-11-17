# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class ElectronicGenerator(GenrePatternGenerator):
    GENRE = "electronic"
    DEFAULT_BPM = 124
    DEFAULT_MODE = "minor"
    SWING = 0.5
    HUMANIZE_TICKS = 1
    VELOCITY_JITTER = 3

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        for pos in [0.5, 1.5, 2.5, 3.5]:
            t = bar_start + int(pos * BEAT)
            n = root + (12 if pos == 3.5 and self.rng.random() < 0.3 else 0)
            self.event_note(ev, t, int(EIGHTH * 0.72), n,
                            self.human_vel(100, 5 if pos == 0.5 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = [n + 12 for n in self.chord_at(ci)]
        positions = [1.5, 3.5] if section == "break" else [0.5, 1.5, 2.5, 3.5]
        for i, pos in enumerate(positions):
            t = bar_start + int(pos * BEAT)
            for n in chord:
                self.event_note(ev, t, int(EIGHTH * 0.42), n,
                                self.human_vel(83, 7 if i == 0 else 0), 1)
            self.event_cc(ev, t, 74, 40 + 60 * self.section_energy(section), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 24
        pos = [i * 0.5 for i in range(8)]
        off = [0, 4, 7, 12, 7, 4, 0, -5]
        for i, p in enumerate(pos):
            t = bar_start + int(p * BEAT)
            self.event_note(ev, t, int(EIGHTH * 0.4), root + off[i % len(off)],
                            self.human_vel(92, 4), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        for pos in [0.0, 1.0, 2.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, KICK,
                            self.human_vel(116), 9)
        for pos in [1.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, CLAP,
                            self.human_vel(99), 9)
        for pos in [0.5, 1.5, 2.5, 3.5]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, OHH,
                            self.human_vel(88), 9)
