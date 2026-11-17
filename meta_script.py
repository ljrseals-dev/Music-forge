#!/usr/bin/env python3
# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""
MusicScript Forge (meta-generator)

Emits one standalone .py MIDI composer per composition. Each child bakes in
its own DNA (tempo, key, mode, structure, progression, swing, density,
humanization, motif, accent map, PROGRAM_MAP, CREATION_SEED) and is fully
independent of this file afterward.

Dependency for children:
    pip install mido

Examples:
    python meta_script.py
    python meta_script.py --count 8
    python meta_script.py --genre funk --count 4
    python meta_script.py --count 5 --run --out my_music
    python meta_script.py --count 10 --seed 123456
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import random
import re
import subprocess
import sys
from pathlib import Path

GENRES = ("gypsy_jazz", "rock", "funk", "house", "techno", "memphis")

KEY_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

MODE_INTERVALS = {
    "major":          [0, 2, 4, 5, 7, 9, 11],
    "minor":          [0, 2, 3, 5, 7, 8, 10],
    "dorian":         [0, 2, 3, 5, 7, 9, 10],
    "mixolydian":     [0, 2, 4, 5, 7, 9, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
}

GENRE_PROFILES = {
    "gypsy_jazz": {
        "bpms": [156, 168, 176, 184, 196, 208],
        "modes": ["minor", "harmonic_minor"],
        "swing": (0.58, 0.68), "density": (0.68, 0.95),
        "humanize_ticks": (2, 9), "vel_jitter": (2, 10),
        "progressions": [[0, 5, 1, 4], [0, 3, 2, 4], [0, 4, 0, 4], [0, 2, 5, 4]],
    },
    "rock": {
        "bpms": [92, 104, 116, 124, 136, 148],
        "modes": ["major", "minor", "mixolydian"],
        "swing": (0.50, 0.54), "density": (0.60, 0.90),
        "humanize_ticks": (1, 6), "vel_jitter": (2, 8),
        "progressions": [[0, 5, 3, 4], [0, 3, 4, 3], [0, 6, 5, 4], [0, 4, 5, 3]],
    },
    "funk": {
        "bpms": [92, 98, 104, 108, 112, 118],
        "modes": ["dorian", "mixolydian", "minor"],
        "swing": (0.52, 0.63), "density": (0.72, 1.00),
        "humanize_ticks": (2, 8), "vel_jitter": (4, 13),
        "progressions": [[0, 0, 3, 4], [0, 3, 0, 4], [0, 5, 4, 3], [0, 2, 3, 4]],
    },
    "house": {
        "bpms": [118, 120, 122, 124, 126, 128],
        "modes": ["minor", "dorian"],
        "swing": (0.50, 0.58), "density": (0.70, 0.96),
        "humanize_ticks": (0, 4), "vel_jitter": (2, 7),
        "progressions": [[0, 5, 3, 4], [0, 3, 5, 4], [0, 6, 5, 3], [0, 4, 5, 3]],
    },
    "techno": {
        "bpms": [126, 128, 130, 132, 134, 136],
        "modes": ["minor", "dorian"],
        "swing": (0.50, 0.56), "density": (0.62, 0.92),
        "humanize_ticks": (0, 3), "vel_jitter": (1, 6),
        "progressions": [[0, 0, 0, 0], [0, 5, 0, 3], [0, 6, 0, 5], [0, 3, 0, 4]],
    },
    "memphis": {
        "bpms": [124, 132, 138, 144, 150, 156],
        "modes": ["minor", "harmonic_minor"],
        "swing": (0.50, 0.61), "density": (0.58, 0.91),
        "humanize_ticks": (1, 7), "vel_jitter": (3, 11),
        "progressions": [[0, 0, 5, 4], [0, 3, 0, 6], [0, 6, 5, 0], [0, 4, 3, 0]],
    },
}

STRUCTURE_BANK = [
    [("intro", 4), ("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8), ("outro", 4)],
    [("intro", 4), ("verse", 16), ("chorus", 8), ("break", 4), ("chorus", 8), ("outro", 4)],
    [("intro", 8), ("verse", 8), ("chorus", 8), ("bridge", 8), ("chorus", 8), ("outro", 4)],
    [("intro", 4), ("verse", 12), ("chorus", 8), ("verse", 12), ("break", 4), ("chorus", 8)],
]

COPYRIGHT_HEADER = (
    "# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.\n"
    "# Licensed under the MIT License – see LICENSE file.\n"
)

CHILD_TEMPLATE = r'''#!/usr/bin/env python3
{header}
"""
AUTO-GENERATED STANDALONE MIDI COMPOSITION SCRIPT

Identity:
    title: {title}
    genre: {genre}
    created: {created}

The musical architecture below was selected by MusicScript Forge and baked
directly into this file. Running this file regenerates the same composition
logic deterministically.

Dependency:
    pip install mido
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from mido import Message, MetaMessage, MidiFile, MidiTrack, bpm2tempo

# ============================================================================
# BAKED-IN COMPOSITION DNA
# ============================================================================

TITLE = {title_repr}
GENRE = {genre_repr}
CREATION_SEED = {creation_seed}
BPM = {bpm}
KEY_PC = {key_pc}
KEY_NAME = {key_name_repr}
MODE = {mode_repr}
MODE_INTERVALS = {mode_intervals}
STRUCTURE = {structure}
DEGREES = {degrees}

PROGRAM_MAP = {program_map_repr}
# 'bass'   -> channel 0 program
# 'chords' -> channel 1 program
# 'melody' -> channel 2 program
# drums    -> channel 9, GM percussion

TICKS_PER_BEAT = 480
BEATS_PER_BAR = 4
BAR = TICKS_PER_BEAT * BEATS_PER_BAR
EIGHTH = TICKS_PER_BEAT // 2
SIXTEENTH = TICKS_PER_BEAT // 4
THIRTYSECOND = TICKS_PER_BEAT // 8

SWING = {swing:.5f}
DENSITY = {density:.5f}
HUMANIZE_TICKS = {humanize_ticks}
VELOCITY_JITTER = {velocity_jitter}
CHORD_SPREAD = {chord_spread}
MELODY_REGISTER = {melody_register}
BASS_REGISTER = {bass_register}
MOTIF = {motif}
ACCENT_MAP = {accent_map}

OUTPUT_MIDI = {output_midi_repr}

RNG = random.Random(CREATION_SEED)

KICK = 36
SNARE = 38
CLAP = 39
CLOSED_HAT = 42
OPEN_HAT = 46
LOW_TOM = 45
MID_TOM = 47
HIGH_TOM = 50
RIDE = 51
COWBELL = 56

# ============================================================================
# MUSICAL HELPERS
# ============================================================================

def clamp(value, lo, hi):
    return max(lo, min(hi, value))

def midi_note(pc, octave):
    return clamp(12 * (octave + 1) + (pc % 12), 0, 127)

def scale_pitch(degree, octave_shift=0):
    intervals = MODE_INTERVALS
    octaves, idx = divmod(degree, len(intervals))
    base = 12 * (octaves + octave_shift)
    return base + intervals[idx]

def degree_root(degree, base_octave):
    return midi_note(KEY_PC, base_octave) + scale_pitch(degree)

def chord_for_degree(degree, octave=3, spread=CHORD_SPREAD):
    root = degree_root(degree, octave)
    chord = [
        root,
        root + scale_pitch(degree + 2) - scale_pitch(degree),
        root + scale_pitch(degree + 4) - scale_pitch(degree),
    ]
    if GENRE in ("gypsy_jazz", "funk", "house") and RNG.random() < 0.72:
        chord.append(root + scale_pitch(degree + 6) - scale_pitch(degree))

    if spread == 1 and len(chord) >= 3:
        chord[1] += 12
    elif spread >= 2 and len(chord) >= 3:
        chord[1] += 12
        chord[-1] += 12

    return [clamp(n, 0, 127) for n in sorted(chord)]

def swing_tick(beat_position):
    whole = math.floor(beat_position)
    frac = beat_position - whole
    if abs(frac - 0.5) < 1e-8:
        frac = SWING
    return int(round((whole + frac) * TICKS_PER_BEAT))

def human_tick(tick, strength=1.0):
    if HUMANIZE_TICKS <= 0:
        return max(0, int(tick))
    jitter = int(round(RNG.randint(-HUMANIZE_TICKS, HUMANIZE_TICKS) * strength))
    return max(0, int(tick) + jitter)

def human_vel(base, accent=0, strength=1.0):
    j = int(round(RNG.randint(-VELOCITY_JITTER, VELOCITY_JITTER) * strength))
    return clamp(base + accent + j, 1, 127)

def event_note(events, start, duration, note, velocity, channel):
    start = max(0, int(start))
    duration = max(1, int(duration))
    events.append((start, 1, Message("note_on", note=clamp(int(note), 0, 127),
                                     velocity=clamp(int(velocity), 1, 127),
                                     channel=channel)))
    events.append((start + duration, 0,
                   Message("note_off", note=clamp(int(note), 0, 127),
                           velocity=0, channel=channel)))

def event_cc(events, tick, control, value, channel):
    events.append((max(0, int(tick)), 2,
                   Message("control_change", control=control,
                           value=clamp(int(value), 0, 127),
                           channel=channel)))

def write_events(track, events):
    events.sort(key=lambda x: (x[0], x[1]))
    last_tick = 0
    for tick, _priority, message in events:
        tick = max(last_tick, tick)
        message.time = tick - last_tick
        track.append(message)
        last_tick = tick

def section_energy(name):
    return {{
        "intro": 0.55,
        "verse": 0.78,
        "chorus": 1.00,
        "bridge": 0.86,
        "break": 0.48,
        "outro": 0.62,
    }}.get(name, 0.8)

# ============================================================================
# STYLE ENGINES
# ============================================================================

def gen_bass(events, bar_start, degree, section, bar_in_section):
    energy = section_energy(section)
    root = degree_root(degree, BASS_REGISTER)

    if GENRE == "gypsy_jazz":
        if section == "chorus":
            positions = [i * 0.25 for i in range(16)]
            for i, pos in enumerate(positions):
                if RNG.random() > DENSITY * energy:
                    continue
                arp = [0, 7, 12, 3, 7, 10, 12, 15]
                note = root + arp[(i + bar_in_section) % len(arp)]
                t = human_tick(bar_start + swing_tick(pos), 0.55)
                event_note(events, t, THIRTYSECOND * 2, note,
                           human_vel(96, 7 if i % 4 == 0 else 0), 0)
        else:
            walk = [0, 7, 12, 5]
            for beat in range(4):
                note = root + walk[(beat + bar_in_section) % len(walk)]
                t = human_tick(bar_start + beat * TICKS_PER_BEAT, 0.55)
                event_note(events, t, int(EIGHTH * 1.55), note,
                           human_vel(91, 8 if beat == 0 else 0), 0)

    elif GENRE == "rock":
        for i in range(8):
            if RNG.random() > DENSITY * energy:
                continue
            note = root + (12 if i in (3, 7) and RNG.random() < 0.55 else 0)
            t = human_tick(bar_start + swing_tick(i * 0.5), 0.45)
            event_note(events, t, int(EIGHTH * 0.82), note,
                       human_vel(101, 8 if i in (0, 4) else 0), 0)

    elif GENRE == "funk":
        positions = [0.0, 0.5, 0.75, 1.5, 1.75, 2.0, 2.75, 3.25, 3.75]
        choices = [0, 0, 7, 10, 12, 3, 5]
        for i, pos in enumerate(positions):
            if RNG.random() > DENSITY * energy:
                continue
            note = root + choices[(i + bar_in_section) % len(choices)]
            t = human_tick(bar_start + swing_tick(pos), 0.8)
            dur = SIXTEENTH if i % 3 else int(SIXTEENTH * 1.45)
            event_note(events, t, dur, note,
                       human_vel(98, ACCENT_MAP[i % len(ACCENT_MAP)]), 0)

    elif GENRE == "house":
        for i, pos in enumerate([0.5, 1.5, 2.5, 3.5]):
            note = root + (12 if i == 3 and RNG.random() < 0.28 else 0)
            t = human_tick(bar_start + swing_tick(pos), 0.18)
            event_note(events, t, int(EIGHTH * 0.72), note,
                       human_vel(100, 5 if i == 0 else 0, 0.55), 0)

    elif GENRE == "techno":
        for i, pos in enumerate([0.0, 0.75, 1.5, 2.0, 2.75, 3.5]):
            if RNG.random() > DENSITY * energy:
                continue
            note = root + ([0, 0, 12, 7][i % 4])
            t = human_tick(bar_start + swing_tick(pos), 0.15)
            event_note(events, t, SIXTEENTH, note,
                       human_vel(96, 5 if i % 3 == 0 else 0, 0.45), 0)

    elif GENRE == "memphis":
        positions = [0.0, 0.75, 1.5, 2.5, 3.25]
        offsets = [0, 0, 12, 6, 7, 3]
        for i, pos in enumerate(positions):
            if RNG.random() > DENSITY * energy:
                continue
            note = root + offsets[(i + bar_in_section) % len(offsets)]
            t = human_tick(bar_start + swing_tick(pos), 0.45)
            event_note(events, t, int(SIXTEENTH * 1.6), note,
                       human_vel(103, 9 if i == 0 else 0), 0)


def gen_chords(events, bar_start, degree, section, bar_in_section):
    energy = section_energy(section)
    chord = chord_for_degree(degree, 3 if GENRE != "house" else 4)

    if GENRE == "gypsy_jazz":
        positions = [1.0, 3.0]
        if section in ("chorus", "bridge") and RNG.random() < 0.65:
            positions += [0.75, 2.75]
        for pos in sorted(positions):
            t = human_tick(bar_start + swing_tick(pos), 0.65)
            for n in chord:
                event_note(events, t, int(SIXTEENTH * 0.9), n,
                           human_vel(84, 8 if pos % 1 else 0), 1)

    elif GENRE == "rock":
        power = [chord[0], chord[0] + 7, chord[0] + 12]
        for beat, pos in enumerate([0.0, 1.0, 2.0, 3.0]):
            if RNG.random() > (0.68 + 0.22 * energy):
                continue
            t = human_tick(bar_start + int(pos * TICKS_PER_BEAT), 0.4)
            for n in power:
                event_note(events, t, int(EIGHTH * 1.65), n,
                           human_vel(91, 8 if beat in (0, 2) else 0), 1)

    elif GENRE == "funk":
        positions = [0.25, 0.75, 1.75, 2.25, 3.25, 3.75]
        for i, pos in enumerate(positions):
            if RNG.random() > DENSITY * energy:
                continue
            t = human_tick(bar_start + swing_tick(pos), 0.85)
            for n in chord:
                event_note(events, t, int(THIRTYSECOND * 1.35), n + 12,
                           human_vel(78, ACCENT_MAP[i % len(ACCENT_MAP)]), 1)

    elif GENRE in ("house", "techno"):
        positions = [0.5, 1.5, 2.5, 3.5] if GENRE == "house" else [0.0, 2.0]
        if section == "break":
            positions = [1.5, 3.5]
        for i, pos in enumerate(positions):
            t = human_tick(bar_start + swing_tick(pos), 0.12)
            for n in chord:
                event_note(events, t, int(EIGHTH * (0.42 if GENRE == "house" else 0.9)),
                           n + 12, human_vel(83, 7 if i == 0 else 0, 0.5), 1)
            event_cc(events, t, 74, 40 + int(68 * energy) + i * 4, 1)

    elif GENRE == "memphis":
        positions = [0.0] if bar_in_section % 2 == 0 else [2.5]
        if section == "chorus":
            positions = [0.0, 2.5]
        for pos in positions:
            t = human_tick(bar_start + swing_tick(pos), 0.35)
            for n in chord[:3]:
                event_note(events, t, int(TICKS_PER_BEAT * 1.35), n + 12,
                           human_vel(72, 5), 1)


def gen_melody(events, bar_start, degree, section, bar_in_section):
    energy = section_energy(section)
    root_abs = degree_root(degree, MELODY_REGISTER)

    if section == "chorus":
        positions = [i * 0.5 for i in range(8)]
    elif section == "break":
        positions = [0.0, 1.5, 3.0]
    else:
        positions = [0.0, 0.5, 1.25, 2.0, 2.5, 3.25]

    for i, pos in enumerate(positions):
        if RNG.random() > DENSITY * energy:
            continue

        motif_degree = MOTIF[(i + bar_in_section) % len(MOTIF)]
        note = root_abs + scale_pitch(motif_degree)

        if GENRE == "gypsy_jazz" and i % 4 == 3 and RNG.random() < 0.55:
            note += RNG.choice([-1, 1])
        elif GENRE == "rock" and RNG.random() < 0.24:
            note += RNG.choice([0, 3, 7])
        elif GENRE == "funk" and i % 3 == 1:
            note += 12 if RNG.random() < 0.28 else 0
        elif GENRE == "memphis" and RNG.random() < 0.32:
            note -= 12

        t = human_tick(bar_start + swing_tick(pos),
                       0.78 if GENRE in ("funk", "gypsy_jazz") else 0.4)
        dur = int(EIGHTH * (0.42 if GENRE in ("funk", "memphis") else 0.72))
        vel = human_vel(92 if section != "chorus" else 105,
                        ACCENT_MAP[i % len(ACCENT_MAP)])
        event_note(events, t, dur, note, vel, 2)


def drum_hit(events, bar_start, pos, note, vel, dur=THIRTYSECOND, human=0.3):
    t = human_tick(bar_start + swing_tick(pos), human)
    event_note(events, t, dur, note, human_vel(vel, 0, human), 9)


def gen_drums(events, bar_start, section, bar_in_section):
    energy = section_energy(section)

    if GENRE == "gypsy_jazz":
        for i in range(8):
            drum_hit(events, bar_start, i * 0.5, CLOSED_HAT,
                     67 + (10 if i % 2 == 0 else 0), human=0.5)
        for pos in ([1.0, 3.0] if section != "intro" else [2.0]):
            drum_hit(events, bar_start, pos, SNARE, 87, human=0.55)
        for pos in [0.0, 2.0]:
            if RNG.random() < 0.65 * energy:
                drum_hit(events, bar_start, pos, KICK, 84, human=0.4)

    elif GENRE == "rock":
        for i in range(8):
            drum_hit(events, bar_start, i * 0.5, CLOSED_HAT,
                     76 + (8 if i % 2 == 0 else 0), human=0.35)
        for pos in [0.0, 2.0]:
            drum_hit(events, bar_start, pos, KICK, 106, human=0.25)
        if RNG.random() < 0.55:
            drum_hit(events, bar_start, 2.5, KICK, 92, human=0.3)
        for pos in [1.0, 3.0]:
            drum_hit(events, bar_start, pos, SNARE, 112, human=0.25)

    elif GENRE == "funk":
        for i in range(16):
            pos = i * 0.25
            hat = OPEN_HAT if i in (6, 14) and RNG.random() < 0.45 else CLOSED_HAT
            drum_hit(events, bar_start, pos, hat,
                     63 + ACCENT_MAP[i % len(ACCENT_MAP)], human=0.7)
        for pos in [0.0, 1.75, 2.5]:
            if RNG.random() < 0.82 * energy:
                drum_hit(events, bar_start, pos, KICK, 104, human=0.5)
        for pos in [1.0, 3.0]:
            drum_hit(events, bar_start, pos, SNARE, 108, human=0.5)
        for pos in [0.75, 2.75, 3.5]:
            if RNG.random() < 0.40 * energy:
                drum_hit(events, bar_start, pos, SNARE, 42, human=0.7)

    elif GENRE == "house":
        for pos in [0.0, 1.0, 2.0, 3.0]:
            drum_hit(events, bar_start, pos, KICK, 116, human=0.08)
        for pos in [1.0, 3.0]:
            drum_hit(events, bar_start, pos, CLAP, 99, human=0.12)
        for pos in [0.5, 1.5, 2.5, 3.5]:
            drum_hit(events, bar_start, pos, OPEN_HAT, 88, human=0.1)
        for i in range(8):
            if RNG.random() < 0.48 * energy:
                drum_hit(events, bar_start, i * 0.5, CLOSED_HAT, 55, human=0.15)

    elif GENRE == "techno":
        for pos in [0.0, 1.0, 2.0, 3.0]:
            drum_hit(events, bar_start, pos, KICK, 119, human=0.05)
        for i in range(16):
            if RNG.random() < (0.42 + 0.36 * energy):
                drum_hit(events, bar_start, i * 0.25, CLOSED_HAT,
                         52 + (16 if i % 4 == 2 else 0), human=0.12)
        for pos in [1.0, 3.0]:
            if section != "break":
                drum_hit(events, bar_start, pos, CLAP, 89, human=0.1)

    elif GENRE == "memphis":
        for pos in [0.0, 2.5]:
            if RNG.random() < 0.90 * energy:
                drum_hit(events, bar_start, pos, KICK, 115, human=0.25)
        drum_hit(events, bar_start, 2.0, SNARE, 112, human=0.28)

        hat_positions = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        if section == "chorus":
            hat_positions += [3.25, 3.75]
        for i, pos in enumerate(sorted(hat_positions)):
            if RNG.random() < (0.72 + 0.18 * energy):
                drum_hit(events, bar_start, pos, CLOSED_HAT,
                         68 + (12 if i % 2 == 0 else 0), human=0.35)

        if bar_in_section % 4 == 3 and section not in ("intro", "outro"):
            for pos, note in [(3.0, LOW_TOM), (3.25, MID_TOM), (3.5, HIGH_TOM)]:
                if RNG.random() < 0.65:
                    drum_hit(events, bar_start, pos, note, 86, human=0.32)


# ============================================================================
# ARRANGEMENT
# ============================================================================

def generate(filename=OUTPUT_MIDI):
    RNG.seed(CREATION_SEED)

    midi = MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)

    conductor = MidiTrack()
    bass_track = MidiTrack()
    chord_track = MidiTrack()
    melody_track = MidiTrack()
    drum_track = MidiTrack()

    midi.tracks.extend([conductor, bass_track, chord_track, melody_track, drum_track])

    conductor.append(MetaMessage("track_name", name=f"{{TITLE}} - Conductor", time=0))
    conductor.append(MetaMessage("set_tempo", tempo=bpm2tempo(BPM), time=0))
    conductor.append(MetaMessage("time_signature", numerator=4, denominator=4,
                                 clocks_per_click=24,
                                 notated_32nd_notes_per_beat=8, time=0))

    bass_track.append(MetaMessage("track_name", name="Bass", time=0))
    chord_track.append(MetaMessage("track_name", name="Chords", time=0))
    melody_track.append(MetaMessage("track_name", name="Melody", time=0))
    drum_track.append(MetaMessage("track_name", name="Drums", time=0))

    bass_track.append(Message("program_change",
                              program=PROGRAM_MAP["bass"], channel=0, time=0))
    chord_track.append(Message("program_change",
                               program=PROGRAM_MAP["chords"], channel=1, time=0))
    melody_track.append(Message("program_change",
                                program=PROGRAM_MAP["melody"], channel=2, time=0))

    bass_events, chord_events, melody_events, drum_events = [], [], [], []

    absolute_bar = 0
    progression_cursor = 0

    for section_name, section_bars in STRUCTURE:
        for local_bar in range(section_bars):
            degree = DEGREES[progression_cursor % len(DEGREES)]
            bar_start = absolute_bar * BAR
            harmonic_rate = 1 if section_name in ("chorus", "bridge") else 2

            gen_bass(bass_events, bar_start, degree, section_name, local_bar)
            gen_chords(chord_events, bar_start, degree, section_name, local_bar)
            gen_melody(melody_events, bar_start, degree, section_name, local_bar)
            gen_drums(drum_events, bar_start, section_name, local_bar)

            absolute_bar += 1
            if (local_bar + 1) % harmonic_rate == 0:
                progression_cursor += 1

    write_events(bass_track, bass_events)
    write_events(chord_track, chord_events)
    write_events(melody_track, melody_events)
    write_events(drum_track, drum_events)

    out = Path(filename)
    out.parent.mkdir(parents=True, exist_ok=True)
    midi.save(out)

    print(f"Saved: {{out}}")
    print(f"Title: {{TITLE}}")
    print(f"Genre: {{GENRE}}")
    print(f"Tempo: {{BPM}} BPM")
    print(f"Key: {{KEY_NAME}} {{MODE.replace('_', ' ')}}")
    print(f"Seed: {{CREATION_SEED}}")


if __name__ == "__main__":
    generate()
'''


def slugify(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text.strip())
    return re.sub(r"_+", "_", text).strip("_").lower()


def random_title(rng: random.Random, genre: str) -> str:
    first = ["Midnight", "Chrome", "Velvet", "Static", "Neon", "Dust",
             "Phantom", "Broken", "Black", "Electric", "Ghost", "Deep",
             "Afterhours", "Copper", "Moonlit", "Cold", "Hot", "Lost"]
    second = ["Circuit", "Boulevard", "Ritual", "Motion", "Signal", "Pocket",
              "Alley", "Mirage", "Machine", "Echo", "Transit", "Pressure",
              "Room", "Tape", "Cadence", "Drive", "Shadow", "Sequence"]
    tag = {
        "gypsy_jazz": ["Caravan", "Strings", "Cafe"],
        "rock":       ["Voltage", "Amp", "Highway"],
        "funk":       ["Pocket", "Grease", "Strut"],
        "house":      ["Floor", "Warehouse", "Pulse"],
        "techno":     ["Grid", "Factory", "Vector"],
        "memphis":    ["Tape", "Basement", "Night"],
    }[genre]
    return f"{rng.choice(first)} {rng.choice(second)} {rng.choice(tag)}"


def choose_config(rng: random.Random, genre: str | None = None) -> dict:
    genre = genre or rng.choice(GENRES)
    profile = GENRE_PROFILES[genre]

    mode = rng.choice(profile["modes"])
    key_pc = rng.randrange(12)
    bpm = rng.choice(profile["bpms"])
    structure = rng.choice(STRUCTURE_BANK)
    degrees = rng.choice(profile["progressions"])

    swing = rng.uniform(*profile["swing"])
    density = rng.uniform(*profile["density"])
    humanize_ticks = rng.randint(*profile["humanize_ticks"])
    velocity_jitter = rng.randint(*profile["vel_jitter"])

    motif_len = rng.choice([4, 5, 6, 8])
    motif = [rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 8]) for _ in range(motif_len)]
    motif[0] = rng.choice([0, 2, 4])

    accent_map = [rng.randint(-4, 12) for _ in range(rng.choice([4, 8]))]
    accent_map[0] = max(accent_map[0], 7)

    title = random_title(rng, genre)

    program_map = {
        "bass":   33,
        "chords": 4 if genre == "funk" else 0,
        "melody": 80 if genre in ("house", "techno") else 26,
    }

    return {
        "title": title,
        "genre": genre,
        "creation_seed": rng.getrandbits(63),
        "bpm": bpm,
        "key_pc": key_pc,
        "key_name": KEY_NAMES[key_pc],
        "mode": mode,
        "mode_intervals": MODE_INTERVALS[mode],
        "structure": structure,
        "degrees": degrees,
        "swing": swing,
        "density": density,
        "humanize_ticks": humanize_ticks,
        "velocity_jitter": velocity_jitter,
        "chord_spread": rng.choice([0, 0, 1, 1, 2]),
        "melody_register": rng.choice([4, 4, 5]),
        "bass_register": rng.choice([1, 2]),
        "motif": motif,
        "accent_map": accent_map,
        "program_map": program_map,
    }


def render_child(config: dict, created: str, midi_filename: str) -> str:
    return CHILD_TEMPLATE.format(
        header=COPYRIGHT_HEADER,
        title=config["title"],
        genre=config["genre"],
        created=created,
        title_repr=repr(config["title"]),
        genre_repr=repr(config["genre"]),
        creation_seed=config["creation_seed"],
        bpm=config["bpm"],
        key_pc=config["key_pc"],
        key_name_repr=repr(config["key_name"]),
        mode_repr=repr(config["mode"]),
        mode_intervals=repr(config["mode_intervals"]),
        structure=repr(config["structure"]),
        degrees=repr(config["degrees"]),
        program_map_repr=repr(config["program_map"]),
        swing=config["swing"],
        density=config["density"],
        humanize_ticks=config["humanize_ticks"],
        velocity_jitter=config["velocity_jitter"],
        chord_spread=config["chord_spread"],
        melody_register=config["melody_register"],
        bass_register=config["bass_register"],
        motif=repr(config["motif"]),
        accent_map=repr(config["accent_map"]),
        output_midi_repr=repr(midi_filename),
    )


def generate_scripts(count: int, out_dir: Path, genre: str | None,
                     master_seed: int | None, run_immediately: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)

    if master_seed is None:
        master_seed = random.SystemRandom().getrandbits(128)

    rng = random.Random(master_seed)
    created = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    manifest = {
        "created": created,
        "master_seed": master_seed,
        "count": count,
        "requested_genre": genre,
        "scripts": [],
    }

    for index in range(1, count + 1):
        cfg = choose_config(rng, genre)
        stem = f"{stamp}_{index:03d}_{slugify(cfg['genre'])}_{slugify(cfg['title'])}"
        py_name = stem + ".py"
        midi_name = stem + ".mid"

        text = render_child(cfg, created, midi_name)
        path = out_dir / py_name
        path.write_text(text, encoding="utf-8")

        entry = {
            "script": py_name,
            "midi": midi_name,
            "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "creation_seed": cfg["creation_seed"],
            **cfg,
        }

        if run_immediately:
            result = subprocess.run(
                [sys.executable, path.name],
                cwd=out_dir, capture_output=True, text=True,
            )
            entry["run_status"] = "ok" if result.returncode == 0 else "error"
            if result.returncode != 0:
                entry["run_error"] = result.stderr
                print(f"ERROR running {path.name}:\n{result.stderr}")
            else:
                print(result.stdout.strip())

        manifest["scripts"].append(entry)
        print(f"Created: {path}")

    manifest_path = out_dir / f"{stamp}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")
    print(f"Master seed: {master_seed}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate standalone Python MIDI-composition scripts.")
    parser.add_argument("--count", type=int, default=1,
                        help="Number of standalone scripts (default: 1)")
    parser.add_argument("--genre", choices=GENRES, default=None,
                        help="Force one genre; omit for random selection")
    parser.add_argument("--out", type=Path, default=Path("generated_music_scripts"),
                        help="Output directory")
    parser.add_argument("--seed", type=int, default=None,
                        help="Master seed for reproducible batch")
    parser.add_argument("--run", "--render", action="store_true", dest="run",
                        help="Execute each generated script immediately")

    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be >= 1")

    generate_scripts(args.count, args.out, args.genre, args.seed,
                     run_immediately=args.run)


if __name__ == "__main__":
    main()
