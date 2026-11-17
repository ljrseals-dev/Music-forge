# MusicScript Forge

Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
Licensed under the MIT License – see LICENSE.

Two entry points, both producing Standard MIDI Files (type 1, 480 PPQ, five tracks: conductor, bass, chords, melody, drums):

- `main.py` – modular multi-genre generator (10 genres, auto-discovered from `genres/`)
- `meta_script.py` – meta-generator that writes standalone `.py` composers (6 genres), each with its musical DNA baked in

## Install

    pip install mido

## Modular generator

    python main.py --genre help
    python main.py --genre all --count 1
    python main.py --genre gypsy_jazz --seed 42 --count 3 --out out/

Genres: blues, electronic, funk, gypsy_jazz, hiphop, jazz, reggae, rnb, rock, synthwave.
Output: `<genre>_seed<seed>_<n>.mid`. The same `--seed` always gives the same file.

### Markov melody (rnb)

`rnb` generates its melody with chains from `markov_engine.py`: scale-degree states, an order-2 pitch chain
with back-off and add-alpha smoothing, a separate duration chain, chord-tone constraints on strong beats,
and a temperature schedule that tightens into each 4-bar cadence and loosens on the cadence note.

    python main.py --genre rnb --seed 3 --temperature 1.3 --report

`--temperature` below 1 gives safer, more repetitive lines; above 1 gives more surprise.
`--report` prints conditional entropy, repetition and pitch diversity of the generated melody.

## Meta-generator

    python meta_script.py --count 5 --run --out my_music
    python meta_script.py --genre funk --count 4 --seed 123456

Genres: gypsy_jazz, rock, funk, house, techno, memphis. Each child script embeds its own seed
and runs without this file. `--run` executes each child and a `*_manifest.json` records
the master seed, per-script seeds and SHA-256 hashes. A fixed `--seed` reproduces the same batch.

## Adding a genre (modular generator)

Drop a file in `genres/` containing a `GenrePatternGenerator` subclass that sets `GENRE` and
overrides `gen_bass`, `gen_chords`, `gen_melody` and `gen_drums`. It is picked up automatically.

## Layout

    genre_base.py     base class + arrangement engine
    markov_engine.py  Markov chain + entropy diagnostics
    genres/           one module per genre
    main.py           modular CLI
    meta_script.py    meta-generator
    docs/Manual.md    short manual
    LICENSE           MIT
