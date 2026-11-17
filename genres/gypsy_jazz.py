# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
from genre_base import *
from genre_base import GenrePatternGenerator

class GypsyJazzGenerator(GenrePatternGenerator):
    GENRE = "gypsy_jazz"
    DEFAULT_BPM = 180
    DEFAULT_MODE = "harmonic_minor"
    SWING = 0.62
    HUMANIZE_TICKS = 4
    VELOCITY_JITTER = 4

    def _define_structure(self):
        return [("intro", 8), ("verse", 16), ("chorus", 16)]

    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0]
        if dt:
            arp = [0, 7, 12, 3, 7, 10, 12, 15]
            for i in range(16):
                t = self.human_tick(bar_start + self.swing_tick(i * 0.25), 3)
                n = root + arp[i % len(arp)]
                self.event_note(ev, t, SIXTEENTH, n,
                                self.human_vel(96, 7 if i % 4 == 0 else 0), 0)
        else:
            walk = [root, root + 3, root + 7, self.chord_at(ci)[2]]
            for beat in range(4):
                t = self.human_tick(bar_start + beat * BEAT, 2)
                self.event_note(ev, t, BEAT // 2, walk[beat],
                                self.human_vel(91, 8 if beat == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = self.chord_at(ci)
        positions = [1.0, 3.0]
        if dt and self.rng.random() < 0.65:
            positions += [0.75, 2.75]
        for pos in sorted(positions):
            t = self.human_tick(bar_start + self.swing_tick(pos), 3)
            for n in chord:
                self.event_note(ev, t, SIXTEENTH // 2, n,
                                self.human_vel(84, 8 if pos % 1 == 0 else 0), 1)

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] + 24
        offs = [0, 1, 2, 3, 2, 1, 0, -1]
        n_pos = 8 if dt else 6
        for i in range(n_pos):
            t = self.human_tick(bar_start + self.swing_tick(i * 0.5), 4)
            off = offs[i % len(offs)]
            if i % 4 == 3 and self.rng.random() < 0.55:
                off += self.rng.choice([-1, 1])
            self.event_note(ev, t, int(EIGHTH * 0.7), root + off,
                            self.human_vel(100 if dt else 92, 4), 2)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        e = self.section_energy(section)
        for i in range(8):
            t = self.human_tick(bar_start + i * EIGHTH, 4)
            self.event_note(ev, t, THIRTYSECOND, CHH,
                            self.human_vel(67, 10 if i % 2 == 0 else 0), 9)
        snares = [2.0] if section == "intro" else ([0.5, 1.5, 2.5, 3.5] if dt else [1.0, 3.0])
        for pos in snares:
            t = self.human_tick(bar_start + self.swing_tick(pos), 4)
            self.event_note(ev, t, THIRTYSECOND, SNARE,
                            self.human_vel(95 if dt else 87), 9)
        for pos in [0.0, 2.0]:
            if self.rng.random() < 0.65 * e:
                t = self.human_tick(bar_start + self.swing_tick(pos), 3)
                self.event_note(ev, t, THIRTYSECOND, KICK,
                                self.human_vel(84), 9)
