#!/usr/bin/env python3
# Copyright (c) 2026 Lewis James Seals Jr and Coletta Love.
# Licensed under the MIT License – see LICENSE file.
"""Multi-genre MIDI generator CLI."""
from __future__ import annotations
import argparse, importlib, pkgutil
from pathlib import Path
import genres
from genre_base import GenrePatternGenerator


def discover_genres():
    found = {}
    for _, name, _ in pkgutil.iter_modules(genres.__path__):
        if name.startswith("_"):
            continue
        mod = importlib.import_module(f"genres.{name}")
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if (isinstance(obj, type)
                    and issubclass(obj, GenrePatternGenerator)
                    and obj is not GenrePatternGenerator
                    and obj.__module__ == mod.__name__):
                found[name] = obj
    return found


def main():
    ap = argparse.ArgumentParser(description="Modular multi-genre MIDI generator.")
    ap.add_argument("--genre", default="all", help="Genre name, 'all', or 'help'")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("."))
    ap.add_argument("--temperature", type=float, default=None,
                    help="Markov sampling temperature (<1 safer/repetitive, >1 surprising)")
    ap.add_argument("--report", action="store_true",
                    help="Print entropy/repetition diagnostics when a genre provides them")
    args = ap.parse_args()

    registry = discover_genres()

    if args.genre == "help":
        print("Available genres:")
        for n in sorted(registry):
            print(f"  {n}")
        return

    names = sorted(registry) if args.genre == "all" else [args.genre]
    for name in names:
        if name not in registry:
            print(f"Unknown genre: {name}")
            continue
        cls = registry[name]
        for i in range(args.count):
            seed = args.seed + i if args.seed is not None else None
            gen = cls(seed=seed)
            if args.temperature is not None:
                gen.TEMPERATURE = args.temperature
            fname = args.out / f"{name}_seed{seed if seed is not None else 'rand'}_{i}.mid"
            gen.generate(str(fname))
            if args.report and gen.report():
                print("Report:", gen.report())


if __name__ == "__main__":
    main()
