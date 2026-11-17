# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class ReggaeGenerator(GenrePatternGenerator):
    GENRE = "reggae"
    DEFAULT_BPM = 76
    DEFAULT_MODE = "minor"
    SWING = 0.55
    HUMANIZE_TICKS = 4
    VELOCITY_JITTER = 6

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        for i, p in enumerate([0.0, 1.0, 2.0, 3.0]):
            n = root + (12 if i in (1, 3) else 0)
            t = self.human_tick(bar_start + self.swing_tick(p), 4)
            self.event_note(ev, t, int(BEAT * 0.8), n,
                            self.human_vel(100, 6 if i == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = self.chord_at(ci)
        for p in [0.5, 1.5, 2.5, 3.5]:
            t = self.human_tick(bar_start + self.swing_tick(p), 4)
            for n in chord:
                self.event_note(ev, t, SIXTEENTH, n,
                                self.human_vel(80, 4), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        if self.rng.random() > 0.5:
            return
        root = self.chord_at(ci)[0] + 12
        scale = self.mode_intervals
        for i in range(4):
            if self.rng.random() < 0.6:
                t = self.human_tick(bar_start + i * BEAT, 4)
                deg = self.rng.randrange(7)
                self.event_note(ev, t, int(BEAT * 0.6),
                                root + scale[deg],
                                self.human_vel(88), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        # One-drop: kick + snare on beat 3
        self.event_note(ev, bar_start + 2 * BEAT, THIRTYSECOND, KICK,
                        self.human_vel(110), 9)
        self.event_note(ev, bar_start + 2 * BEAT, THIRTYSECOND, SNARE,
                        self.human_vel(105), 9)
        for i in range(8):
            t = self.human_tick(bar_start + self.swing_tick(i * 0.5), 5)
            self.event_note(ev, t, THIRTYSECOND, CHH,
                            self.human_vel(72, 8 if i % 2 == 0 else 0), 9)
