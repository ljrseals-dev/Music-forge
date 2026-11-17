# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class HipHopGenerator(GenrePatternGenerator):
    GENRE = "hiphop"
    DEFAULT_BPM = 90
    DEFAULT_MODE = "minor"
    SWING = 0.55
    HUMANIZE_TICKS = 5
    VELOCITY_JITTER = 6

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        for i, p in enumerate([0.0, 0.75, 2.0, 2.75]):
            t = self.human_tick(bar_start + self.swing_tick(p), 5)
            self.event_note(ev, t, int(SIXTEENTH * 2), root,
                            self.human_vel(103, 6 if i == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = self.chord_at(ci)
        for p in [0.0, 2.0]:
            t = self.human_tick(bar_start + p * BEAT, 5)
            for n in chord:
                self.event_note(ev, t, int(BEAT * 0.9), n,
                                self.human_vel(74, 4), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        if self.rng.random() < 0.35:
            return
        root = self.chord_at(ci)[0] + 12
        scale = self.mode_intervals
        for i in range(3):
            if self.rng.random() < 0.7:
                t = self.human_tick(bar_start + i * BEAT + EIGHTH, 5)
                self.event_note(ev, t, int(EIGHTH * 0.8),
                                root + scale[self.rng.randrange(5)],
                                self.human_vel(90), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        # Boom-bap: kick on 1 and 2&, snare on 2 & 4
        for pos in [0.0, 1.5]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, KICK,
                            self.human_vel(112), 9)
        for pos in [1.0, 3.0]:
            self.event_note(ev, bar_start + int(pos * BEAT), THIRTYSECOND, SNARE,
                            self.human_vel(110), 9)
        for i in range(8):
            t = self.human_tick(bar_start + self.swing_tick(i * 0.5), 5)
            self.event_note(ev, t, THIRTYSECOND, CHH,
                            self.human_vel(70, 8 if i % 2 == 0 else 0), 9)
