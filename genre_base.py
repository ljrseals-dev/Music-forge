# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""Base class for all genre pattern generators."""
from __future__ import annotations

import math
import random
from pathlib import Path

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

PPQ          = 480
BEAT         = PPQ
BAR          = 4 * BEAT
EIGHTH       = BEAT // 2
SIXTEENTH    = BEAT // 4
THIRTYSECOND = BEAT // 8

# General MIDI percussion
KICK, SNARE, CLAP = 36, 38, 39
CHH, OHH          = 42, 46
LTOM, MTOM, HTOM  = 45, 47, 50
RIDE, COWBELL     = 51, 56

MODE_INTERVALS = {
    "major":          [0, 2, 4, 5, 7, 9, 11],
    "minor":          [0, 2, 3, 5, 7, 8, 10],
    "dorian":         [0, 2, 3, 5, 7, 9, 10],
    "mixolydian":     [0, 2, 4, 5, 7, 9, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "blues":          [0, 3, 5, 6, 7, 10],
}

SECTION_ENERGY = {
    "intro": 0.55, "verse": 0.78, "chorus": 1.00,
    "bridge": 0.86, "break": 0.48, "outro": 0.62,
}


class GenrePatternGenerator:
    """Base class. Subclasses override the four gen_* methods."""

    GENRE         = "base"
    DEFAULT_BPM   = 120
    DEFAULT_MODE  = "minor"
    DEFAULT_KEY_PC = 0
    SWING         = 0.5
    HUMANIZE_TICKS = 2
    VELOCITY_JITTER = 3

    def __init__(self, seed=None, bpm=None, key_pc=None, mode=None):
        self.rng   = random.Random(seed)
        self.seed  = seed
        self.bpm   = bpm or self.DEFAULT_BPM
        self.key_pc = self.DEFAULT_KEY_PC if key_pc is None else key_pc
        self.mode  = mode or self.DEFAULT_MODE
        self.mode_intervals = MODE_INTERVALS[self.mode]
        self.structure   = self._define_structure()
        self.chords      = self._define_chords()
        self.progression = self._define_progression()

    # ---- configuration (override in subclasses) -----------------------
    def _define_structure(self):
        return [("intro", 8), ("verse", 16), ("chorus", 16)]

    def _define_chords(self):
        return [
            self._chord_from_degree(0, 3),
            self._chord_from_degree(3, 3),
            self._chord_from_degree(4, 3),
            self._chord_from_degree(0, 3),
        ]

    def _define_progression(self):
        return [0, 1, 2, 3]

    # ---- musical helpers ----------------------------------------------
    def clamp(self, v, lo, hi): return max(lo, min(hi, v))

    def midi_note(self, pc, octave):
        return self.clamp(12 * (octave + 1) + (pc % 12), 0, 127)

    def scale_pitch(self, degree):
        octs, idx = divmod(degree, len(self.mode_intervals))
        return 12 * octs + self.mode_intervals[idx]

    def degree_root(self, degree, octave):
        return self.midi_note(self.key_pc, octave) + self.scale_pitch(degree)

    def _chord_from_degree(self, degree, octave):
        root  = self.degree_root(degree, octave)
        third = root + self.scale_pitch(degree + 2) - self.scale_pitch(degree)
        fifth = root + self.scale_pitch(degree + 4) - self.scale_pitch(degree)
        return [self.clamp(n, 0, 127) for n in (root, third, fifth)]

    def swing_tick(self, beat_pos, swing=None):
        s = self.SWING if swing is None else swing
        whole = math.floor(beat_pos)
        frac  = beat_pos - whole
        if abs(frac - 0.5) < 1e-9:
            frac = s
        return int(round((whole + frac) * BEAT))

    def human_tick(self, tick, jitter=None, strength=1.0):
        j = self.HUMANIZE_TICKS if jitter is None else jitter
        if j <= 0:
            return max(0, int(tick))
        return max(0, int(tick) + int(round(self.rng.randint(-j, j) * strength)))

    def human_vel(self, base, accent=0, jitter=None, strength=1.0):
        j = self.VELOCITY_JITTER if jitter is None else jitter
        delta = 0 if j <= 0 else int(round(self.rng.randint(-j, j) * strength))
        return self.clamp(base + accent + delta, 1, 127)

    def event_note(self, events, start, dur, note, vel, channel):
        start = max(0, int(start)); dur = max(1, int(dur))
        note  = self.clamp(int(note), 0, 127)
        events.append((start, 1, Message("note_on", note=note,
                                         velocity=self.clamp(int(vel), 1, 127),
                                         channel=channel)))
        events.append((start + dur, 0, Message("note_off", note=note,
                                               velocity=0, channel=channel)))

    def event_cc(self, events, tick, control, value, channel):
        events.append((max(0, int(tick)), 2,
                       Message("control_change", control=control,
                               value=self.clamp(int(value), 0, 127),
                               channel=channel)))

    def write_events(self, track, events):
        events.sort(key=lambda x: (x[0], x[1]))
        last = 0
        for tick, _pri, msg in events:
            tick = max(last, tick)
            msg.time = tick - last
            track.append(msg)
            last = tick

    def section_energy(self, name):
        return SECTION_ENERGY.get(name, 0.8)

    def chord_at(self, chord_index):
        return self.chords[chord_index % len(self.chords)]

    def report(self):
        """Optional diagnostics (dict) printed by main.py --report."""
        return {}

    # ---- genre hooks (override) ---------------------------------------
    def gen_bass(self, bar, section, chord_index, bar_start, double_time, events): pass
    def gen_chords(self, bar, section, chord_index, bar_start, double_time, events): pass
    def gen_melody(self, bar, section, chord_index, bar_start, double_time, events): pass
    def gen_drums(self, bar, section, bar_start, double_time, events): pass

    # ---- arrangement engine (do not override) -------------------------
    def generate(self, filename=None):
        if filename is None:
            filename = f"{self.GENRE}_seed{self.seed}.mid"

        midi = MidiFile(type=1, ticks_per_beat=PPQ)
        conductor, bass, chords, melody, drums = (MidiTrack() for _ in range(5))
        midi.tracks.extend([conductor, bass, chords, melody, drums])

        conductor.append(MetaMessage("track_name", name=f"{self.GENRE} - Conductor", time=0))
        conductor.append(MetaMessage("set_tempo", tempo=bpm2tempo(self.bpm), time=0))
        conductor.append(MetaMessage("time_signature", numerator=4, denominator=4,
                                     clocks_per_click=24,
                                     notated_32nd_notes_per_beat=8, time=0))

        bass.append(MetaMessage("track_name", name="Bass", time=0))
        chords.append(MetaMessage("track_name", name="Chords", time=0))
        melody.append(MetaMessage("track_name", name="Melody", time=0))
        drums.append(MetaMessage("track_name", name="Drums", time=0))

        bass.append(Message("program_change",   program=33, channel=0, time=0))
        chords.append(Message("program_change", program=0,  channel=1, time=0))
        melody.append(Message("program_change", program=26, channel=2, time=0))

        bass_ev, chord_ev, mel_ev, drum_ev = [], [], [], []

        abs_bar, prog_cursor = 0, 0
        for section, n_bars in self.structure:
            double_time = section in ("chorus", "bridge")
            for local_bar in range(n_bars):
                chord_index = self.progression[prog_cursor % len(self.progression)]
                bar_start   = abs_bar * BAR
                self.gen_bass(abs_bar, section, chord_index, bar_start, double_time, bass_ev)
                self.gen_chords(abs_bar, section, chord_index, bar_start, double_time, chord_ev)
                self.gen_melody(abs_bar, section, chord_index, bar_start, double_time, mel_ev)
                self.gen_drums(abs_bar, section, bar_start, double_time, drum_ev)
                abs_bar += 1
                rate = 1 if double_time else 2
                if (local_bar + 1) % rate == 0:
                    prog_cursor += 1

        self.write_events(bass, bass_ev)
        self.write_events(chords, chord_ev)
        self.write_events(melody, mel_ev)
        self.write_events(drums, drum_ev)

        out = Path(filename)
        out.parent.mkdir(parents=True, exist_ok=True)
        midi.save(out)
        print(f"Saved: {out}")
        print(f"Genre: {self.GENRE} | BPM: {self.bpm} | Seed: {self.seed}")
        return out
