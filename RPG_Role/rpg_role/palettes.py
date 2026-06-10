"""Color ramps and per-job style definitions.

A "ramp" is (dark, base, light) — shading is applied automatically by the
canvas, so most drawing uses the base color and lets the shader pick the
dark/light variants.
"""

from __future__ import annotations

OUTLINE = (34, 32, 52)

Color = tuple[int, int, int]
Ramp = tuple[Color, Color, Color]


def _clamp(v: int) -> int:
    return max(0, min(255, v))


def shift(c: Color, d: int) -> Color:
    return (_clamp(c[0] + d), _clamp(c[1] + d), _clamp(c[2] + d))


def ramp(base: Color) -> Ramp:
    return (shift(base, -45), base, shift(base, 45))


SKIN_TONES: list[Ramp] = [
    ramp((236, 188, 148)),
    ramp((219, 164, 122)),
    ramp((184, 128, 92)),
    ramp((136, 88, 60)),
]

HAIR_COLORS: list[Ramp] = [
    ramp((58, 46, 38)),    # dark brown
    ramp((120, 80, 44)),   # brown
    ramp((216, 176, 80)),  # blond
    ramp((176, 60, 44)),   # red
    ramp((70, 90, 120)),   # blue-black
    ramp((150, 150, 158)), # silver
]

STEEL = ramp((150, 156, 170))
WOOD = ramp((122, 82, 46))
GOLD = ramp((220, 180, 70))

# Effect palettes: list of colors cycled over effect frames.
FX_SLASH = [(255, 255, 255), (255, 232, 140), (255, 180, 60)]
FX_SPECIAL = [(255, 255, 255), (255, 210, 80), (255, 120, 40), (220, 60, 30)]
FX_MAGIC = [(255, 255, 255), (150, 220, 255), (110, 140, 255), (190, 120, 255)]

# Per-job visual identity. "primary" = tunic/armor, "secondary" = pants/trim.
JOBS: dict[str, dict] = {
    "hero": {
        "primary": (52, 100, 180),    # blue tunic
        "secondary": (190, 70, 50),   # red trim / cape
        "pants": (78, 84, 102),
        "weapon": "sword",
        "hats": ["short", "spiky"],
        "cape": True,
    },
    "warrior": {
        "primary": (160, 70, 50),     # red armor
        "secondary": (110, 116, 130), # steel
        "pants": (96, 100, 112),
        "weapon": "axe",
        "hats": ["helmet"],
        "cape": False,
    },
    "mage": {
        "primary": (110, 70, 170),    # purple robe
        "secondary": (60, 50, 90),
        "pants": (60, 50, 90),
        "weapon": "staff",
        "hats": ["wizard_hat"],
        "cape": False,
        "robe": True,
    },
    "priest": {
        "primary": (225, 222, 210),   # white robe
        "secondary": (70, 140, 130),  # teal trim
        "pants": (200, 196, 186),
        "weapon": "mace",
        "hats": ["hood"],
        "cape": False,
        "robe": True,
    },
    "thief": {
        "primary": (70, 130, 80),     # green garb
        "secondary": (50, 52, 60),    # black
        "pants": (56, 58, 66),
        "weapon": "dagger",
        "hats": ["bandana", "short"],
        "cape": False,
    },
    "monk": {
        "primary": (210, 130, 50),    # orange gi
        "secondary": (120, 60, 30),
        "pants": (228, 220, 200),
        "weapon": "fists",
        "hats": ["headband", "spiky"],
        "cape": False,
    },
}
