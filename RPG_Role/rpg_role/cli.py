"""Command-line interface.

    python -m rpg_role generate --job hero --seed 7 --out out/ --gifs
    python -m rpg_role party --seed 1 --out out/
    python -m rpg_role jobs

Two render styles:
    lpc  (default) — artist-drawn 64x64 LPC layers, high fidelity
    mini           — fully procedural 32x32 pixel sprites, zero assets
"""

from __future__ import annotations

import argparse

from . import lpc
from .character import make_character
from .palettes import JOBS
from .sheets import export_character


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="out")
    p.add_argument("--style", choices=["lpc", "mini"], default="lpc")
    p.add_argument("--scale", type=int, default=1,
                   help="integer upscale (mini style only)")
    p.add_argument("--gifs", action="store_true", help="write GIF previews")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="rpg_role",
        description="Retro RPG character sprite generator (LPC + procedural)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="generate one character")
    gen.add_argument("--job", required=True, choices=sorted(JOBS))
    _add_common(gen)

    party = sub.add_parser("party", help="generate every job at once")
    _add_common(party)

    sub.add_parser("jobs", help="list available jobs")

    args = parser.parse_args(argv)

    if args.cmd == "jobs":
        for job, spec in sorted(JOBS.items()):
            print(f"{job:8s} weapon={spec['weapon']}")
        return

    jobs = sorted(JOBS) if args.cmd == "party" else [args.job]
    for job in jobs:
        if args.style == "lpc":
            root = lpc.export_character(job, args.seed, args.out,
                                        gifs=args.gifs)
        else:
            ch = make_character(job, args.seed)
            root = export_character(ch, args.out, scale=args.scale,
                                    gifs=args.gifs)
        print(f"{job}: {root}")


if __name__ == "__main__":
    main()
