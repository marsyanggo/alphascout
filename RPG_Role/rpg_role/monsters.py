"""Procedural monsters in the 32x32 mini style — currently the DQ-style
slime family (palette-swapped, classic squash & stretch animation).

LPC-based humanoid monsters (orc, skeleton, ...) live in lpc.py; this
module covers shapes that aren't humanoid.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from . import FRAME
from .canvas import Canvas
from .palettes import OUTLINE, Ramp, ramp

SLIME_COLORS: dict[str, Ramp] = {
    "blue": ramp((70, 120, 220)),
    "red": ramp((215, 80, 70)),
    "green": ramp((80, 180, 90)),
    "orange": ramp((230, 150, 60)),
    "metal": ramp((150, 156, 170)),
    "shadow": ramp((80, 70, 110)),
}

GIF_BG = (48, 44, 70)

# name: (frames as (squash, lean, flash), fps)
#   squash: -2..2  (negative = stretched tall, positive = flattened)
#   lean:   x offset (lunge)
#   flash:  draw highlight ring (attack impact)
SLIME_ANIMS: dict[str, dict] = {
    "idle": {"fps": 3, "frames": [(0, 0, False), (1, 0, False)]},
    "walk": {"fps": 8, "frames": [(1, 0, False), (-1, 0, False),
                                  (0, 0, False), (1, 0, False)]},
    "attack": {"fps": 10, "frames": [(2, -2, False), (-2, 1, False),
                                     (-1, 5, True), (0, 2, False)]},
    "special": {"fps": 10, "frames": [(2, -2, False), (2, -2, True),
                                      (-2, 2, False), (-2, 6, True),
                                      (-1, 6, True), (0, 2, False)]},
    "hurt": {"fps": 8, "frames": [(2, -3, False), (1, -1, False)]},
    "dead": {"fps": 1, "frames": [(3, 0, False)]},
}


def _draw_slime(color: Ramp, squash: int, lean: int,
                flash: bool) -> Image.Image:
    c = Canvas()
    cx = 16 + lean
    base = 26
    h = 14 - squash * 2          # body height
    w = 16 + squash * 2          # body width
    if squash >= 3:              # defeated puddle
        c.rect(cx - 10, base - 2, cx + 9, base, color[1])
        c.put(cx - 4, base - 2, color[2])
        return c.finish()
    top = base - h
    # Dome: stacked rows, widening toward the base.
    for y in range(top, base + 1):
        t = (y - top) / max(h, 1)
        half = round((w / 2) * min(1.0, 0.35 + t * 0.9))
        c.rect(cx - half, y, cx + half - 1, y, color[1])
    # Drippy tip and highlight.
    c.put(cx + w // 4, top - 1, color[1])
    c.rect(cx - w // 4 - 1, top + 2, cx - w // 4, top + 4, color[2])
    # Face.
    ey = top + h // 2
    c.put(cx - 3, ey, OUTLINE)
    c.put(cx + 2, ey, OUTLINE)
    c.rect(cx - 1, ey + 3, cx, ey + 3, OUTLINE)   # mouth
    img = c.finish()
    if flash:
        px = img.load()
        for x, y in ((cx + 9, ey - 2), (cx + 11, ey + 1), (cx + 9, ey + 4),
                     (cx + 12, ey - 4)):
            if 0 <= x < FRAME and 0 <= y < FRAME:
                px[x, y] = (255, 255, 200, 255)
    return img


def export_slime(color: str, out_dir: str | Path, scale: int = 1,
                 gifs: bool = False) -> Path:
    if color not in SLIME_COLORS:
        raise ValueError(
            f"unknown slime color {color!r}; choose from {sorted(SLIME_COLORS)}")
    palette = SLIME_COLORS[color]
    root = Path(out_dir) / f"slime_{color}"
    root.mkdir(parents=True, exist_ok=True)

    meta = {"character": {"monster": "slime", "color": color},
            "frame_size": FRAME, "scale": scale, "animations": {}}
    for name, spec in SLIME_ANIMS.items():
        frames = [_draw_slime(palette, *f) for f in spec["frames"]]
        sheet = Image.new("RGBA", (len(frames) * FRAME, FRAME), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.paste(f, (i * FRAME, 0))
        if scale > 1:
            sheet = sheet.resize((sheet.width * scale, sheet.height * scale),
                                 Image.NEAREST)
        sheet.save(root / f"{name}.png")
        meta["animations"][name] = {"file": f"{name}.png",
                                    "frames": len(frames), "rows": ["all"],
                                    "fps": spec["fps"]}
        if gifs:
            imgs = []
            for f in frames:
                bg = Image.new("RGBA", (FRAME, FRAME), (*GIF_BG, 255))
                bg.alpha_composite(f)
                bg = bg.resize((FRAME * 4, FRAME * 4), Image.NEAREST)
                imgs.append(bg.convert("P", palette=Image.ADAPTIVE))
            imgs[0].save(root / f"preview_{name}.gif", save_all=True,
                         append_images=imgs[1:],
                         duration=int(1000 / spec["fps"]), loop=0)
    (root / "spritesheet.json").write_text(json.dumps(meta, indent=2))
    return root
