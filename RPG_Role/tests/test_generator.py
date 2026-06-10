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


if __name__ == "__main__":
    for fn in (test_all_jobs_all_animations, test_deterministic,
               test_seeds_differ, test_metadata):
        fn()
        print(f"ok: {fn.__name__}")
    print("all tests passed")
