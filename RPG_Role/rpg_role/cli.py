"""Command-line interface.

    python -m rpg_role generate --job hero --seed 7 --out out/ --gifs
    python -m rpg_role party --seed 1 --out out/ --scale 2
    python -m rpg_role jobs
"""

from __future__ import annotations

import argparse

from .character import make_character
from .palettes import JOBS
from .sheets import export_character


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="rpg_role",
        description="Procedural 32x32 retro RPG character sprite generator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="generate one character")
    gen.add_argument("--job", required=True, choices=sorted(JOBS))
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--out", default="out")
    gen.add_argument("--scale", type=int, default=1)
    gen.add_argument("--gifs", action="store_true", help="write GIF previews")

    party = sub.add_parser("party", help="generate every job at once")
    party.add_argument("--seed", type=int, default=0)
    party.add_argument("--out", default="out")
    party.add_argument("--scale", type=int, default=1)
    party.add_argument("--gifs", action="store_true")

    sub.add_parser("jobs", help="list available jobs")

    args = parser.parse_args(argv)

    if args.cmd == "jobs":
        for job, spec in sorted(JOBS.items()):
            print(f"{job:8s} weapon={spec['weapon']}")
        return

    jobs = sorted(JOBS) if args.cmd == "party" else [args.job]
    for job in jobs:
        ch = make_character(job, args.seed)
        root = export_character(ch, args.out, scale=args.scale, gifs=args.gifs)
        print(f"{job}: {root}")


if __name__ == "__main__":
    main()
