"""Command-line interface.

    python -m rpg_role generate --job hero --seed 7 --out out/ --gifs
    python -m rpg_role party --seed 1 --out out/
    python -m rpg_role monster --type orc --seed 2 --out out/
    python -m rpg_role horde --seed 1 --out out/        # every monster
    python -m rpg_role items --out out/
    python -m rpg_role map --kind overworld --width 64 --height 48 --seed 7
    python -m rpg_role jobs

Two character render styles:
    lpc  (default) — artist-drawn 64x64 LPC layers, high fidelity
    mini           — fully procedural 32x32 pixel sprites, zero assets
"""

from __future__ import annotations

import argparse

from . import lpc, worldmap
from .character import make_character
from .items import export_items
from .lpc_manifest import MONSTERS
from .monsters import SLIME_COLORS, export_slime
from .palettes import JOBS
from .sheets import export_character


def _add_common(p: argparse.ArgumentParser, mini: bool = True) -> None:
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="out")
    styles = ["hd", "lpc"] + (["mini"] if mini else [])
    p.add_argument("--style", choices=styles, default="hd")
    if mini:
        p.add_argument("--scale", type=int, default=1,
                       help="integer upscale (mini style only)")
    p.add_argument("--gifs", action="store_true", help="write GIF previews")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="rpg_role",
        description="Retro RPG generator: characters, monsters, items, maps")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="generate one character")
    gen.add_argument("--job", required=True, choices=sorted(JOBS))
    _add_common(gen)

    party = sub.add_parser("party", help="generate every job at once")
    _add_common(party)

    mon = sub.add_parser("monster", help="generate one monster")
    mon.add_argument("--type", required=True, dest="mtype",
                     choices=sorted(MONSTERS) + ["slime"])
    mon.add_argument("--color", choices=sorted(SLIME_COLORS),
                     default="blue", help="slime color")
    _add_common(mon, mini=False)

    horde = sub.add_parser("horde", help="generate every monster at once")
    _add_common(horde, mini=False)

    items = sub.add_parser("items", help="generate the item icon set")
    items.add_argument("--out", default="out")
    items.add_argument("--scale", type=int, default=1)

    mp = sub.add_parser("map", help="generate a tile map")
    mp.add_argument("--kind", choices=["overworld", "dungeon"],
                    default="overworld")
    mp.add_argument("--width", type=int, default=48)
    mp.add_argument("--height", type=int, default=36)
    mp.add_argument("--seed", type=int, default=0)
    mp.add_argument("--out", default="out")

    art = sub.add_parser("aiart", help="AI-generated battle art / portraits")
    art.add_argument("--subject", required=True,
                     help='e.g. "golden dragon boss" or "young hero, red cape"')
    art.add_argument("--kind", choices=["monster", "portrait", "item", "scene"],
                     default="monster")
    art.add_argument("--provider",
                     choices=["auto", "openai", "stability", "pollinations"],
                     default="auto")
    art.add_argument("--seed", type=int, default=0)
    art.add_argument("--out", default="out")
    art.add_argument("--no-pixel", action="store_true",
                     help="keep full-res AI art (skip retro pixelation)")

    sub.add_parser("jobs", help="list available jobs and monsters")

    args = parser.parse_args(argv)

    if args.cmd == "jobs":
        for job, spec in sorted(JOBS.items()):
            print(f"job      {job:10s} weapon={spec['weapon']}")
        for m in sorted(MONSTERS):
            print(f"monster  {m}")
        print(f"monster  slime ({', '.join(sorted(SLIME_COLORS))})")
        return

    if args.cmd == "items":
        print(export_items(args.out, scale=args.scale))
        return

    if args.cmd == "map":
        print(export_map_cmd(args))
        return

    if args.cmd == "aiart":
        from .ai import export_ai_art
        print(export_ai_art(args.subject, args.kind, args.out,
                            seed=args.seed, provider=args.provider,
                            pixel_grid=None if args.no_pixel else 96))
        return

    hd = getattr(args, "style", "hd") == "hd"

    if args.cmd == "monster":
        if args.mtype == "slime":
            print(export_slime(args.color, args.out, gifs=args.gifs, hd=hd))
        else:
            print(lpc.export_character(args.mtype, args.seed, args.out,
                                       gifs=args.gifs, hd=hd))
        return

    if args.cmd == "horde":
        for m in sorted(MONSTERS):
            print(f"{m}: {lpc.export_character(m, args.seed, args.out, gifs=args.gifs, hd=hd)}")
        for color in sorted(SLIME_COLORS):
            print(f"slime_{color}: "
                  f"{export_slime(color, args.out, gifs=args.gifs, hd=hd)}")
        return

    jobs = sorted(JOBS) if args.cmd == "party" else [args.job]
    for job in jobs:
        if args.style == "mini":
            ch = make_character(job, args.seed)
            root = export_character(ch, args.out, scale=args.scale,
                                    gifs=args.gifs)
        else:
            root = lpc.export_character(job, args.seed, args.out,
                                        gifs=args.gifs, hd=hd)
        print(f"{job}: {root}")


def export_map_cmd(args) -> str:
    return str(worldmap.export_map(args.kind, args.width, args.height,
                                   args.seed, args.out))


if __name__ == "__main__":
    main()
