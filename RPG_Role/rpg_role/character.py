"""Character spec: everything visual about one character, derived from
(job, seed) so the same inputs always produce the same sprite."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .palettes import HAIR_COLORS, JOBS, SKIN_TONES, Ramp, ramp, shift


@dataclass
class Character:
    job: str
    seed: int
    skin: Ramp
    hair: Ramp
    hat: str           # short/spiky/long/wizard_hat/hood/helmet/bandana/headband
    primary: Ramp      # tunic / armor / robe
    secondary: Ramp    # trim / cape / bandana
    pants: Ramp
    weapon: str        # sword/axe/staff/mace/dagger/fists
    cape: bool
    robe: bool         # robe covers the legs (mage / priest)


def make_character(job: str, seed: int = 0) -> Character:
    if job not in JOBS:
        raise ValueError(f"unknown job {job!r}; choose from {sorted(JOBS)}")
    spec = JOBS[job]
    rng = random.Random(f"{job}:{seed}")

    jitter = rng.randint(-18, 18)
    return Character(
        job=job,
        seed=seed,
        skin=rng.choice(SKIN_TONES),
        hair=rng.choice(HAIR_COLORS),
        hat=rng.choice(spec["hats"]),
        primary=ramp(shift(spec["primary"], jitter)),
        secondary=ramp(shift(spec["secondary"], jitter // 2)),
        pants=ramp(shift(spec["pants"], jitter // 2)),
        weapon=spec["weapon"],
        cape=spec["cape"],
        robe=spec.get("robe", False),
    )
