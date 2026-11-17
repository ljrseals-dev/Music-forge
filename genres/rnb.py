# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""R&B generator with a Markov melody (pitch chain + duration chain).

Design (after "Secrets of Markov Chains"):
  * states are scale degrees, not raw MIDI notes, so the line stays in key
  * separate chains for pitch (order 2, back-off) and duration (order 1)
  * constraint injection: chord tones on strong beats, leaps capped at a 4th
  * temperature schedule: sharpen into the cadence, flatten on the cadence note
  * seeded corpus below is the "idiom"; swap it to change the style
"""
from genre_base import *
from genre_base import GenrePatternGenerator
from markov_engine import (MarkovChain, conditional_entropy, repetition,
                           diversity)

PITCH_CORPUS = [   # scale degrees (0 = tonic, 7 = octave, -1 = leading tone below)
    [4, 4, 2, 0, 2, 4, 5, 4, 2, 0],
    [0, 2, 4, 5, 4, 2, 2, 0, -1, 0],
    [7, 6, 4, 4, 2, 4, 6, 4, 2, 0],
    [2, 4, 4, 5, 4, 2, 0, 2, 2, 0],
    [4, 5, 7, 6, 4, 2, 4, 2, 0, -1],
    [0, 0, 2, 4, 4, 5, 4, 2, 4, 2],
]
DURATION_CORPUS = []   # beats
for d in ([0.75, 0.25, 0.5, 0.5, 1.0, 0.5, 0.5, 0.75, 0.25, 1.0],
          [0.5, 0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5],
          [0.25, 0.75, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0],
          [1.0, 0.5, 0.5, 0.75, 0.25, 1.0, 0.5, 0.5]):
    DURATION_CORPUS.append(d)


class RnBGenerator(GenrePatternGenerator):
    GENRE = "rnb"
    DEFAULT_BPM = 74
    DEFAULT_MODE = "minor"
    SWING = 0.58
    HUMANIZE_TICKS = 5
    VELOCITY_JITTER = 6
    TEMPERATURE = 1.0
    LAYBACK = 8                      # ticks the backbeat/melody sits behind the grid
    CHORD_DEGREES = [0, 5, 3, 4]     # i  VI  iv  v

    def _define_structure(self):
        return [("intro", 4), ("verse", 16), ("chorus", 16), ("verse", 8), ("chorus", 16), ("outro", 4)]

    def _define_chords(self):
        out = []
        for d in self.CHORD_DEGREES:
            root = self.degree_root(d, 3)
            out.append([self.clamp(root + self.scale_pitch(d + k) - self.scale_pitch(d), 0, 127)
                        for k in (0, 2, 4, 6)])           # 7th chords
        return out

    # ---- Markov melody ------------------------------------------------
    def _markov_setup(self):
        if hasattr(self, "pitch_chain"):
            return
        self.pitch_chain = MarkovChain(order=2, alpha=0.1)
        self.dur_chain = MarkovChain(order=1, alpha=0.1)
        for seq in PITCH_CORPUS:
            self.pitch_chain.train(seq)
        for seq in DURATION_CORPUS:
            self.dur_chain.train(seq)
        self._p_hist, self._d_hist = [0], [1.0]
        self.mel_degrees, self.mel_durs = [], []

    def _allowed(self, root_deg, chord_only, prev):
        states = range(-1, 10)
        if chord_only:
            pool = [d for d in states if (d - root_deg) % 7 in (0, 2, 4)]
        else:
            pool = list(states)
        near = {d for d in pool if abs(d - prev) <= 3}
        return near or {prev}

    def gen_melody(self, bar, section, ci, bar_start, dt, ev):
        self._markov_setup()
        rd = self.CHORD_DEGREES[ci % len(self.CHORD_DEGREES)]
        phrase_bar = bar % 4
        energy = self.section_energy(section)
        tau = self.TEMPERATURE * (0.7 if phrase_bar >= 2 else 1.0)  # sharpen into cadence
        pos = 0.0
        while pos < 4.0 - 1e-9:
            dur = min(self.dur_chain.sample(self._d_hist, self.rng, tau), 4.0 - pos)
            self._d_hist.append(dur)
            last = pos + dur >= 4.0 - 1e-9
            cadence = phrase_bar == 3 and last
            if section == "intro" or self.rng.random() < 0.20 * (1.0 - energy):
                pos += dur                                    # rest
                continue
            strong = abs(pos % 2.0) < 1e-9
            allowed = self._allowed(rd, strong or cadence, self._p_hist[-1])
            deg = self.pitch_chain.sample(self._p_hist, self.rng,
                                          tau * (1.5 if cadence else 1.0), allowed)
            self._p_hist.append(deg)
            self.mel_degrees.append(deg)
            self.mel_durs.append(dur)
            weight = 10 if abs(pos % 4.0) < 1e-9 else (5 if strong else 0)
            if pos % 1.0:
                weight -= 4
            t = self.human_tick(bar_start + self.swing_tick(pos) + self.LAYBACK, 4)
            pitch = self.midi_note(self.key_pc, 5) + self.scale_pitch(deg)
            self.event_note(ev, t, int(dur * BEAT * 0.9), pitch,
                            self.human_vel(88 if section == "chorus" else 80, weight), 2)
            pos += dur

    def report(self):
        if not getattr(self, "mel_degrees", None):
            return {}
        return {
            "melody_notes": len(self.mel_degrees),
            "pitch_entropy_bits": round(conditional_entropy(self.mel_degrees), 3),
            "duration_entropy_bits": round(conditional_entropy(self.mel_durs), 3),
            "pitch_repetition": round(repetition(self.mel_degrees), 3),
            "pitch_diversity": diversity(self.mel_degrees),
            "temperature": self.TEMPERATURE,
        }

    # ---- rest of the band ---------------------------------------------
    def gen_bass(self, bar, section, ci, bar_start, dt, ev):
        root = self.chord_at(ci)[0] - 12
        for p, off, ln in [(0.0, 0, 1.25), (1.5, 0, 0.5), (2.75, 12, 0.75)]:
            t = self.human_tick(bar_start + self.swing_tick(p), 4)
            self.event_note(ev, t, int(BEAT * ln), root + off,
                            self.human_vel(96, 6 if p == 0 else 0), 0)

    def gen_chords(self, bar, section, ci, bar_start, dt, ev):
        chord = self.chord_at(ci)
        for p, ln in [(0.0, 1.5), (2.5, 1.25)]:
            t = self.human_tick(bar_start + self.swing_tick(p), 5)
            for n in chord:
                self.event_note(ev, t, int(BEAT * ln), n,
                                self.human_vel(66, 4 if p == 0 else 0), 1)

    def gen_drums(self, bar, section, bar_start, dt, ev):
        e = self.section_energy(section)
        for i in range(16):
            t = self.human_tick(bar_start + self.swing_tick(i * 0.25), 3)
            self.event_note(ev, t, THIRTYSECOND, CHH,
                            self.human_vel(50, 14 if i % 4 == 0 else (6 if i % 2 == 0 else 0)), 9)
        for pos in [0.0, 1.75, 2.5]:
            if pos == 0.0 or self.rng.random() < 0.7 * e:
                self.event_note(ev, bar_start + self.swing_tick(pos), THIRTYSECOND, KICK,
                                self.human_vel(104), 9)
        for pos in [1.0, 3.0]:
            t = self.human_tick(bar_start + int(pos * BEAT) + self.LAYBACK, 3)
            self.event_note(ev, t, THIRTYSECOND, SNARE, self.human_vel(106), 9)
            if section == "chorus":
                self.event_note(ev, t, THIRTYSECOND, CLAP, self.human_vel(84), 9)
        if self.rng.random() < 0.35:
            self.event_note(ev, bar_start + self.swing_tick(2.75), THIRTYSECOND, SNARE,
                            self.human_vel(36), 9)
