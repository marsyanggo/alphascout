"""Animation definitions: each animation maps to a list of Pose kwargs.

Directions are filled in by the sheet builder; poses here describe one
direction's frame sequence. fps is a playback suggestion stored in the
metadata for game engines.
"""

from __future__ import annotations

DIRECTIONS = ["down", "left", "right", "up"]

# name -> {"frames": [pose kwargs...], "fps": int, "dirs": bool}
ANIMATIONS: dict[str, dict] = {
    "idle": {
        "fps": 3,
        "dirs": True,
        "frames": [
            {},
            {"bob": 1, "stride": 0},
        ],
    },
    "walk": {
        "fps": 8,
        "dirs": True,
        "frames": [
            {"stride": 1, "arms": "swing", "bob": -1},
            {},
            {"stride": -1, "arms": "swing", "bob": -1},
            {},
        ],
    },
    "attack": {
        "fps": 10,
        "dirs": True,
        "frames": [
            {"weapon": True, "weapon_angle": -30, "lean": -1},          # windup
            {"weapon": True, "weapon_angle": 10},                       # raised
            {"weapon": True, "weapon_angle": 80, "weapon_reach": 1,
             "arms": "extend", "lean": 1, "fx": ("slash", 0)},          # swing
            {"weapon": True, "weapon_angle": 110, "weapon_reach": 2,
             "arms": "extend", "lean": 1, "fx": ("slash", 1)},          # follow
        ],
    },
    "special": {
        "fps": 10,
        "dirs": True,
        "frames": [
            {"weapon": True, "weapon_angle": -40, "lean": -1,
             "fx": ("special", 0)},                                     # charge
            {"weapon": True, "weapon_angle": -20, "lean": -1, "bob": -1,
             "fx": ("special", 1)},
            {"weapon": True, "weapon_angle": 70, "weapon_reach": 2,
             "arms": "extend", "lean": 2, "fx": ("special", 2)},        # burst
            {"weapon": True, "weapon_angle": 100, "weapon_reach": 2,
             "arms": "extend", "lean": 2, "fx": ("special", 3)},
            {"weapon": True, "weapon_angle": 110, "weapon_reach": 1,
             "arms": "extend", "lean": 1, "fx": ("special", 4)},        # fade
            {"weapon": True, "weapon_angle": 110, "fx": ("special", 5)},
        ],
    },
    "cast": {
        "fps": 8,
        "dirs": True,
        "frames": [
            {"arms": "raise", "weapon": True, "weapon_angle": 0,
             "fx": ("magic", 0)},
            {"arms": "raise", "weapon": True, "weapon_angle": 0, "bob": -1,
             "fx": ("magic", 1)},
            {"arms": "raise", "weapon": True, "weapon_angle": 0,
             "fx": ("magic", 2)},
            {"arms": "raise", "weapon": True, "weapon_angle": 0, "bob": -1,
             "fx": ("magic", 3)},
        ],
    },
    "hurt": {
        "fps": 8,
        "dirs": True,
        "frames": [
            {"lean": -2, "arms": "guard", "bob": 1},
            {"lean": -1, "arms": "guard"},
        ],
    },
    "dead": {
        "fps": 1,
        "dirs": False,
        "frames": [
            {"flat": True},
        ],
    },
}
