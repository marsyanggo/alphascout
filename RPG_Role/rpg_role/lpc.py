"""LPC backend: composes artist-drawn 64x64 LPC layers into the same
animation set as the procedural backend, deterministically from (job, seed).

Only the standard 21-row universal layout is used (every vendored layer
supports it): spellcast row 0, thrust row 4, walk row 8, slash row 12,
shoot row 16, hurt row 20. Row order within a block is up, left, down, right.

Weapon swings live in separate 128/192px "oversize" sheets (one frame per
cell, same row order), composited around each base frame; attack/special
sheets therefore use a larger cell size, recorded per-animation in the
metadata. Special and cast get a procedural effect overlay (burst / sparkle)
so they read as 絕招/魔法 rather than a plain swing.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image

from .lpc_manifest import BODY, HAIR, HAIR_COLORS, HAIR_STYLES, JOBS, SKINS
from .palettes import FX_MAGIC, FX_SPECIAL

FRAME = 64
SHEET_ROWS = 21
ASSETS = Path(__file__).resolve().parents[1] / "assets" / "lpc"

# (row_start, frame_count) in the universal sheet; rows are up/left/down/right.
UNIVERSAL = {
    "spellcast": (0, 7),
    "thrust": (4, 8),
    "walk": (8, 9),      # frame 0 is the standing pose
    "slash": (12, 6),
    "hurt": (20, 6),     # single row: collapse/die
}
ROW_DIRS = ["up", "left", "down", "right"]
OUT_DIRS = ["down", "left", "right", "up"]
GIF_BG = (48, 44, 70)


class LpcCharacter:
    """Resolved layers + loaded sheets for one (job, seed)."""

    def __init__(self, job: str, seed: int):
        if job not in JOBS:
            raise ValueError(f"unknown job {job!r}; choose from {sorted(JOBS)}")
        self.job, self.seed = job, seed
        spec = JOBS[job]
        rng = random.Random(f"lpc:{job}:{seed}")
        values = {"skin": rng.choice(SKINS)}
        for key, choices in spec.get("shared", {}).items():
            values[key] = rng.choice(choices)

        self.layers = [(p["z"], p["path"].format(**values)) for p in BODY]
        if spec["hair"]:
            style = rng.choice([s for s in spec["hair"] if s in HAIR_STYLES])
            self.layers.append((HAIR["z"], HAIR["path"].format(
                hair_style=style, hair=rng.choice(HAIR_COLORS))))
        for part in spec["parts"]:
            self.layers.append((part["z"], part["path"].format(**values)))
        self.layers.sort()

        self.attack_anim = spec.get("attack_anim", "slash")
        self.oversize = [
            (o["z"], o["anim"], o["size"],
             _load(o["path"].format(**values)))
            for o in spec.get("oversize", [])
        ]
        self.sheet = self._compose()

    def _compose(self) -> Image.Image:
        sheet = Image.new("RGBA", (13 * FRAME, SHEET_ROWS * FRAME),
                          (0, 0, 0, 0))
        for _, rel in self.layers:
            layer = _load(rel)
            layer = layer.crop((0, 0, sheet.width,
                                min(layer.height, sheet.height)))
            sheet.alpha_composite(layer)
        return sheet

    def cell_size(self, source: str) -> int:
        sizes = [s for _, anim, s, _ in self.oversize if anim == source]
        return max([FRAME, *sizes])

    def frame(self, source: str, direction: str, index: int,
              fx: str | None = None) -> Image.Image:
        """One composited cell: bg oversize + base 64px frame + fg + effects."""
        row_start, n = UNIVERSAL[source]
        index = min(index, n - 1)
        row = 0 if source == "hurt" else ROW_DIRS.index(direction)
        cell = self.cell_size(source)
        off = (cell - FRAME) // 2
        out = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))

        def paste_oversize(z_filter) -> None:
            for z, anim, size, img in self.oversize:
                if anim != source or not z_filter(z):
                    continue
                crop = img.crop((index * size, row * size,
                                 (index + 1) * size, (row + 1) * size))
                d = (size - cell) // 2
                out.alpha_composite(crop.crop((d, d, d + cell, d + cell)))

        paste_oversize(lambda z: z < 10)
        base_row = row_start if source == "hurt" else row_start + row
        base = self.sheet.crop((index * FRAME, base_row * FRAME,
                                (index + 1) * FRAME, (base_row + 1) * FRAME))
        out.alpha_composite(base, (off, off))
        paste_oversize(lambda z: z >= 10)
        if fx:
            out.alpha_composite(_fx_layer(fx, index, n, cell, direction))
        return out


def _load(rel: str) -> Image.Image:
    path = ASSETS / f"{rel}.png"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} — run tools/vendor_lpc.py to fetch LPC assets")
    return Image.open(path).convert("RGBA")


def _fx_layer(kind: str, index: int, total: int, cell: int,
              direction: str) -> Image.Image:
    """Procedural overlay (scaled-up cousin of the 32px backend effects)."""
    img = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
    px = img.load()
    k = cell / 32.0

    def put(x: float, y: float, color) -> None:
        xi, yi = round(x), round(y)
        for dx in (0, 1):
            for dy in (0, 1):
                if 0 <= xi + dx < cell and 0 <= yi + dy < cell:
                    px[xi + dx, yi + dy] = (*color, 255)

    fxv = {"down": (0, 1), "up": (0, -1),
           "right": (1, 0), "left": (-1, 0)}[direction]
    phase = index * 6 // max(total, 1)  # normalize to 6 effect phases
    cx, cy = cell / 2 + fxv[0] * 6 * k, cell / 2 + fxv[1] * 6 * k

    if kind == "special":
        if phase < 2:    # charge: glow ring gathering
            r = (8 - phase) * k
            for i in range(0, 360, 24):
                a = math.radians(i + index * 17)
                put(cell / 2 + math.cos(a) * r, cell / 2 + math.sin(a) * r,
                    FX_SPECIAL[3 - phase])
        elif phase < 5:  # burst: wide double crescent in front
            for ri, col in ((9 * k, FX_SPECIAL[phase - 2]),
                            (11 * k, FX_SPECIAL[0])):
                for deg in range(-80, 81, 4):
                    a = math.radians(deg)
                    ox = math.cos(a) * ri * fxv[0] + math.sin(a) * ri * abs(fxv[1])
                    oy = math.cos(a) * ri * fxv[1] + math.sin(a) * ri * abs(fxv[0])
                    put(cx + ox, cy + oy, col)
        if phase >= 4:   # sparks flying outward
            for i in range(10):
                a = math.radians(i * 36 + index * 11)
                d = (8 + (phase - 4) * 4) * k
                put(cx + math.cos(a) * d, cy + math.sin(a) * d,
                    FX_SPECIAL[(i + index) % 2])
    elif kind == "magic":
        col = FX_MAGIC[index % len(FX_MAGIC)]
        w = (8 + phase) * k
        for i in range(0, 360, 9):  # magic circle under the feet
            a = math.radians(i)
            put(cell / 2 + math.cos(a) * w / 2,
                cell - 6 * k + math.sin(a) * 2 * k, col)
        for i in range(8):          # rising sparkles
            sx = (8 + (i * 37 + index * 11) % 17) * k
            sy = (24 - ((i * 23 + index * 7) % 20)) * k
            put(sx, sy, FX_MAGIC[(i + index) % len(FX_MAGIC)])
    return img


def exports(ch: LpcCharacter) -> dict[str, dict]:
    """Animation table for one character (attack anim varies per job)."""
    atk = ch.attack_anim
    atk_frames = UNIVERSAL[atk][1]
    return {
        "idle": {"source": "walk", "frames": [0], "fps": 2, "fx": None},
        "walk": {"source": "walk", "frames": list(range(1, 9)), "fps": 10,
                 "fx": None},
        "attack": {"source": atk, "frames": list(range(atk_frames)),
                   "fps": 12, "fx": None},
        "special": {"source": atk, "frames": list(range(atk_frames)),
                    "fps": 12, "fx": "special"},
        "cast": {"source": "spellcast", "frames": list(range(7)), "fps": 10,
                 "fx": "magic"},
        "hurt": {"source": "hurt", "frames": [0, 1, 2], "fps": 8, "fx": None},
        "dead": {"source": "hurt", "frames": [3, 4, 5], "fps": 6, "fx": None},
    }


def build_sheet(ch: LpcCharacter, name: str) -> Image.Image:
    spec = exports(ch)[name]
    source = spec["source"]
    dirs = ["down"] if source == "hurt" else OUT_DIRS
    cell = ch.cell_size(source)
    out = Image.new("RGBA", (len(spec["frames"]) * cell, len(dirs) * cell),
                    (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        for c, f in enumerate(spec["frames"]):
            out.paste(ch.frame(source, d, f, spec["fx"]), (c * cell, r * cell))
    return out


def export_character(job: str, seed: int, out_dir: str | Path,
                     gifs: bool = False) -> Path:
    root = Path(out_dir) / f"{job}_{seed}_lpc"
    root.mkdir(parents=True, exist_ok=True)
    ch = LpcCharacter(job, seed)
    table = exports(ch)

    meta: dict = {
        "character": {"job": job, "seed": seed, "style": "lpc"},
        "frame_size": FRAME,
        "layers": [rel for _, rel in ch.layers],
        "license": "art CC-BY-SA 3.0 / GPL 3.0 — see assets/lpc/ATTRIBUTION.md",
        "animations": {},
    }
    for name, spec in table.items():
        sheet = build_sheet(ch, name)
        sheet.save(root / f"{name}.png")
        cell = ch.cell_size(spec["source"])
        dirs = ["down"] if spec["source"] == "hurt" else OUT_DIRS
        meta["animations"][name] = {
            "file": f"{name}.png", "frame_size": cell, "rows": dirs,
            "frames": len(spec["frames"]), "fps": spec["fps"],
        }
    (root / "spritesheet.json").write_text(json.dumps(meta, indent=2))

    if gifs:
        for name, spec in table.items():
            direction = "down" if spec["source"] == "hurt" else \
                ("right" if name in ("attack", "special") else "down")
            cell = ch.cell_size(spec["source"])
            imgs = []
            for f in spec["frames"]:
                bg = Image.new("RGBA", (cell, cell), (*GIF_BG, 255))
                bg.alpha_composite(ch.frame(spec["source"], direction, f,
                                            spec["fx"]))
                bg = bg.resize((cell * 2, cell * 2), Image.NEAREST)
                imgs.append(bg.convert("P", palette=Image.ADAPTIVE))
            imgs[0].save(root / f"preview_{name}.gif", save_all=True,
                         append_images=imgs[1:],
                         duration=int(1000 / spec["fps"]), loop=0)
    return root
