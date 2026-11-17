# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""Style knowledge base: every musical choice the planner can make, with weights.

This is DATA, not logic. To teach the Forge a new genre, add an entry to GENRES.
To retune taste, edit the weights. The numbers are heuristic starting points
(hand-set from idiom knowledge); they are meant to be re-calibrated later, e.g.
from MIDI you train on or from listening/Suno feedback.

Conventions
-----------
* weights are relative (they are normalised when sampled)
* positions are in beats inside a 4/4 bar (0.0 = beat 1, 0.5 = the "and")
* drum hit    = (pos, velocity, probability[, "dt"])   "dt" = only in chorus/bridge
* bass hit    = (pos, interval, length_beats, velocity)
                interval: semitones, or "r" root, "3" third, "5" fifth, "7" seventh, "o" octave
* comp hit    = (pos, length_beats, velocity[, "arp"])  "arp" = one chord tone per hit
* degrees     = 0-based scale degrees (0 = tonic, 7 = octave above, -1 = below tonic)
* GM programs = General MIDI program numbers (0-127)
"""

KICK, SNARE, CLAP, CHH, OHH, RIDE = 36, 38, 39, 42, 46, 51
LTOM, MTOM, HTOM = 45, 47, 50


def H8(main=68, accent=80, prob=1.0, note=CHH):
    return [(i * 0.5, accent if i % 2 == 0 else main, prob) for i in range(8)]


def H16(main=60, accent=74, off=50, prob=1.0, note=CHH):
    return [(i * 0.25, accent if i % 4 == 0 else (main if i % 2 == 0 else off), prob)
            for i in range(16)]


def ARP16(vel=76):
    return [(i * 0.25, 0.22, vel + (6 if i % 4 == 0 else 0), "arp") for i in range(16)]


GM_NAMES = {
    0: "acoustic piano", 4: "Rhodes electric piano", 5: "chorus electric piano",
    11: "vibraphone", 16: "organ", 21: "accordion", 22: "harmonica", 25: "steel-string guitar",
    26: "jazz guitar", 27: "clean electric guitar", 29: "overdriven guitar",
    30: "distorted guitar", 32: "upright bass", 33: "fingered bass", 34: "picked bass",
    35: "fretless bass", 36: "slap bass", 38: "synth bass", 39: "analog synth bass",
    40: "violin", 48: "string ensemble", 52: "choir", 53: "vocal oohs", 56: "trumpet",
    62: "synth brass", 65: "alto sax", 73: "flute", 80: "square lead", 81: "saw lead",
    89: "warm pad", 90: "polysynth",
}

# --------------------------------------------------------------------------
# song forms: list of (section, bars)
# --------------------------------------------------------------------------
FORMS = {
    "pop":        [("intro", 4), ("verse", 8), ("chorus", 8), ("verse", 8), ("chorus", 8), ("outro", 4)],
    "bridge":     [("intro", 4), ("verse", 8), ("chorus", 8), ("bridge", 8), ("chorus", 8), ("outro", 4)],
    "verse_heavy": [("intro", 4), ("verse", 16), ("chorus", 8), ("verse", 16), ("chorus", 8), ("outro", 4)],
    "loop":       [("intro", 8), ("verse", 16), ("break", 8), ("chorus", 16), ("outro", 8)],
    "twelve_bar": [("intro", 4), ("verse", 24), ("chorus", 12), ("verse", 12), ("outro", 4)],
    "head_solo":  [("intro", 4), ("verse", 16), ("chorus", 16), ("verse", 16), ("outro", 4)],
}

# --------------------------------------------------------------------------
# moods and energy: they bias the weights below, they never override genre rules
# --------------------------------------------------------------------------
MOODS = {
    "dark":       {"modes": {"minor": 2.0, "harmonic_minor": 1.6, "major": 0.3}, "genres": {"trap": 2.0, "hiphop": 1.4, "synthwave": 1.3}, "tempo_pos": 0.4, "rest": 0.0, "temp": -0.1, "intensity": 0.6},
    "bright":     {"modes": {"major": 2.5, "mixolydian": 1.6, "minor": 0.3}, "genres": {"funk": 1.5, "rock": 1.3, "house": 1.2, "reggae": 1.2}, "tempo_pos": 0.6, "rest": -0.05, "temp": 0.0, "intensity": 0.65},
    "chill":      {"modes": {"dorian": 1.6, "minor": 1.2}, "genres": {"rnb": 2.0, "reggae": 1.6, "hiphop": 1.4, "jazz": 1.3}, "tempo_pos": 0.15, "rest": 0.08, "temp": -0.1, "intensity": 0.3},
    "aggressive": {"modes": {"minor": 1.5, "harmonic_minor": 1.4}, "genres": {"rock": 2.0, "trap": 1.8, "house": 1.2}, "tempo_pos": 0.9, "rest": -0.08, "temp": 0.1, "intensity": 0.85},
    "romantic":   {"modes": {"major": 1.4, "minor": 1.2, "dorian": 1.2}, "genres": {"rnb": 2.5, "jazz": 1.5, "reggae": 1.2}, "tempo_pos": 0.1, "rest": 0.05, "temp": -0.05, "intensity": 0.3},
    "dreamy":     {"modes": {"dorian": 1.8, "major": 1.3}, "genres": {"synthwave": 2.5, "rnb": 1.5, "house": 1.2}, "tempo_pos": 0.3, "rest": 0.05, "temp": 0.0, "intensity": 0.4},
    "nostalgic":  {"modes": {"major": 1.4, "minor": 1.2}, "genres": {"synthwave": 2.0, "blues": 1.5, "jazz": 1.4, "gypsy_jazz": 1.4}, "tempo_pos": 0.35, "rest": 0.0, "temp": -0.05, "intensity": 0.45},
    "sad":        {"modes": {"minor": 2.5, "harmonic_minor": 1.2, "major": 0.2}, "genres": {"blues": 2.0, "rnb": 1.5, "jazz": 1.3}, "tempo_pos": 0.1, "rest": 0.08, "temp": -0.1, "intensity": 0.25},
    "energetic":  {"modes": {"major": 1.5, "mixolydian": 1.5, "dorian": 1.2}, "genres": {"house": 2.0, "funk": 1.8, "rock": 1.6, "gypsy_jazz": 1.5}, "tempo_pos": 0.85, "rest": -0.1, "temp": 0.1, "intensity": 0.85},
    "groovy":     {"modes": {"dorian": 2.0, "mixolydian": 1.8}, "genres": {"funk": 2.5, "rnb": 1.5, "hiphop": 1.3, "house": 1.3}, "tempo_pos": 0.5, "rest": 0.0, "temp": 0.05, "intensity": 0.6},
}
MOOD_WORDS = {"moody": "dark", "gritty": "dark", "menacing": "dark", "happy": "bright", "sunny": "bright",
              "uplifting": "bright", "mellow": "chill", "relaxed": "chill", "lofi": "chill", "lo-fi": "chill",
              "smooth": "romantic", "sexy": "romantic", "sensual": "romantic", "love": "romantic",
              "hard": "aggressive", "angry": "aggressive", "heavy": "aggressive", "ethereal": "dreamy",
              "retro": "nostalgic", "melancholy": "sad", "upbeat": "energetic", "party": "energetic",
              "club": "energetic", "funky": "groovy"}
ENERGY = {"low": {"tempo_pos": 0.15, "intensity": 0.3}, "medium": {"tempo_pos": 0.5, "intensity": 0.55},
          "high": {"tempo_pos": 0.85, "intensity": 0.85}}

# --------------------------------------------------------------------------
# genres
# --------------------------------------------------------------------------
GENRES = {
    "rnb": {
        "label": "R&B",
        "tags": {"rnb": 4, "r&b": 4, "soul": 3, "neo-soul": 3, "smooth": 2, "slow": 1, "vocal": 1, "ballad": 2, "love": 1, "groove": 1},
        "bpm": (66, 92), "swing": (0.56, 0.62), "layback": 8,
        "modes": {"minor": 5, "dorian": 3, "major": 1},
        "progressions": [([0, 5, 3, 4], 4), ([0, 3, 4, 0], 2), ([0, 5, 2, 4], 2), ([1, 4, 0, 5], 2)],
        "colors": {"seventh": 5, "ninth": 2, "triad": 1},
        "chord_bars": (2, 1), "keys": None, "forms": {"bridge": 3, "pop": 3, "verse_heavy": 1},
        "drums": [
            ("laid_back_backbeat", 0.45, 4, {KICK: [(0, 104, 1), (1.75, 96, .7), (2.5, 98, .6)], SNARE: [(1, 106, 1), (3, 106, 1), (2.75, 36, .35)], CHH: H16(50, 64, 44)}),
            ("half_time_pocket", 0.30, 3, {KICK: [(0, 104, 1), (2.5, 94, .7)], SNARE: [(2, 106, 1)], CHH: H8(62, 74)}),
            ("uptempo_neo_soul", 0.62, 3, {KICK: [(0, 104, 1), (1.5, 92, .6), (2.5, 98, .8)], SNARE: [(1, 108, 1), (3, 108, 1), (3.5, 40, .4)], CHH: H16(56, 72, 46)}),
        ],
        "bass": [("root_pocket", 4, [(0, "r", 1.25, 96), (1.5, "r", .5, 86), (2.75, "o", .75, 90)]),
                 ("sustain", 2, [(0, "r", 3.6, 92)]),
                 ("walk_syncopated", 2, [(0, "r", .75, 96), (1, "5", .5, 84), (2, "r", .75, 90), (3, "3", .5, 84)])],
        "comp": [("two_stabs", 4, [(0, 1.5, 70), (2.5, 1.25, 64)]), ("whole", 2, [(0, 3.8, 62)]),
                 ("syncopated", 2, [(.5, .5, 66), (1.5, .5, 60), (2.75, .75, 68)])],
        "instruments": {"bass": [(33, 3), (35, 2), (38, 2)], "chords": [(4, 4), (5, 2), (0, 2), (89, 1)],
                        "lead": [(53, 3), (11, 1), (65, 1), (80, 1)]},
        "motifs": [[4, 4, 2, 0, 2, 4, 5, 4, 2, 0], [0, 2, 4, 5, 4, 2, 2, 0, -1, 0], [7, 6, 4, 4, 2, 4, 6, 4, 2, 0], [2, 4, 4, 5, 4, 2, 0, 2, 2, 0]],
        "rhythms": [[.75, .25, .5, .5, 1, .5, .5, .75, .25, 1], [.5, .5, .5, .5, 1, 1, .5, .5], [.25, .75, .5, .5, .5, 1, .5, .5, 1]],
        "rest": 0.15, "temp": (0.9, 1.3), "lead_octave": 5, "fill": 0.1,
    },
    "hiphop": {
        "label": "boom-bap hip hop",
        "tags": {"hiphop": 4, "hip-hop": 4, "hip": 2, "boom": 2, "bap": 2, "rap": 3, "beat": 1, "sample": 1, "dusty": 1},
        "bpm": (82, 98), "swing": (0.55, 0.60), "layback": 6,
        "modes": {"minor": 5, "dorian": 2, "harmonic_minor": 1},
        "progressions": [([0, 5], 3), ([0, 3], 2), ([0, 0, 5, 4], 3), ([0, 2, 5, 4], 2)],
        "colors": {"seventh": 3, "triad": 2, "ninth": 1},
        "chord_bars": (2, 2), "keys": None, "forms": {"verse_heavy": 3, "pop": 2, "loop": 1},
        "drums": [
            ("boom_bap", 0.55, 4, {KICK: [(0, 110, 1), (1.5, 100, .8), (2.5, 104, .5)], SNARE: [(1, 108, 1), (3, 108, 1)], CHH: H8(66, 78)}),
            ("dusty_lazy", 0.40, 4, {KICK: [(0, 108, 1), (1.75, 96, .7), (2.5, 100, .7)], SNARE: [(1, 104, 1), (3, 104, 1)], CHH: H8(56, 68)}),
            ("boom_bap_ghost", 0.62, 4, {KICK: [(0, 110, 1), (1.5, 100, .7), (2.25, 96, .6)], SNARE: [(1, 110, 1), (3, 110, 1), (3.5, 40, .4), (2.75, 36, .3)], CHH: H8(66, 80)}),
        ],
        "bass": [("sub_sustain", 3, [(0, "r", 1.5, 104), (2, "r", 1.5, 100)]),
                 ("bouncy", 3, [(0, "r", 1.0, 104), (.75, "r", .5, 92), (2, "r", 1.0, 100), (2.75, "5", .5, 92)]),
                 ("whole_note", 1, [(0, "r", 3.6, 100)])],
        "comp": [("two_stabs", 3, [(0, .9, 74), (2, .9, 70)]), ("loop_stab", 3, [(0, .5, 76), (1.5, .5, 68), (2, .5, 72)])],
        "instruments": {"bass": [(33, 2), (39, 3), (38, 2)], "chords": [(4, 4), (0, 2), (11, 1), (16, 1)],
                        "lead": [(11, 2), (73, 2), (80, 1), (53, 1)]},
        "motifs": [[4, 4, 2, 0], [0, 2, 4, 2, 0, -1], [2, 2, 4, 5, 4, 2]],
        "rhythms": [[1, 1, .5, .5, 1], [.75, .25, 1, 1, 1], [.5, .5, 1, 1, .5, .5]],
        "rest": 0.30, "temp": (0.8, 1.1), "lead_octave": 5, "fill": 0.15,
    },
    "trap": {
        "label": "trap",
        "tags": {"trap": 4, "808": 3, "drill": 2, "hiphop": 1, "rap": 2, "hi-hats": 1, "hard": 1, "dark": 1},
        "bpm": (130, 160), "swing": (0.50, 0.52), "layback": 0,
        "modes": {"minor": 5, "harmonic_minor": 2, "dorian": 1},
        "progressions": [([0, 0, 5, 4], 3), ([0, 5, 3, 4], 2), ([0, 6, 5, 4], 3), ([0, 0, 0, 3], 1)],
        "colors": {"triad": 4, "seventh": 2},
        "chord_bars": (2, 2), "keys": None, "forms": {"loop": 3, "verse_heavy": 2, "pop": 2},
        "drums": [
            ("half_time_trap", 0.55, 4, {KICK: [(0, 112, 1), (.75, 100, .5), (1.75, 104, .7), (3.25, 100, .5)], SNARE: [(2, 108, 1)], CLAP: [(2, 90, 1)], CHH: H8(60, 74) + [(3.5, 60, .6), (3.625, 66, .6), (3.75, 72, .6), (3.875, 78, .6)]}),
            ("trap_rolls", 0.78, 4, {KICK: [(0, 112, 1), (1.5, 104, .6), (2.75, 100, .6), (3.25, 104, .5)], SNARE: [(2, 110, 1)], CLAP: [(2, 92, 1)], CHH: H8(58, 72) + [(1.75, 60, .7), (1.875, 66, .7), (3.5, 60, .8), (3.625, 68, .8), (3.75, 76, .8), (3.875, 84, .8)], OHH: [(3.25, 70, .5)]}),
            ("sparse_dark", 0.38, 3, {KICK: [(0, 112, 1), (2.5, 104, .6)], SNARE: [(2, 106, 1)], CHH: H8(52, 66)}),
        ],
        "bass": [("808_sustain", 4, [(0, "r", 1.6, 112), (1.75, "r", .5, 100), (2.5, "r", 1.25, 106)]),
                 ("808_sparse", 2, [(0, "r", 3.2, 110)]),
                 ("808_bounce", 2, [(0, "r", 1.0, 112), (1.5, "r", .5, 98), (2.75, "5", .75, 104)])],
        "comp": [("pad_whole", 4, [(0, 3.8, 64)]), ("two_stabs", 2, [(0, 1.0, 70), (2, 1.0, 66)])],
        "instruments": {"bass": [(38, 3), (39, 3)], "chords": [(89, 3), (4, 2), (0, 1), (52, 1)],
                        "lead": [(80, 2), (81, 2), (11, 1), (53, 1)]},
        "motifs": [[4, 4, 2, 4, 5, 4, 2, 0], [0, 2, 4, 2, 0, 2, 4, 5], [7, 6, 4, 2, 4, 2, 0]],
        "rhythms": [[.5, .5, .75, .25, 1, 1], [.75, .75, .5, 1, 1], [.5, .5, .5, .5, 2]],
        "rest": 0.28, "temp": (0.8, 1.15), "lead_octave": 5, "fill": 0.12,
    },
    "funk": {
        "label": "funk",
        "tags": {"funk": 4, "funky": 3, "groove": 2, "slap": 2, "pocket": 2, "james": 1, "disco": 1},
        "bpm": (96, 116), "swing": (0.52, 0.60), "layback": 0,
        "modes": {"dorian": 5, "mixolydian": 3, "minor": 1},
        "progressions": [([0, 0, 3, 4], 3), ([0, 3, 0, 4], 3), ([0, 5, 4, 3], 2), ([0, 2, 3, 4], 2)],
        "colors": {"seventh": 5, "ninth": 3, "triad": 1},
        "chord_bars": (2, 1), "keys": None, "forms": {"bridge": 3, "pop": 3, "loop": 1},
        "drums": [
            ("tight_16th_funk", 0.72, 4, {KICK: [(0, 104, 1), (1.75, 98, .8), (2.5, 100, .7)], SNARE: [(1, 108, 1), (3, 108, 1), (.75, 42, .4), (2.75, 42, .4), (3.5, 40, .4)], CHH: H16(62, 76, 52), OHH: [(1.5, 72, .45), (3.5, 72, .45)]}),
            ("half_funk", 0.50, 4, {KICK: [(0, 104, 1), (1.75, 96, .7)], SNARE: [(1, 106, 1), (3, 106, 1), (2.75, 40, .4)], CHH: H8(66, 78)}),
        ],
        "bass": [("syncopated_16ths", 4, [(0, "r", .3, 100), (.5, "r", .25, 88), (.75, "5", .25, 92), (1.5, "7", .25, 90), (1.75, "o", .25, 94), (2, "5", .3, 96), (2.75, "3", .25, 88), (3.25, "5", .25, 90)]),
                 ("octave_slap", 3, [(0, "r", .3, 102), (.5, "o", .25, 90), (1.5, "r", .3, 94), (2, "o", .25, 96), (2.75, "5", .3, 92), (3.5, "r", .3, 94)])],
        "comp": [("choppy", 4, [(.25, .12, 78), (.75, .12, 72), (1.75, .12, 78), (2.25, .12, 72), (3.25, .12, 78), (3.75, .12, 72)]),
                 ("sparse_stab", 2, [(.5, .2, 80), (2.5, .2, 80)])],
        "instruments": {"bass": [(36, 3), (33, 2), (34, 1), (35, 1)], "chords": [(4, 3), (16, 2), (27, 3), (26, 1)],
                        "lead": [(65, 2), (56, 2), (81, 1), (62, 1)]},
        "motifs": [[0, 2, 4, 3, 2, 0, 4, 2], [4, 4, 2, 0, 2, 4, 4, 5], [0, 0, 2, 4, 5, 4, 2, 0]],
        "rhythms": [[.5, .25, .25, .5, .5, .5, 1, .5, .25, .25], [.75, .25, .5, .5, 1, .5, .5]],
        "rest": 0.12, "temp": (0.9, 1.2), "lead_octave": 5, "fill": 0.2,
    },
    "rock": {
        "label": "rock",
        "tags": {"rock": 4, "guitar": 2, "band": 1, "riff": 2, "punk": 1, "pop-rock": 2, "indie": 1, "distorted": 1},
        "bpm": (100, 152), "swing": (0.50, 0.52), "layback": 0,
        "modes": {"major": 3, "mixolydian": 2, "minor": 3},
        "progressions": [([0, 5, 3, 4], 3), ([0, 3, 4, 3], 3), ([0, 6, 5, 4], 2), ([0, 4, 5, 3], 3)],
        "colors": {"power": 4, "triad": 2},
        "chord_bars": (2, 1), "keys": [4, 9, 2, 7, 0, 5], "forms": {"pop": 3, "bridge": 3, "verse_heavy": 1},
        "drums": [
            ("straight_8ths", 0.6, 4, {KICK: [(0, 106, 1), (2, 104, 1), (2.5, 92, .5)], SNARE: [(1, 112, 1), (3, 112, 1)], CHH: H8(74, 86)}),
            ("driving_open", 0.82, 4, {KICK: [(0, 108, 1), (1.5, 96, .5), (2, 104, 1), (2.5, 96, .6)], SNARE: [(1, 114, 1), (3, 114, 1)], CHH: H8(74, 86), OHH: [(3.5, 84, .5, "dt")]}),
            ("half_time_rock", 0.5, 3, {KICK: [(0, 108, 1), (2.5, 98, .6)], SNARE: [(2, 114, 1)], CHH: H8(70, 82)}),
        ],
        "bass": [("eighth_pulse", 4, [(i * .5, "o" if i in (3, 7) else "r", .45, 100 if i % 2 == 0 else 90) for i in range(8)]),
                 ("quarter_drive", 2, [(i, "r", .9, 98) for i in range(4)]),
                 ("root_fifth", 2, [(0, "r", .9, 100), (1, "r", .9, 94), (2, "5", .9, 98), (3, "r", .9, 94)])],
        "comp": [("power_quarters", 4, [(i, .9, 92 if i % 2 == 0 else 86) for i in range(4)]),
                 ("eighth_chug", 2, [(i * .5, .4, 90 if i % 2 == 0 else 82) for i in range(8)])],
        "instruments": {"bass": [(34, 3), (33, 2)], "chords": [(29, 3), (30, 3), (27, 1)], "lead": [(29, 2), (30, 2), (81, 1)]},
        "motifs": [[0, 2, 4, 4, 2, 4, 5, 4], [4, 4, 5, 7, 5, 4, 2, 0], [0, 0, 2, 4, 2, 4, 5, 2]],
        "rhythms": [[1, .5, .5, 1, 1], [.5, .5, .5, .5, 1, 1], [1, 1, .5, .5, 1]],
        "rest": 0.12, "temp": (0.8, 1.1), "lead_octave": 5, "fill": 0.3,
    },
    "jazz": {
        "label": "jazz",
        "tags": {"jazz": 4, "swing": 2, "bebop": 3, "standard": 2, "trio": 1, "sax": 1, "walking": 2, "lounge": 1},
        "bpm": (110, 200), "swing": (0.62, 0.68), "layback": 0,
        "modes": {"major": 4, "dorian": 2, "mixolydian": 1},
        "progressions": [([1, 4, 0, 5], 4), ([0, 5, 1, 4], 3), ([0, 3, 1, 4], 2), ([0, 1, 2, 3], 1)],
        "colors": {"ninth": 3, "seventh": 4},
        "chord_bars": (1, 1), "keys": None, "forms": {"head_solo": 3, "pop": 2},
        "drums": [
            ("ride_swing", 0.5, 4, {RIDE: [(0, 78, 1), (1, 70, 1), (1.5, 64, 1), (2, 78, 1), (3, 70, 1), (3.5, 64, 1)], CHH: [(1, 60, 1), (3, 60, 1)], KICK: [(0, 58, .8), (1, 54, .8), (2, 58, .8), (3, 54, .8)], SNARE: [(2.5, 40, .4), (3.5, 38, .3)]}),
            ("brush_ballad", 0.28, 3, {RIDE: [(0, 62, 1), (1, 58, 1), (2, 62, 1), (3, 58, 1)], CHH: [(1, 50, 1), (3, 50, 1)], KICK: [(0, 50, .6)]}),
        ],
        "bass": [("walking", 5, [(0, "r", .95, 94), (1, "3", .95, 88), (2, "5", .95, 90), (3, "7", .95, 88)]),
                 ("two_feel", 2, [(0, "r", 1.9, 92), (2, "5", 1.9, 88)])],
        "comp": [("comping", 4, [(0, .8, 74), (1.5, .6, 68), (2.5, .6, 70)]), ("charleston", 2, [(0, .6, 76), (1.5, .6, 70)])],
        "instruments": {"bass": [(32, 4), (33, 1)], "chords": [(0, 3), (26, 3), (4, 1)], "lead": [(65, 2), (56, 2), (11, 2), (73, 1), (26, 1)]},
        "motifs": [[0, 1, 2, 4, 3, 2, 1, 0], [4, 3, 2, 1, 2, 4, 5, 4], [2, 4, 6, 4, 3, 1, 0, -1]],
        "rhythms": [[.5, .5, .5, .5, .5, .5, 1], [.5, .5, 1, .5, .5, 1], [.5, .5, .5, .5, 1, 1]],
        "rest": 0.18, "temp": (1.0, 1.3), "lead_octave": 5, "fill": 0.1,
    },
    "blues": {
        "label": "blues",
        "tags": {"blues": 4, "12-bar": 3, "shuffle": 3, "delta": 1, "chicago": 2, "harmonica": 1, "slow-blues": 2},
        "bpm": (72, 120), "swing": (0.64, 0.70), "layback": 4,
        "modes": {"mixolydian": 4, "minor": 3, "dorian": 1},
        "progressions": [([0, 0, 0, 0, 3, 3, 0, 0, 4, 3, 0, 4], 6), ([0, 0, 3, 3, 0, 4, 0, 4], 1)],
        "colors": {"seventh": 5, "triad": 1},
        "chord_bars": (1, 1), "keys": [4, 9, 2, 7, 0, 5], "forms": {"twelve_bar": 1},
        "drums": [
            ("shuffle", 0.5, 4, {KICK: [(0, 102, 1), (2, 98, 1)], SNARE: [(1, 108, 1), (3, 108, 1)], CHH: [(i * .5, 76 if i % 2 == 0 else 62, 1) for i in range(8)]}),
            ("slow_blues", 0.3, 3, {KICK: [(0, 98, 1), (2.5, 90, .5)], SNARE: [(1, 100, 1), (3, 100, 1)], RIDE: [(i * .5, 64 if i % 2 == 0 else 54, 1) for i in range(8)]}),
        ],
        "bass": [("walking_shuffle", 4, [(0, "r", .9, 94), (1, "3", .9, 88), (2, "5", .9, 90), (3, "3", .9, 88)]),
                 ("boogie", 3, [(i * .5, ("r", "r", "3", "3", "5", "5", "3", "3")[i], .45, 92 if i % 2 == 0 else 84) for i in range(8)])],
        "comp": [("organ_pad", 2, [(0, 3.8, 66)]), ("shuffle_stabs", 3, [(0, 1.5, 76), (2.5, 1.25, 70)])],
        "instruments": {"bass": [(33, 3), (32, 1)], "chords": [(16, 2), (0, 2), (26, 2), (27, 1)], "lead": [(29, 3), (26, 1), (27, 1), (22, 2)]},
        "motifs": [[0, 2, 3, 4, 3, 2, 0], [4, 4, 6, 4, 3, 2, 0], [0, 0, 2, 3, 3, 4, 3, 2]],
        "rhythms": [[.5, .5, 1, .5, .5, 1], [1, .5, .5, 1, 1], [.5, .5, .5, .5, 2]],
        "rest": 0.22, "temp": (0.9, 1.2), "lead_octave": 5, "fill": 0.1,
    },
    "reggae": {
        "label": "reggae",
        "tags": {"reggae": 4, "dub": 3, "one-drop": 3, "skank": 2, "ska": 1, "island": 1, "roots": 2, "rocksteady": 2},
        "bpm": (68, 84), "swing": (0.54, 0.58), "layback": 6,
        "modes": {"minor": 4, "major": 2, "dorian": 2},
        "progressions": [([0, 3], 3), ([0, 4, 5, 3], 2), ([0, 5, 3, 4], 2), ([0, 3, 4, 3], 2)],
        "colors": {"triad": 5, "seventh": 1},
        "chord_bars": (2, 2), "keys": None, "forms": {"pop": 3, "verse_heavy": 2},
        "drums": [
            ("one_drop", 0.35, 4, {KICK: [(2, 108, 1)], SNARE: [(2, 104, 1)], CHH: H8(66, 74)}),
            ("rockers", 0.5, 4, {KICK: [(0, 104, 1), (1, 98, 1), (2, 104, 1), (3, 98, 1)], SNARE: [(2, 104, 1)], CHH: H8(66, 76)}),
        ],
        "bass": [("dub_root", 4, [(0, "r", 1.2, 104), (1, "o", .8, 96), (2, "r", 1.2, 100), (3, "5", .8, 92)]),
                 ("melodic_sparse", 3, [(0, "r", .9, 100), (1.5, "5", .4, 90), (2, "r", .9, 98), (3, "3", .8, 90)])],
        "comp": [("skank", 5, [(.5, .4, 82), (1.5, .4, 78), (2.5, .4, 82), (3.5, .4, 78)])],
        "instruments": {"bass": [(33, 3), (34, 1), (35, 1)], "chords": [(16, 3), (27, 3), (4, 1)], "lead": [(22, 1), (65, 2), (56, 2), (11, 1)]},
        "motifs": [[4, 4, 2, 0], [0, 2, 4, 2, 0], [2, 4, 5, 4, 2]],
        "rhythms": [[1, 1, 2], [1.5, .5, 1, 1], [1, 1, 1, 1]],
        "rest": 0.35, "temp": (0.8, 1.1), "lead_octave": 5, "fill": 0.05,
    },
    "house": {
        "label": "house",
        "tags": {"house": 4, "club": 2, "dance": 2, "edm": 2, "four-on-the-floor": 3, "disco": 1, "deep": 1, "electronic": 2},
        "bpm": (118, 128), "swing": (0.50, 0.55), "layback": 0,
        "modes": {"minor": 4, "dorian": 3, "major": 1},
        "progressions": [([0, 5, 3, 4], 3), ([0, 3, 5, 4], 2), ([0, 6, 5, 3], 2), ([0, 0, 3, 4], 2)],
        "colors": {"seventh": 3, "ninth": 3, "triad": 2},
        "chord_bars": (2, 2), "keys": None, "forms": {"loop": 4, "pop": 1},
        "drums": [
            ("four_on_floor", 0.7, 4, {KICK: [(0, 116, 1), (1, 114, 1), (2, 116, 1), (3, 114, 1)], CLAP: [(1, 100, 1), (3, 100, 1)], OHH: [(.5, 88, 1), (1.5, 88, 1), (2.5, 88, 1), (3.5, 88, 1)], CHH: H16(50, 56, 44, .45)}),
            ("minimal_house", 0.5, 3, {KICK: [(0, 114, 1), (1, 112, 1), (2, 114, 1), (3, 112, 1)], CLAP: [(1, 92, 1), (3, 92, 1)], CHH: [(i * .5 + .25, 62, 1) for i in range(8)]}),
        ],
        "bass": [("offbeat", 4, [(.5, "r", .35, 100), (1.5, "r", .35, 96), (2.5, "r", .35, 100), (3.5, "o", .35, 94)]),
                 ("rolling_16ths", 2, [(i * .25, "o" if i % 8 == 7 else "r", .2, 96 if i % 4 == 0 else 86) for i in range(16)])],
        "comp": [("offbeat_stabs", 4, [(.5, .3, 84), (1.5, .3, 80), (2.5, .3, 84), (3.5, .3, 80)]), ("pad", 3, [(0, 3.9, 70)])],
        "instruments": {"bass": [(38, 3), (39, 3)], "chords": [(89, 2), (90, 2), (4, 2), (0, 1)], "lead": [(81, 3), (80, 2), (11, 1)]},
        "motifs": [[0, 2, 4, 2], [4, 4, 2, 2, 0, 0, 2, 4], [0, 4, 2, 4, 0, 2]],
        "rhythms": [[.5, .5, .5, .5, 1, 1], [.25, .25, .5, .5, .5, .5, .5, 1]],
        "rest": 0.20, "temp": (0.7, 1.0), "lead_octave": 5, "fill": 0.25,
    },
    "synthwave": {
        "label": "synthwave",
        "tags": {"synthwave": 4, "retro": 2, "80s": 3, "outrun": 3, "neon": 2, "retrowave": 3, "synth": 2, "cinematic": 1},
        "bpm": (90, 118), "swing": (0.50, 0.51), "layback": 0,
        "modes": {"minor": 5, "major": 1, "dorian": 1},
        "progressions": [([0, 5, 2, 6], 4), ([0, 2, 5, 6], 2), ([0, 3, 5, 4], 2)],
        "colors": {"triad": 3, "seventh": 3},
        "chord_bars": (2, 2), "keys": None, "forms": {"bridge": 3, "pop": 2, "loop": 2},
        "drums": [
            ("gated_pop", 0.6, 4, {KICK: [(0, 112, 1), (1, 110, 1), (2, 112, 1), (3, 110, 1)], SNARE: [(1, 108, 1), (3, 108, 1)], CLAP: [(1, 88, 1), (3, 88, 1)], CHH: H8(66, 78)}),
            ("pulse", 0.45, 3, {KICK: [(0, 110, 1), (2, 108, 1), (2.5, 94, .5)], SNARE: [(1, 106, 1), (3, 106, 1)], CHH: H8(60, 72)}),
        ],
        "bass": [("pumping_8ths", 5, [(i * .5, "o" if i in (3, 7) else "r", .45, 98 if i % 2 == 0 else 90) for i in range(8)]),
                 ("driving_16ths", 2, [(i * .25, "r", .2, 96 if i % 4 == 0 else 84) for i in range(16)])],
        "comp": [("arp_16ths", 4, ARP16(74)), ("pad", 3, [(0, 3.9, 66)])],
        "instruments": {"bass": [(38, 3), (39, 2)], "chords": [(89, 3), (90, 2), (48, 2)], "lead": [(81, 3), (80, 2), (62, 1)]},
        "motifs": [[4, 5, 7, 5, 4, 2, 4], [7, 6, 4, 2, 4, 6, 7], [0, 2, 4, 7, 6, 4, 2]],
        "rhythms": [[1, 1, 1, 1], [1, .5, .5, 1, 1], [1.5, .5, 1, 1]],
        "rest": 0.15, "temp": (0.7, 1.0), "lead_octave": 5, "fill": 0.2,
    },
    "gypsy_jazz": {
        "label": "gypsy jazz",
        "tags": {"gypsy": 4, "manouche": 4, "django": 3, "hot-club": 3, "swing": 1, "violin": 1, "acoustic": 1, "jazz": 1},
        "bpm": (150, 210), "swing": (0.60, 0.68), "layback": 0,
        "modes": {"harmonic_minor": 4, "minor": 2},
        "progressions": [([0, 5, 1, 4], 3), ([0, 3, 4, 0], 2), ([0, 4, 0, 4], 2)],
        "colors": {"seventh": 4, "triad": 1},
        "chord_bars": (1, 1), "keys": [9, 2, 7, 4], "forms": {"head_solo": 3, "pop": 2},
        "drums": [
            ("pompe_brush", 0.5, 4, {SNARE: [(1, 70, 1), (3, 70, 1), (.5, 44, .5, "dt"), (2.5, 44, .5, "dt")], CHH: H8(62, 72), KICK: [(0, 70, .7), (2, 70, .7)]}),
        ],
        "bass": [("pompe", 5, [(0, "r", .9, 92), (1, "5", .9, 86), (2, "r", .9, 90), (3, "3", .9, 86)])],
        "comp": [("la_pompe", 5, [(1, .4, 90), (3, .4, 90)]), ("pompe_push", 2, [(.75, .3, 84), (1, .4, 90), (2.75, .3, 84), (3, .4, 90)])],
        "instruments": {"bass": [(32, 3)], "chords": [(26, 4), (25, 2), (27, 1)], "lead": [(26, 3), (40, 3), (21, 1)]},
        "motifs": [[0, 1, 2, 3, 2, 1, 0, -1], [4, 3, 2, 1, 0, 1, 2, 4], [0, 2, 4, 6, 4, 3, 1, 0]],
        "rhythms": [[.5, .5, .5, .5, .5, .5, .5, .5], [.5, .5, .5, .5, 1, .5, .5]],
        "rest": 0.10, "temp": (1.0, 1.3), "lead_octave": 5, "fill": 0.05,
    },
}
