"""Procedural 32x32 item icon generator.

Same retro treatment as the mini sprites (flat colors + auto shading +
1px outline via Canvas.finish()). Items come in material/color variants,
so `catalog()` expands to a full item list (e.g. potion_red, sword_gold).
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from . import FRAME
from .canvas import Canvas
from .palettes import GOLD, STEEL, WOOD, Ramp, ramp

# Variant palettes.
METALS: dict[str, Ramp] = {
    "steel": STEEL,
    "gold": GOLD,
    "bronze": ramp((176, 110, 56)),
}
LIQUIDS: dict[str, Ramp] = {
    "red": ramp((210, 60, 60)),
    "blue": ramp((70, 110, 220)),
    "green": ramp((70, 180, 90)),
    "yellow": ramp((230, 200, 70)),
    "purple": ramp((160, 80, 200)),
}
GEMS = LIQUIDS
GLASS = ramp((190, 215, 230))
PAPER = ramp((230, 220, 190))
LEATHER = ramp((140, 92, 50))


def _blade(c: Canvas, x0, y0, x1, y1, metal: Ramp) -> None:
    c.line(x0, y0, x1, y1, metal[2])
    c.line(x0 + 1, y0, x1 + 1, y1, metal[1])


def draw_sword(c: Canvas, metal: Ramp) -> None:
    _blade(c, 9, 23, 21, 11, metal)
    c.put(22, 10, metal[2])                       # tip
    c.line(11, 19, 15, 23, GOLD[1])               # crossguard
    c.line(8, 24, 6, 26, WOOD[1])                 # grip
    c.rect(5, 26, 6, 27, GOLD[1])                 # pommel


def draw_dagger(c: Canvas, metal: Ramp) -> None:
    _blade(c, 12, 20, 19, 13, metal)
    c.line(12, 17, 15, 20, GOLD[1])
    c.line(11, 21, 9, 23, WOOD[1])


def draw_axe(c: Canvas, metal: Ramp) -> None:
    c.line(12, 25, 20, 9, WOOD[1])                # haft
    c.line(13, 25, 21, 9, WOOD[0])
    c.rect(13, 7, 19, 13, metal[1])               # blade
    c.rect(13, 7, 15, 13, metal[2])
    c.put(12, 8, metal[1])
    c.put(12, 12, metal[1])


def draw_staff(c: Canvas, gem: Ramp) -> None:
    c.line(11, 26, 20, 8, WOOD[1])
    c.line(12, 26, 21, 8, WOOD[0])
    c.rect(19, 5, 22, 8, gem[1])                  # orb
    c.put(20, 6, gem[2])


def draw_mace(c: Canvas, metal: Ramp) -> None:
    c.line(13, 25, 18, 13, WOOD[1])
    c.rect(16, 8, 21, 13, metal[1])
    c.put(17, 9, metal[2])
    for x, y in ((15, 7), (22, 7), (15, 14), (22, 14)):   # studs
        c.put(x, y, metal[2])


def draw_bow(c: Canvas, metal: Ramp) -> None:
    for t in range(15):                           # curved limb
        a = t / 14.0
        x = 10 + round(8 * (1 - abs(a - 0.5) * 2) ** 0.8)
        y = 6 + round(a * 20)
        c.put(x, y, WOOD[1])
        c.put(x + 1, y, WOOD[0])
    c.line(10, 6, 10, 26, PAPER[2])               # string
    c.line(11, 16, 22, 16, WOOD[1])               # arrow
    c.put(23, 16, metal[2])


def draw_shield(c: Canvas, metal: Ramp) -> None:
    c.rect(10, 8, 21, 17, metal[1])
    for i, w in enumerate((5, 4, 2, 1)):          # tapered point
        c.rect(16 - w, 18 + i, 15 + w, 18 + i, metal[1])
    c.rect(10, 8, 21, 9, metal[2])
    c.rect(14, 12, 17, 15, GOLD[1])               # emblem
    c.put(15, 13, GOLD[2])


def draw_helmet(c: Canvas, metal: Ramp) -> None:
    c.rect(11, 12, 20, 18, metal[1])
    c.rect(12, 9, 19, 11, metal[1])
    c.rect(12, 9, 19, 9, metal[2])
    c.rect(15, 6, 16, 8, ramp((200, 60, 60))[1])  # crest
    c.rect(13, 15, 14, 18, (30, 28, 40))          # eye slits
    c.rect(17, 15, 18, 18, (30, 28, 40))


def draw_armor(c: Canvas, metal: Ramp) -> None:
    c.rect(11, 9, 20, 21, metal[1])
    c.rect(8, 9, 10, 13, metal[0])                # pauldrons
    c.rect(21, 9, 23, 13, metal[0])
    c.rect(11, 9, 20, 10, metal[2])
    c.line(15, 11, 15, 21, metal[0])              # seam
    c.rect(11, 19, 20, 21, metal[0])


def draw_boots(c: Canvas, _: Ramp) -> None:
    for x0 in (9, 17):
        c.rect(x0, 11, x0 + 3, 21, LEATHER[1])
        c.rect(x0, 21, x0 + 5, 23, LEATHER[0])    # foot
        c.rect(x0, 11, x0 + 3, 12, LEATHER[2])


def draw_ring(c: Canvas, gem: Ramp) -> None:
    for i in range(0, 360, 12):
        import math
        a = math.radians(i)
        c.put(16 + round(math.cos(a) * 5), 18 + round(math.sin(a) * 5),
              GOLD[1])
    c.rect(15, 10, 17, 12, gem[1])
    c.put(16, 11, gem[2])


def draw_potion(c: Canvas, liquid: Ramp) -> None:
    c.rect(14, 7, 17, 8, WOOD[1])                 # cork
    c.rect(14, 9, 17, 12, GLASS[1])               # neck
    c.rect(11, 13, 20, 23, GLASS[1])              # bulb
    c.rect(12, 15, 19, 22, liquid[1])             # liquid
    c.rect(12, 15, 19, 15, liquid[2])
    c.put(13, 17, GLASS[2])                       # shine


def draw_herb(c: Canvas, _: Ramp) -> None:
    green = ramp((80, 170, 70))
    c.line(16, 12, 15, 24, green[0])              # stem
    for dx, dy in ((-4, -2), (4, 0), (-3, 4), (3, 6)):
        x, y = 16 + dx, 14 + dy
        c.rect(x - 1, y - 1, x + 1, y, green[1])
        c.put(x, y - 2, green[2])


def draw_scroll(c: Canvas, _: Ramp) -> None:
    c.rect(10, 10, 21, 22, PAPER[1])
    c.rect(10, 10, 21, 11, PAPER[0])              # top roll
    c.rect(10, 21, 21, 22, PAPER[0])
    for y in (14, 16, 18):
        c.line(12, y, 19, y, (120, 110, 90))      # script lines
    c.rect(15, 12, 16, 20, ramp((200, 60, 60))[1])  # ribbon seal


def draw_book(c: Canvas, gem: Ramp) -> None:
    cover = ramp((110, 60, 40))
    c.rect(10, 8, 21, 23, cover[1])
    c.rect(10, 8, 11, 23, cover[0])               # spine
    c.rect(12, 9, 21, 10, PAPER[2])               # page edge
    c.rect(15, 14, 17, 17, gem[1])                # inset gem
    c.put(16, 15, gem[2])


def draw_gem(c: Canvas, gem: Ramp) -> None:
    c.rect(12, 12, 19, 17, gem[1])
    c.rect(14, 10, 17, 11, gem[1])                # crown
    for i, w in enumerate((3, 2, 1)):
        c.rect(16 - w, 18 + i, 15 + w, 18 + i, gem[1])
    c.put(14, 12, gem[2])
    c.put(13, 13, gem[2])


def draw_coin(c: Canvas, _: Ramp) -> None:
    import math
    for r, col in ((6, GOLD[1]), (4, GOLD[0])):
        for i in range(0, 360, 6):
            a = math.radians(i)
            c.put(16 + round(math.cos(a) * r), 16 + round(math.sin(a) * r),
                  col)
    c.rect(11, 11, 20, 20, GOLD[1])
    c.rect(15, 13, 16, 19, GOLD[2])               # emboss


def draw_key(c: Canvas, metal: Ramp) -> None:
    import math
    for i in range(0, 360, 10):
        a = math.radians(i)
        c.put(13 + round(math.cos(a) * 4), 11 + round(math.sin(a) * 4),
              metal[1])
    c.line(15, 14, 20, 22, metal[1])
    c.line(16, 14, 21, 22, metal[0])
    c.rect(20, 22, 23, 23, metal[1])              # teeth
    c.put(21, 24, metal[1])


def draw_chest(c: Canvas, metal: Ramp) -> None:
    c.rect(8, 13, 23, 23, WOOD[1])
    c.rect(8, 10, 23, 13, WOOD[2])                # lid
    c.rect(8, 16, 23, 16, metal[1])               # band
    c.rect(14, 14, 17, 19, metal[1])              # lock plate
    c.put(15, 16, (30, 28, 40))                   # keyhole
    c.put(16, 16, (30, 28, 40))


def draw_meat(c: Canvas, _: Ramp) -> None:
    meat = ramp((190, 100, 70))
    bone = PAPER
    c.rect(9, 10, 18, 19, meat[1])
    c.rect(10, 9, 17, 9, meat[1])
    c.put(11, 12, meat[2])
    c.line(18, 19, 23, 24, bone[1])               # bone
    c.rect(22, 23, 24, 25, bone[2])


# type -> (draw fn, variant palette dict or None)
TYPES = {
    "sword": (draw_sword, METALS),
    "dagger": (draw_dagger, METALS),
    "axe": (draw_axe, METALS),
    "staff": (draw_staff, GEMS),
    "mace": (draw_mace, METALS),
    "bow": (draw_bow, METALS),
    "shield": (draw_shield, METALS),
    "helmet": (draw_helmet, METALS),
    "armor": (draw_armor, METALS),
    "boots": (draw_boots, None),
    "ring": (draw_ring, GEMS),
    "potion": (draw_potion, LIQUIDS),
    "herb": (draw_herb, None),
    "scroll": (draw_scroll, None),
    "book": (draw_book, GEMS),
    "gem": (draw_gem, GEMS),
    "coin": (draw_coin, None),
    "key": (draw_key, METALS),
    "chest": (draw_chest, METALS),
    "meat": (draw_meat, None),
}


def catalog() -> list[tuple[str, str, str | None]]:
    """(item_id, type, variant) for every icon."""
    items = []
    for name, (_, variants) in TYPES.items():
        if variants is None:
            items.append((name, name, None))
        else:
            for v in variants:
                items.append((f"{name}_{v}", name, v))
    return items


def render_icon(item_type: str, variant: str | None) -> Image.Image:
    fn, variants = TYPES[item_type]
    c = Canvas()
    fn(c, variants[variant] if variants else STEEL)
    return c.finish()


def export_items(out_dir: str | Path, scale: int = 1) -> Path:
    root = Path(out_dir) / "items"
    root.mkdir(parents=True, exist_ok=True)
    items = catalog()
    cols = 10
    rows = (len(items) + cols - 1) // cols
    atlas = Image.new("RGBA", (cols * FRAME, rows * FRAME), (0, 0, 0, 0))
    meta = {"frame_size": FRAME, "columns": cols, "items": {}}
    for i, (item_id, item_type, variant) in enumerate(items):
        icon = render_icon(item_type, variant)
        if scale > 1:
            icon_out = icon.resize((FRAME * scale, FRAME * scale),
                                   Image.NEAREST)
        else:
            icon_out = icon
        icon_out.save(root / f"{item_id}.png")
        atlas.paste(icon, ((i % cols) * FRAME, (i // cols) * FRAME))
        meta["items"][item_id] = {"type": item_type, "variant": variant,
                                  "index": i}
    if scale > 1:
        atlas = atlas.resize((atlas.width * scale, atlas.height * scale),
                             Image.NEAREST)
    atlas.save(root / "atlas.png")
    (root / "atlas.json").write_text(json.dumps(meta, indent=2))
    return root
