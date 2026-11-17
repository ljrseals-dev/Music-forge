# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class JazzGenerator(GenrePatternGenerator):
    GENRE = "jazz"
    DEFAULT_BPM = 200
    DEFAULT_MODE = "major"
    SWING = 0.64
    HUMANIZE_TICKS = 3
    VELOCITY_JITTER = 5

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        walk = [root, root + self.rng.choice([3, 4]), root + 7, root + 9]
        for beat in range(4):
            t = self.human_tick(bar_start + self.swing_tick(beat), 3)
            self.event_note(ev, t, BEAT // 2, walk[beat],
                            self.human_vel(95, 6 if beat == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = self.chord_at(ci)
        for beat in [0.0, 1.5, 2.5]:
            t = self.human_tick(bar_start + self.swing_tick(beat), 3)
            for n in chord:
                self.event_note(ev, t, int(EIGHTH * 0.9), n,
                                self.human_vel(78, 5), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 24
        scale = self.mode_intervals
        pos = [i * 0.5 for i in range(8)]
        for i, p in enumerate(pos):
            if self.rng.random() < 0.75:
                t = self.human_tick(bar_start + self.swing_tick(p), 3)
                deg = self.rng.randrange(7)
                self.event_note(ev, t, int(EIGHTH * 0.6),
                                root + scale[deg],
                                self.human_vel(92, 4), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        for i in range(8):
            t = self.human_tick(bar_start + self.swing_tick(i * 0.5), 3)
            self.event_note(ev, t, THIRTYSECOND, RIDE,
                            self.human_vel(78, 8 if i % 2 == 0 else 0), 9)
        self.event_note(ev, bar_start, THIRTYSECOND, KICK,
                        self.human_vel(100), 9)
        for pos in [1.0, 3.0]:
            t = self.human_tick(bar_start + self.swing_tick(pos), 3)
            self.event_note(ev, t, THIRTYSECOND, SNARE,
                            self.human_vel(85), 9)
