# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class FunkGenerator(GenrePatternGenerator):
    GENRE = "funk"
    DEFAULT_BPM = 108
    DEFAULT_MODE = "dorian"
    SWING = 0.56
    HUMANIZE_TICKS = 4
    VELOCITY_JITTER = 8

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        pos = [0.0, 0.5, 0.75, 1.5, 1.75, 2.0, 2.75, 3.25, 3.75]
        off = [0, 0, 7, 10, 12, 3, 5]
        for i, p in enumerate(pos):
            if self.rng.random() < 0.85:
                t = self.human_tick(bar_start + self.swing_tick(p), 4)
                self.event_note(ev, t, SIXTEENTH, root + off[i % len(off)],
                                self.human_vel(98, 6 if i % 3 == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = [n + 12 for n in self.chord_at(ci)]
        pos = [0.25, 0.75, 1.75, 2.25, 3.25, 3.75]
        for i, p in enumerate(pos):
            if self.rng.random() < 0.8:
                t = self.human_tick(bar_start + self.swing_tick(p), 5)
                for n in chord:
                    self.event_note(ev, t, THIRTYSECOND, n,
                                    self.human_vel(78, 6 if i % 2 == 0 else 0), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 12
        pos = [i * 0.5 for i in range(8)] if dt else [0.0, 0.5, 1.25, 2.0, 2.5, 3.25]
        off = [0, 2, 4, 3, 2, 0, 4, 2]
        for i, p in enumerate(pos):
            if self.rng.random() < 0.7:
                t = self.human_tick(bar_start + self.swing_tick(p), 5)
                self.event_note(ev, t, int(SIXTEENTH * 2),
                                root + off[i % len(off)],
                                self.human_vel(95 if dt else 88, 4), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        for i in range(16):
            t = bar_start + i * SIXTEENTH
            hat = OHH if i in (6, 14) and self.rng.random() < 0.45 else CHH
            self.event_note(ev, t, THIRTYSECOND, hat,
                            self.human_vel(63, 8 if i % 4 == 0 else 0), 9)
        for pos in [0.0, 1.75, 2.5]:
            if self.rng.random() < 0.82:
                self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, KICK,
                                self.human_vel(104), 9)
        for pos in [1.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, SNARE,
                            self.human_vel(108), 9)
        for pos in [0.75, 2.75, 3.5]:
            if self.rng.random() < 0.4:
                self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, SNARE,
                                self.human_vel(42), 9)
