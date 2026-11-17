# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""Style classifier + deterministic composition planner.

    brief (free text / mood / energy / bpm / key)  ->  classify()  ->  genre probabilities
    seed + brief                                   ->  plan_composition()  ->  Plan

A Plan is a complete, inspectable set of musical decisions (genre, tempo, key,
mode, progression, chord colour, drum / bass / comping patterns, GM instruments,
top-line motifs and rhythms, form, swing, temperature). Every choice is a
weighted draw from style_kb.py using a seeded RNG, so the same (seed, brief)
always gives the same Plan. Candidate plans are scored for coherence and the
best of a few deterministic attempts is kept.

No machine learning and no network. This is the heuristic stage; the weights in
style_kb.py are the part you would later calibrate (from trained MIDI, listening
tests, or Suno results).
"""
from __future__ import annotations

import math
import random
import re
from dataclasses import asdict, dataclass, field
from typing import Optional

import style_kb as kb

KEY_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
_KEY_LOOKUP = {k.lower(): i for i, k in enumerate(KEY_NAMES)}
_KEY_LOOKUP.update({"db": 1, "d#": 3, "gb": 6, "g#": 8, "a#": 10})


@dataclass
class Brief:
    """What the user asked for. Every field is optional."""
    text: str = ""
    style: Optional[str] = None      # force a genre from style_kb.GENRES
    mood: Optional[str] = None
    energy: Optional[str] = None     # low | medium | high
    bpm: Optional[int] = None
    key: Optional[str] = None        # e.g. "F#" or "Bb"
    mode: Optional[str] = None


@dataclass
class Plan:
    seed: int
    attempt: int
    genre: str
    label: str
    genre_probs: dict
    mood: Optional[str]
    energy: Optional[str]
    bpm: int
    key_pc: int
    key_name: str
    mode: str
    swing: float
    layback: int
    form_name: str
    structure: list
    degrees: list
    chord_color: str
    chord_bars: tuple
    drum_name: str
    drum_pattern: dict
    drum_intensity: float
    bass_name: str
    bass_pattern: list
    comp_name: str
    comp_pattern: list
    programs: dict
    motifs: list
    rhythms: list
    temperature: float
    rest_prob: float
    lead_octave: int
    fill_prob: float
    coherence: float = 0.0
    breakdown: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def weighted_choice(rng: random.Random, items):
    """items: [(value, weight)]; deterministic given rng state."""
    total = sum(max(w, 0.0) for _v, w in items)
    if total <= 0:
        return items[rng.randrange(len(items))][0]
    r = rng.random() * total
    cum = 0.0
    for v, w in items:
        cum += max(w, 0.0)
        if r <= cum:
            return v
    return items[-1][0]


def _tokens(text: str):
    return re.findall(r"[a-z0-9&#'+-]+", text.lower())


def parse_brief(brief: Brief) -> Brief:
    """Fill mood / energy / bpm / key / mode from free text where not given."""
    text = brief.text or ""
    toks = _tokens(text)
    b = Brief(**brief.__dict__)
    if b.mood is None:
        for t in toks:
            if t in kb.MOODS:
                b.mood = t
                break
            if t in kb.MOOD_WORDS:
                b.mood = kb.MOOD_WORDS[t]
                break
    if b.energy is None:
        for lvl in ("low", "medium", "high"):
            if f"{lvl} energy" in text.lower():
                b.energy = lvl
    if b.bpm is None:
        m = re.search(r"(\d{2,3})\s*bpm", text.lower())
        if m:
            b.bpm = int(m.group(1))
    if b.key is None or b.mode is None:
        m = re.search(r"\b([a-g][#b]?)\s+(major|minor)\b", text.lower())
        if m:
            b.key = b.key or m.group(1)
            b.mode = b.mode or m.group(2)
    return b


# --------------------------------------------------------------------------
# classifier
# --------------------------------------------------------------------------
def classify(brief: Brief):
    """Rank genres for a brief. Returns [(genre, probability)] sorted high to low."""
    b = parse_brief(brief)
    if b.style:
        if b.style not in kb.GENRES:
            raise ValueError(f"unknown style {b.style!r}; choose from {sorted(kb.GENRES)}")
        return [(b.style, 1.0)] + [(g, 0.0) for g in sorted(kb.GENRES) if g != b.style]
    toks = set(_tokens(b.text))
    mood = kb.MOODS.get(b.mood or "", {})
    scores = {}
    for g, spec in kb.GENRES.items():
        tag_score = sum(w for tag, w in spec["tags"].items() if tag in toks or tag == g)
        s = (1.0 + tag_score) ** 2
        s *= mood.get("genres", {}).get(g, 1.0)
        if b.bpm:
            lo, hi = spec["bpm"]
            mid, half = (lo + hi) / 2.0, max((hi - lo) / 2.0, 8.0)
            s *= math.exp(-(((b.bpm - mid) / (half * 1.5)) ** 2))
        scores[g] = s
    total = sum(scores.values())
    return sorted(((g, s / total) for g, s in scores.items()), key=lambda x: -x[1])


# --------------------------------------------------------------------------
# planner
# --------------------------------------------------------------------------
def _draft(seed: int, attempt: int, rng: random.Random, b: Brief, ranking) -> Plan:
    genre = weighted_choice(rng, ranking)
    G = kb.GENRES[genre]
    mood = kb.MOODS.get(b.mood or "", {})
    energy = kb.ENERGY.get(b.energy or "", {})

    # tempo
    lo, hi = G["bpm"]
    pos = energy.get("tempo_pos", mood.get("tempo_pos"))
    if pos is None:
        pos = rng.random()
    pos = min(1.0, max(0.0, pos + rng.uniform(-0.12, 0.12)))
    bpm = int(b.bpm) if b.bpm else int(round(lo + pos * (hi - lo)))

    # key + mode
    if b.key and b.key.lower() in _KEY_LOOKUP:
        key_pc = _KEY_LOOKUP[b.key.lower()]
    elif G["keys"]:
        key_pc = rng.choice(G["keys"])
    else:
        key_pc = rng.randrange(12)
    if b.mode and b.mode in G["modes"]:
        mode = b.mode
    elif b.mode in ("major", "minor") and b.mode:
        mode = b.mode
    else:
        mode = weighted_choice(rng, [(m, w * mood.get("modes", {}).get(m, 1.0))
                                     for m, w in G["modes"].items()])

    degrees = list(weighted_choice(rng, [(tuple(p), w) for p, w in G["progressions"]]))
    color = weighted_choice(rng, list(G["colors"].items()))

    # drums: prefer patterns whose intensity matches the requested energy/mood
    target = energy.get("intensity", mood.get("intensity"))
    drum_items = []
    for name, inten, _w, pat in G["drums"]:
        fit = 1.0 if target is None else math.exp(-(((inten - target) / 0.3) ** 2))
        drum_items.append(((name, inten, pat), fit + 0.05))
    drum_name, drum_int, drum_pat = weighted_choice(rng, drum_items)

    bass_name, bass_pat = weighted_choice(rng, [((n, p), w) for n, w, p in G["bass"]])
    comp_name, comp_pat = weighted_choice(rng, [((n, p), w) for n, w, p in G["comp"]])

    inst = G["instruments"]
    chords_prog = weighted_choice(rng, inst["chords"])
    lead_items = [(p, w) for p, w in inst["lead"] if p != chords_prog] or inst["lead"]
    programs = {"bass": weighted_choice(rng, inst["bass"]), "chords": chords_prog,
                "melody": weighted_choice(rng, lead_items)}

    form_name = weighted_choice(rng, list(G["forms"].items()))
    t_lo, t_hi = G["temp"]
    temperature = rng.uniform(t_lo, t_hi) + mood.get("temp", 0.0)

    return Plan(
        seed=seed, attempt=attempt, genre=genre, label=G["label"],
        genre_probs={g: round(p, 4) for g, p in ranking[:3]},
        mood=b.mood, energy=b.energy, bpm=bpm, key_pc=key_pc, key_name=KEY_NAMES[key_pc],
        mode=mode, swing=round(rng.uniform(*G["swing"]), 4), layback=G["layback"],
        form_name=form_name, structure=[list(s) for s in kb.FORMS[form_name]],
        degrees=degrees, chord_color=color, chord_bars=tuple(G["chord_bars"]),
        drum_name=drum_name, drum_pattern=drum_pat, drum_intensity=drum_int,
        bass_name=bass_name, bass_pattern=bass_pat, comp_name=comp_name, comp_pattern=comp_pat,
        programs=programs,
        motifs=[list(m) for m in G["motifs"]], rhythms=[list(r) for r in G["rhythms"]],
        temperature=round(temperature, 3),
        rest_prob=round(min(0.6, max(0.0, G["rest"] + mood.get("rest", 0.0))), 3),
        lead_octave=G["lead_octave"], fill_prob=G["fill"],
    )


def score(plan: Plan):
    """Heuristic coherence in [0, 1] plus a per-check breakdown."""
    G = kb.GENRES[plan.genre]
    lo, hi = G["bpm"]
    tempo = 1.0 if lo <= plan.bpm <= hi else max(0.3, 1.0 - min(abs(plan.bpm - lo), abs(plan.bpm - hi)) / 40.0)
    mw = G["modes"].get(plan.mode, 0.0)
    mode = 0.65 if mw == 0 else 0.65 + 0.35 * mw / max(G["modes"].values())
    degs = plan.degrees
    prog = (1.0 if degs[0] == 0 else 0.6) * (1.0 if degs[-1] in (0, 4) else 0.85)
    swing = 1.0 if G["swing"][0] <= plan.swing <= G["swing"][1] else 0.7
    timbre = 0.6 if plan.programs["melody"] == plan.programs["chords"] else 1.0
    chord_len = len(plan.degrees) * (plan.chord_bars[0])
    form_bars = sum(b for _s, b in plan.structure)
    form = 1.0 if form_bars % max(1, len(plan.degrees)) == 0 or plan.genre == "blues" else 0.9
    rest_fit = 1.0 - abs(plan.rest_prob - G["rest"]) * 1.5
    breakdown = {"tempo": tempo, "mode": mode, "progression": prog, "swing": swing,
                 "timbre": timbre, "form": form, "melody_density": max(0.5, rest_fit)}
    total = sum(breakdown.values()) / len(breakdown)
    return round(total, 4), {k: round(v, 3) for k, v in breakdown.items()}


def plan_composition(seed: int, brief: Optional[Brief] = None,
                     attempts: int = 12, threshold: float = 0.92) -> Plan:
    """Deterministic: same (seed, brief) -> same Plan."""
    b = parse_brief(brief or Brief())
    ranking = classify(b)
    best = None
    for k in range(attempts):
        rng = random.Random(f"musicscript-plan:{seed}:{k}")
        plan = _draft(seed, k, rng, b, ranking)
        plan.coherence, plan.breakdown = score(plan)
        if best is None or plan.coherence > best.coherence:
            best = plan
        if plan.coherence >= threshold:
            break
    return best


def explain(plan: Plan) -> str:
    lines = [
        f"Genre      : {plan.label} (top matches {plan.genre_probs})",
        f"Mood/energy: {plan.mood or '-'} / {plan.energy or '-'}",
        f"Tempo/key  : {plan.bpm} BPM, {plan.key_name} {plan.mode.replace('_', ' ')}, swing {plan.swing}",
        f"Form       : {plan.form_name} ({sum(b for _s, b in plan.structure)} bars)",
        f"Progression: degrees {plan.degrees}, {plan.chord_color} chords, {plan.chord_bars[0]}/{plan.chord_bars[1]} bars per chord",
        f"Drums      : {plan.drum_name} (intensity {plan.drum_intensity})",
        f"Bass/comp  : {plan.bass_name} / {plan.comp_name}",
        "Instruments: " + ", ".join(f"{k}={kb.GM_NAMES.get(v, v)}" for k, v in plan.programs.items()),
        f"Top line   : {len(plan.motifs)} motifs, temperature {plan.temperature}, rests {plan.rest_prob}",
        f"Coherence  : {plan.coherence}  {plan.breakdown}  (attempt {plan.attempt + 1})",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Suno hand-off (text only; there is no API call here)
# --------------------------------------------------------------------------
SECTION_TAGS = {"intro": "[Intro]", "verse": "[Verse]", "chorus": "[Chorus]",
                "bridge": "[Bridge]", "break": "[Instrumental Break]", "outro": "[Outro]"}
_DRUM_WORDS = {"rnb": "laid-back drums", "hiphop": "boom-bap drums", "trap": "808s and rolling hi-hats",
               "funk": "tight funk drums", "rock": "driving rock drums", "jazz": "brushed swing drums",
               "blues": "shuffle drums", "reggae": "one-drop drums", "house": "four-on-the-floor kick",
               "synthwave": "gated snare drums", "gypsy_jazz": "light brushes"}


def to_suno(plan: Plan) -> dict:
    """Turn a Plan into a Suno-ready text brief.

    `style` is a comma-separated style prompt. `style_short` is trimmed to 200
    characters as a conservative default (check Suno's current limit; I have not
    verified it). `lyrics_skeleton` is the section structure with Suno-style tags.
    `weights` is the machine-readable part you can later calibrate against results.
    """
    names = [kb.GM_NAMES.get(plan.programs[k], str(plan.programs[k])) for k in ("melody", "chords", "bass")]
    parts = [plan.label, plan.mood or "", f"{plan.bpm} BPM",
             f"{plan.key_name} {plan.mode.replace('_', ' ')}",
             f"{names[0]} lead", names[1], f"{names[2]}", _DRUM_WORDS.get(plan.genre, "")]
    parts = [p for p in parts if p]
    style = ", ".join(parts)
    short = ""
    for p in parts:
        cand = (short + ", " + p) if short else p
        if len(cand) > 200:
            break
        short = cand
    skeleton = "\n\n".join(f"{SECTION_TAGS.get(s, '[' + s.title() + ']')}\n(lyrics)" for s, _b in plan.structure)
    return {
        "style": style, "style_short": short, "lyrics_skeleton": skeleton,
        "weights": {"genre_mix": plan.genre_probs, "coherence": plan.coherence,
                    "melody_temperature": plan.temperature, "drum_intensity": plan.drum_intensity,
                    "seed": plan.seed},
    }
