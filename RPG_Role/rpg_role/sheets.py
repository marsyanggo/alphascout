"""Sprite-sheet / GIF / metadata assembly."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from . import FRAME
from .animations import ANIMATIONS, DIRECTIONS
from .character import Character
from .drawing import Pose, render_frame

GIF_BG = (48, 44, 70)


def render_animation(ch: Character, name: str, direction: str) -> list[Image.Image]:
    spec = ANIMATIONS[name]
    frames = []
    for kwargs in spec["frames"]:
        frames.append(render_frame(ch, Pose(dir=direction, **kwargs)))
    return frames


def build_sheet(ch: Character, name: str, scale: int = 1) -> Image.Image:
    """One animation sheet: rows = directions (or 1), cols = frames."""
    spec = ANIMATIONS[name]
    dirs = DIRECTIONS if spec["dirs"] else ["down"]
    n = len(spec["frames"])
    sheet = Image.new("RGBA", (n * FRAME, len(dirs) * FRAME), (0, 0, 0, 0))
    for row, d in enumerate(dirs):
        for col, frame in enumerate(render_animation(ch, name, d)):
            sheet.paste(frame, (col * FRAME, row * FRAME))
    if scale > 1:
        sheet = sheet.resize((sheet.width * scale, sheet.height * scale),
                             Image.NEAREST)
    return sheet


def build_master_sheet(ch: Character, scale: int = 1) -> tuple[Image.Image, dict]:
    """All animations stacked vertically, plus engine-ready metadata."""
    sheets = {name: build_sheet(ch, name) for name in ANIMATIONS}
    width = max(s.width for s in sheets.values())
    height = sum(s.height for s in sheets.values())
    master = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    meta: dict = {
        "character": {"job": ch.job, "seed": ch.seed, "weapon": ch.weapon},
        "frame_size": FRAME,
        "scale": scale,
        "animations": {},
    }
    y = 0
    for name, sheet in sheets.items():
        master.paste(sheet, (0, y))
        spec = ANIMATIONS[name]
        dirs = DIRECTIONS if spec["dirs"] else ["down"]
        meta["animations"][name] = {
            "row_start": y // FRAME,
            "rows": dirs,
            "frames": len(spec["frames"]),
            "fps": spec["fps"],
        }
        y += sheet.height
    if scale > 1:
        master = master.resize((master.width * scale, master.height * scale),
                               Image.NEAREST)
    return master, meta


def build_gif(ch: Character, name: str, direction: str, scale: int = 4) -> list[Image.Image]:
    frames = []
    for f in render_animation(ch, name, direction):
        bg = Image.new("RGBA", (FRAME, FRAME), (*GIF_BG, 255))
        bg = Image.alpha_composite(bg, f)
        bg = bg.resize((FRAME * scale, FRAME * scale), Image.NEAREST)
        frames.append(bg.convert("P", palette=Image.ADAPTIVE))
    return frames


def export_character(ch: Character, out_dir: str | Path, scale: int = 1,
                     gifs: bool = False) -> Path:
    """Write sheets + metadata (+ optional GIF previews) for one character."""
    root = Path(out_dir) / f"{ch.job}_{ch.seed}"
    root.mkdir(parents=True, exist_ok=True)

    for name in ANIMATIONS:
        build_sheet(ch, name, scale).save(root / f"{name}.png")
    master, meta = build_master_sheet(ch, scale)
    master.save(root / "spritesheet.png")
    (root / "spritesheet.json").write_text(json.dumps(meta, indent=2))

    if gifs:
        for name in ANIMATIONS:
            spec = ANIMATIONS[name]
            direction = "right" if name in ("attack", "special", "hurt") else "down"
            if not spec["dirs"]:
                direction = "down"
            frames = build_gif(ch, name, direction)
            frames[0].save(root / f"preview_{name}.gif", save_all=True,
                           append_images=frames[1:],
                           duration=int(1000 / spec["fps"]), loop=0)
    return root
