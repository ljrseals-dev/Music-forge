# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class BluesGenerator(GenrePatternGenerator):
    GENRE = "blues"
    DEFAULT_BPM = 100
    DEFAULT_MODE = "blues"
    SWING = 0.66
    HUMANIZE_TICKS = 3
    VELOCITY_JITTER = 5

    def _define_structure(self):
        return [("intro", 4), ("verse", 48), ("outro", 4)]

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        walk = [root, root + 4, root + 7, root + 9]
        for beat in range(4):
            t = self.human_tick(bar_start + self.swing_tick(beat), 3)
            self.event_note(ev, t, BEAT // 2, walk[beat],
                            self.human_vel(95, 6 if beat == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = self.chord_at(ci)
        for beat in [0.0, 2.5]:
            t = self.human_tick(bar_start + self.swing_tick(beat), 4)
            for n in chord:
                self.event_note(ev, t, int(EIGHTH * 1.5), n,
                                self.human_vel(78, 5), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 12
        scale = [0, 3, 5, 6, 7, 10]
        pos = [i * 0.5 for i in range(8)]
        for i, p in enumerate(pos):
            if self.rng.random() < 0.55:
                t = self.human_tick(bar_start + self.swing_tick(p), 4)
                self.event_note(ev, t, int(EIGHTH * 0.6),
                                root + scale[self.rng.randrange(len(scale))],
                                self.human_vel(90, 4), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        for i in range(8):
            t = self.human_tick(bar_start + self.swing_tick(i * 0.5), 4)
            self.event_note(ev, t, THIRTYSECOND, CHH,
                            self.human_vel(70, 6 if i % 2 == 0 else 0), 9)
        for pos in [0.0, 2.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, KICK,
                            self.human_vel(102), 9)
        for pos in [1.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, SNARE,
                            self.human_vel(108), 9)
