"""Smoke tests: every job renders every animation, deterministically."""

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rpg_role import FRAME
from rpg_role.animations import ANIMATIONS, DIRECTIONS
from rpg_role.character import make_character
from rpg_role.palettes import JOBS
from rpg_role.sheets import build_master_sheet, build_sheet


def png_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_all_jobs_all_animations():
    for job in JOBS:
        ch = make_character(job, seed=3)
        for name, spec in ANIMATIONS.items():
            sheet = build_sheet(ch, name)
            rows = len(DIRECTIONS) if spec["dirs"] else 1
            assert sheet.size == (len(spec["frames"]) * FRAME, rows * FRAME), \
                f"{job}/{name} unexpected sheet size {sheet.size}"


def test_deterministic():
    a = build_master_sheet(make_character("hero", seed=42))[0]
    b = build_master_sheet(make_character("hero", seed=42))[0]
    assert png_bytes(a) == png_bytes(b)


def test_seeds_differ():
    a = build_master_sheet(make_character("thief", seed=1))[0]
    b = build_master_sheet(make_character("thief", seed=2))[0]
    assert png_bytes(a) != png_bytes(b)


def test_metadata():
    _, meta = build_master_sheet(make_character("mage", seed=0))
    assert meta["frame_size"] == FRAME
    assert set(meta["animations"]) == set(ANIMATIONS)
    walk = meta["animations"]["walk"]
    assert walk["frames"] == 4 and walk["rows"] == DIRECTIONS
    json.dumps(meta)  # must be serializable


def test_lpc_all_jobs():
    from rpg_role import lpc

    for job in JOBS:
        ch = lpc.LpcCharacter(job, seed=5)
        for name, spec in lpc.exports(ch).items():
            sheet = lpc.build_sheet(ch, name)
            cell = ch.cell_size(spec["source"])
            rows = 1 if spec["source"] == "hurt" else 4
            assert sheet.size == (len(spec["frames"]) * cell, rows * cell), \
                f"{job}/{name} unexpected sheet size {sheet.size}"


def test_lpc_deterministic():
    from rpg_role import lpc

    a = lpc.LpcCharacter("hero", 9)
    b = lpc.LpcCharacter("hero", 9)
    assert a.layers == b.layers
    assert png_bytes(a.sheet) == png_bytes(b.sheet)


def test_lpc_monsters():
    from rpg_role import lpc
    from rpg_role.lpc_manifest import MONSTERS

    for m in MONSTERS:
        ch = lpc.LpcCharacter(m, seed=2)
        sheet = lpc.build_sheet(ch, "attack")
        assert sheet.width > 0, m


def test_slimes():
    from rpg_role.monsters import SLIME_ANIMS, SLIME_COLORS, _draw_slime

    for color, palette in SLIME_COLORS.items():
        for spec in SLIME_ANIMS.values():
            for f in spec["frames"]:
                img = _draw_slime(palette, *f)
                assert img.size == (FRAME, FRAME)
                assert img.getbbox(), f"empty slime frame {color} {f}"


def test_items():
    from rpg_role.items import catalog, render_icon

    seen = set()
    for item_id, item_type, variant in catalog():
        assert item_id not in seen
        seen.add(item_id)
        icon = render_icon(item_type, variant)
        assert icon.size == (FRAME, FRAME)
        assert icon.getbbox(), f"empty icon {item_id}"
    assert len(seen) >= 50


def test_overworld():
    from rpg_role.worldmap import OVERWORLD_TILES, generate_overworld

    a = generate_overworld(40, 30, 3)
    b = generate_overworld(40, 30, 3)
    assert a == b, "overworld not deterministic"
    assert len(a["tiles"]) == 30 and len(a["tiles"][0]) == 40
    used = {t for row in a["tiles"] for t in row}
    assert used <= set(OVERWORLD_TILES)
    kinds = {f["type"] for f in a["features"]}
    assert {"castle", "town"} <= kinds


def test_dungeon():
    from rpg_role.worldmap import DUNGEON_TILES, generate_dungeon

    d = generate_dungeon(36, 24, 4)
    used = {t for row in d["tiles"] for t in row}
    assert used <= set(DUNGEON_TILES)
    flat = [t for row in d["tiles"] for t in row]
    assert flat.count("stairs_up") == 1 and flat.count("stairs_down") == 1
    # Every walkable tile must be reachable from the entry stairs.
    h, w = len(d["tiles"]), len(d["tiles"][0])
    start = next((x, y) for y in range(h) for x in range(w)
                 if d["tiles"][y][x] == "stairs_up")
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen
                    and d["tiles"][ny][nx] != "wall"):
                seen.add((nx, ny))
                todo.append((nx, ny))
    walkable = {(x, y) for y in range(h) for x in range(w)
                if d["tiles"][y][x] != "wall"}
    assert seen == walkable, "dungeon has unreachable areas"


def test_hd_pipeline():
    from rpg_role import lpc
    from rpg_role.hd import enhance
    from rpg_role.monsters import SLIME_COLORS, _draw_slime

    ch = lpc.LpcCharacter("hero", 1)
    frame = ch.frame("walk", "down", 0)
    hd = enhance(frame)
    assert hd.size == (frame.width * 4, frame.height * 4)
    assert hd.getbbox(), "HD frame is empty"
    # Deterministic.
    assert hd.tobytes() == enhance(ch.frame("walk", "down", 0)).tobytes()
    # Works on the 32px slime frames too.
    s = enhance(_draw_slime(SLIME_COLORS["blue"], 0, 0, False))
    assert s.size == (128, 128)
    # HD sheets are 4x the lpc cell size.
    sheet = lpc.build_sheet(ch, "attack", hd=True)
    cell = ch.cell_size("slash") * 4
    assert sheet.size == (6 * cell, 4 * cell)


def test_ai_postprocess():
    """The AI art post pipeline must work offline on synthetic input."""
    from PIL import Image, ImageDraw

    from rpg_role.ai import PROMPTS, remove_background, stylize

    img = Image.new("RGB", (512, 512), (250, 250, 248))
    d = ImageDraw.Draw(img)
    d.ellipse((150, 150, 360, 400), fill=(60, 120, 200))
    cut = remove_background(img.convert("RGBA"))
    assert cut.getpixel((5, 5))[3] == 0, "background not removed"
    assert cut.getpixel((255, 275))[3] == 255, "subject was erased"
    out = stylize(img.convert("RGBA"))
    assert out.getbbox(), "stylized output is empty"
    for kind, tpl in PROMPTS.items():
        assert "{subject}" in tpl, kind


def test_tiles_render():
    from rpg_role.worldmap import (DUNGEON_TILES, OVERWORLD_TILES, TILE,
                                   draw_tile)

    for t in OVERWORLD_TILES + DUNGEON_TILES:
        img = draw_tile(t, 1)
        assert img.size == (TILE, TILE), t


if __name__ == "__main__":
    for fn in (test_all_jobs_all_animations, test_deterministic,
               test_seeds_differ, test_metadata, test_lpc_all_jobs,
               test_lpc_deterministic, test_lpc_monsters, test_slimes,
               test_items, test_overworld, test_dungeon, test_hd_pipeline,
               test_ai_postprocess,
               test_tiles_render):
        fn()
        print(f"ok: {fn.__name__}")
    print("all tests passed")
