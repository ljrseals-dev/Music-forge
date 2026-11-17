# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class RockGenerator(GenrePatternGenerator):
    GENRE = "rock"
    DEFAULT_BPM = 120
    DEFAULT_MODE = "major"
    SWING = 0.5
    HUMANIZE_TICKS = 2
    VELOCITY_JITTER = 3

    def _define_structure(self):
        return [("intro", 4), ("verse", 16), ("chorus", 16), ("outro", 4)]

    def _define_chords(self):
        return [
            self._chord_from_degree(0, 3),
            self._chord_from_degree(4, 3),
            self._chord_from_degree(3, 3),
            self._chord_from_degree(4, 3),
        ]

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        for i in range(8):
            t = bar_start + i * EIGHTH
            n = root + (12 if i in (3, 7) and self.rng.random() < 0.55 else 0)
            self.event_note(ev, t, int(EIGHTH * 0.82), n,
                            self.human_vel(101, 8 if i in (0, 4) else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0]
        power = [root, root + 7, root + 12]
        for beat in range(4):
            t = bar_start + beat * BEAT
            for n in power:
                self.event_note(ev, t, int(EIGHTH * 1.65), n,
                                self.human_vel(91, 8 if beat in (0, 2) else 0), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 12
        scale = [0, 2, 4, 7, 9]
        pos = [i * 0.5 for i in range(8)] if dt else [0.0, 1.0, 2.0, 3.0]
        for i, p in enumerate(pos):
            if self.rng.random() < 0.7:
                self.event_note(ev, bar_start + int(p * BEAT),
                                int(EIGHTH * 0.7), root + scale[i % len(scale)],
                                self.human_vel(100 if dt else 92, 3), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        for i in range(8):
            self.event_note(ev, bar_start + i * EIGHTH, THIRTYSECOND, CHH,
                            self.human_vel(76, 8 if i % 2 == 0 else 0), 9)
        for pos in [0.0, 2.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, KICK,
                            self.human_vel(106), 9)
        for pos in [1.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, SNARE,
                            self.human_vel(112), 9)
