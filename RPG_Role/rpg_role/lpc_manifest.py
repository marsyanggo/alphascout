"""Manifest of vendored LPC (Liberated Pixel Cup) assets and job recipes.

Asset paths are relative to assets/lpc/ and mirror the layout of
https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator
(spritesheets/...). Art is CC-BY-SA 3.0 / GPL 3.0 — see assets/lpc/ATTRIBUTION.md.

Templates may reference {skin}, {hair_style}, {hair} and any key defined in a
job's "shared" choices (e.g. {m} for the warrior's metal).
"""

SKINS = ["light", "amber", "olive", "taupe", "bronze", "brown", "black"]

HAIR_STYLES = ["plain", "spiked", "page"]
HAIR_COLORS = ["blonde", "ash", "chestnut", "light_brown", "dark_brown",
               "black", "redhead", "gray"]

BODY = [
    {"z": 10, "path": "body/bodies/male/{skin}"},
    {"z": 100, "path": "head/heads/human/male/{skin}"},
]

HAIR = {"z": 120, "path": "hair/{hair_style}/male/{hair}"}

# Per-job recipe. "hair": eligible styles (empty = headgear covers the head).
# Each part: z position + path template; shared keys keep parts color-matched.
# "attack_anim" picks the base animation the weapon has art for (slash or
# thrust). "oversize" layers are 128/192px per-frame weapon art used during
# that animation (the 64px universal weapon sheets only cover walk/hurt/idle).
JOBS = {
    "hero": {
        "hair": ["plain", "spiked"],
        "attack_anim": "slash",
        "shared": {"shirt": ["blue", "teal", "maroon"],
                   "pant": ["charcoal", "navy", "brown"],
                   "boot": ["brown", "black"]},
        "parts": [
            {"z": 35, "path": "torso/clothes/longsleeve/longsleeve/male/{shirt}"},
            {"z": 20, "path": "legs/pants/male/{pant}"},
            {"z": 25, "path": "feet/boots/male/{boot}"},
            {"z": 140, "path": "weapon/sword/arming/universal/fg/steel"},
            {"z": 9, "path": "weapon/sword/arming/universal/bg/steel"},
        ],
        "oversize": [
            {"anim": "slash", "z": 150, "size": 128,
             "path": "weapon/sword/arming/attack_slash/fg/steel"},
            {"anim": "slash", "z": 8, "size": 128,
             "path": "weapon/sword/arming/attack_slash/bg/steel"},
        ],
    },
    "warrior": {
        "hair": [],
        "attack_anim": "slash",
        "shared": {"m": ["steel", "iron", "bronze"]},
        "parts": [
            {"z": 60, "path": "torso/armour/plate/male/{m}"},
            {"z": 20, "path": "legs/armour/plate/male/{m}"},
            {"z": 26, "path": "feet/boots_plating/universal/male/{m}"},
            {"z": 130, "path": "hat/helmet/barbuta_simple/adult/{m}"},
            {"z": 140, "path": "weapon/blunt/waraxe/waraxe"},
            {"z": 9, "path": "weapon/blunt/waraxe/behind/waraxe"},
        ],
        "oversize": [
            {"anim": "slash", "z": 150, "size": 192,
             "path": "weapon/blunt/waraxe/attack_slash/waraxe"},
            {"anim": "slash", "z": 8, "size": 192,
             "path": "weapon/blunt/waraxe/attack_slash/behind/waraxe"},
        ],
    },
    "mage": {
        "hair": ["plain", "page"],
        "attack_anim": "thrust",
        "shared": {"robe": ["purple", "navy", "black"],
                   "staff": ["medium", "dark"]},
        "parts": [
            {"z": 35, "path": "torso/clothes/longsleeve/longsleeve/male/{robe}"},
            {"z": 20, "path": "legs/skirts/plain/male/{robe}"},
            {"z": 15, "path": "feet/shoes/male/black"},
            {"z": 130, "path": "hat/magic/wizard/base/adult/{robe}"},
            {"z": 140, "path": "weapon/magic/gnarled/universal/foreground/{staff}"},
            {"z": 9, "path": "weapon/magic/gnarled/universal/background/{staff}"},
        ],
        "oversize": [
            {"anim": "thrust", "z": 150, "size": 192,
             "path": "weapon/magic/gnarled/thrust/foreground/{staff}"},
            {"anim": "thrust", "z": 8, "size": 192,
             "path": "weapon/magic/gnarled/thrust/background/{staff}"},
        ],
    },
    "priest": {
        "hair": [],
        "attack_anim": "slash",
        "shared": {"trim": ["white", "tan"]},
        "parts": [
            {"z": 35, "path": "torso/clothes/longsleeve/longsleeve/male/white"},
            {"z": 20, "path": "legs/skirts/plain/male/{trim}"},
            {"z": 15, "path": "feet/shoes/male/brown"},
            {"z": 130, "path": "hat/cloth/hood/adult/hood_white"},
            {"z": 140, "path": "weapon/blunt/mace/mace"},
            {"z": 9, "path": "weapon/blunt/mace/universal_behind/mace"},
        ],
        "oversize": [
            {"anim": "slash", "z": 150, "size": 192,
             "path": "weapon/blunt/mace/attack_slash/mace"},
            {"anim": "slash", "z": 8, "size": 192,
             "path": "weapon/blunt/mace/attack_slash/behind/mace"},
        ],
    },
    "thief": {
        "hair": ["plain", "spiked"],
        "attack_anim": "slash",  # dagger fits the 64px universal sheet
        "shared": {"shirt": ["charcoal", "forest", "slate"],
                   "pant": ["black", "charcoal"],
                   "scarf": ["bandana_red", "charcoal", "forest"]},
        "parts": [
            {"z": 35, "path": "torso/clothes/sleeveless/sleeveless/male/{shirt}"},
            {"z": 20, "path": "legs/pants/male/{pant}"},
            {"z": 15, "path": "feet/shoes/male/black"},
            {"z": 130, "path": "hat/cloth/bandana/adult/{scarf}"},
            {"z": 140, "path": "weapon/sword/dagger/dagger"},
            {"z": 9, "path": "weapon/sword/dagger/behind/dagger"},
        ],
        "oversize": [],
    },
    "monk": {
        "hair": ["spiked", "page"],
        "attack_anim": "slash",  # bare-handed strike
        "shared": {"gi": ["orange", "maroon"],
                   "sash": ["black", "white"],
                   "pant": ["white", "tan"]},
        "parts": [
            {"z": 35, "path": "torso/clothes/sleeveless/sleeveless/male/{gi}"},
            {"z": 65, "path": "torso/waist/sash/male/{sash}"},
            {"z": 20, "path": "legs/pants/male/{pant}"},
            {"z": 15, "path": "feet/shoes/male/brown"},
        ],
        "oversize": [],
    },
}


def all_asset_paths() -> set[str]:
    """Every asset file any (job, seed) combination can reference."""
    paths: set[str] = set()
    for part in BODY:
        for skin in SKINS:
            paths.add(part["path"].format(skin=skin))
    for style in HAIR_STYLES:
        for color in HAIR_COLORS:
            paths.add(HAIR["path"].format(hair_style=style, hair=color))
    for job in JOBS.values():
        keys = job.get("shared", {})
        names = sorted(keys)
        # Cartesian product over shared choices (small: <= 3 keys, <= 3 each).
        combos = [{}]
        for name in names:
            combos = [{**c, name: v} for c in combos for v in keys[name]]
        for part in job["parts"] + job.get("oversize", []):
            for combo in combos:
                paths.add(part["path"].format(**combo))
    return {p + ".png" for p in paths}
