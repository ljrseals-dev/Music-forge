# MusicScript Forge – Manual

## Concepts
- **Section structure**: intro/verse/chorus/bridge/break/outro, each with an energy level used to thin or thicken parts.
- **Double time**: in `main.py`, chorus and bridge sections use busier patterns and change chord every bar (other sections every two bars).
- **Determinism**: all randomness comes from a seeded `random.Random`; same seed, same MIDI.
- **Channels**: bass 0, chords 1, melody 2, drums 9 (General MIDI percussion).

## main.py options
`--genre NAME|all|help`, `--seed N` (item i uses seed N+i), `--count N`, `--out DIR`, `--temperature T`, `--report`.

## meta_script.py options
`--count N`, `--genre NAME`, `--seed N` (master seed), `--out DIR`, `--run` (alias `--render`).

## Writing a genre
Subclass `GenrePatternGenerator`; set `GENRE`, `DEFAULT_BPM`, `DEFAULT_MODE`, `SWING`, `HUMANIZE_TICKS`, `VELOCITY_JITTER`; optionally override `_define_structure`, `_define_chords`, `_define_progression`; implement the four `gen_*` hooks using `self.event_note(...)`, `self.swing_tick(...)`, `self.human_tick(...)`, `self.human_vel(...)`.

## License
MIT, unmodified. See LICENSE.
