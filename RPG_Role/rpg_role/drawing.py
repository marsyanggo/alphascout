"""Renders one Character in one Pose into a finished 32x32 RGBA frame.

Coordinate system: x grows right, y grows down. Characters are drawn facing
'down', 'up' or 'right'; 'left' is a mirror of 'right'. Body parts are laid
out on a fixed grid and nudged by small per-frame offsets (stride, bob,
arm swing) — classic 2/4-frame retro animation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

from . import FRAME
from .canvas import Canvas
from .character import Character
from .palettes import FX_MAGIC, FX_SLASH, FX_SPECIAL, GOLD, OUTLINE, STEEL, WOOD

# Head box (facing down): x 12..19, y 5..12. Body below, legs to y ~26.
HX0, HX1, HY0, HY1 = 12, 19, 5, 12


@dataclass
class Pose:
    dir: str = "down"          # down / up / left / right
    bob: int = 0               # whole-body y offset (walk bounce)
    stride: int = 0            # -1 / 0 / 1 leg phase
    arms: str = "down"         # down / swing / raise / extend / guard
    weapon: bool = False       # battle poses draw the weapon
    weapon_angle: float = 90.0 # 0 = rest axis, 90 = toward facing dir
    weapon_reach: int = 0      # extra px toward facing dir for thrusts
    lean: int = 0              # x offset (hurt knockback)
    fx: tuple | None = None    # (kind, frame_index) overlay effect
    flat: bool = False         # render lying down (defeated)


def _facing_vec(direction: str) -> tuple[int, int]:
    return {"down": (0, 1), "up": (0, -1), "right": (1, 0), "left": (-1, 0)}[direction]


# ---------------------------------------------------------------- body parts

def _draw_legs(c: Canvas, ch: Character, p: Pose, side_view: bool) -> None:
    y0, y1 = 20, 26
    pants, boot = ch.pants[1], WOOD[0]
    if ch.robe:
        # Robe covers the legs; hem sways with the stride.
        c.rect(12, 13, 19, 24, ch.primary[1])
        c.rect(12, 23, 19, 24, ch.secondary[1])
        c.rect(13 + p.stride, 25, 14 + p.stride, 26, boot)
        c.rect(17 + p.stride, 25, 18 + p.stride, 26, boot)
        return
    if side_view:
        back, front = 13 - p.stride, 16 + p.stride
        c.rect(back, y0, back + 2, y1, ch.pants[0])          # far leg, darker
        c.rect(back, y1 - 1, back + 2, y1, boot)
        c.rect(front, y0, front + 2, y1, pants)
        c.rect(front, y1 - 1, front + 3, y1, boot)           # boot with toe
    else:
        lift = p.stride  # one leg lifts, the other plants
        c.rect(12, y0, 14, y1 - max(0, lift), pants)
        c.rect(12, y1 - 1 - max(0, lift), 14, y1 - max(0, lift), boot)
        c.rect(17, y0, 19, y1 - max(0, -lift), pants)
        c.rect(17, y1 - 1 - max(0, -lift), 19, y1 - max(0, -lift), boot)


def _draw_torso(c: Canvas, ch: Character, p: Pose, side_view: bool) -> None:
    if side_view:
        c.rect(13, 13, 18, 19, ch.primary[1])
        c.rect(13, 18, 18, 19, ch.secondary[0])              # belt
    else:
        c.rect(12, 13, 19, 19, ch.primary[1])
        c.rect(12, 18, 19, 19, ch.secondary[0])
        c.rect(12, 13, 19, 13, ch.primary[0])                # shoulder trim


def _draw_arms(c: Canvas, ch: Character, p: Pose) -> None:
    sleeve, hand = ch.primary[0], ch.skin[1]
    if p.dir in ("down", "up"):
        swing = p.stride if p.arms == "swing" else 0
        if p.arms == "raise":                                # spell-casting
            for x0 in (10, 20):
                c.rect(x0, 9, x0 + 1, 14, sleeve)
                c.rect(x0, 8, x0 + 1, 9, hand)
        else:
            c.rect(10, 14 + swing, 11, 18 + swing, sleeve)
            c.rect(10, 17 + swing, 11, 18 + swing, hand)
            c.rect(20, 14 - swing, 21, 18 - swing, sleeve)
            c.rect(20, 17 - swing, 21, 18 - swing, hand)
    else:                                                    # side view: near arm only
        if p.arms == "raise":
            c.rect(16, 9, 17, 14, sleeve)
            c.rect(16, 8, 17, 9, hand)
        elif p.arms == "extend":
            c.rect(16, 14, 20, 15, sleeve)
            c.rect(20, 14, 21, 15, hand)
        elif p.arms == "guard":
            c.rect(15, 12, 16, 16, sleeve)
            c.rect(15, 11, 16, 12, hand)
        else:
            c.rect(16, 14 + p.stride, 17, 18 + p.stride, sleeve)
            c.rect(16, 17 + p.stride, 17, 18 + p.stride, hand)


def _draw_head(c: Canvas, ch: Character, p: Pose) -> None:
    c.rect(HX0, HY0, HX1, HY1, ch.skin[1])
    if p.dir == "down":
        c.put(14, 9, OUTLINE)
        c.put(17, 9, OUTLINE)
    elif p.dir == "right":
        c.put(17, 9, OUTLINE)
    _draw_hat(c, ch, p)


def _draw_hat(c: Canvas, ch: Character, p: Pose) -> None:
    hair = ch.hair[1]
    back = p.dir == "up"
    side = p.dir == "right"
    if ch.hat == "helmet":
        c.rect(HX0, HY0 - 1, HX1, HY0 + 3, STEEL[1])
        c.rect(HX0, HY0 + 4, HX0, HY1 - 2, STEEL[0])         # cheek guards
        c.rect(HX1, HY0 + 4, HX1, HY1 - 2, STEEL[0])
        c.put(15, HY0 - 2, ch.secondary[1])                  # crest
        c.put(16, HY0 - 2, ch.secondary[1])
        return
    if ch.hat == "wizard_hat":
        c.rect(HX0 - 2, HY0 + 2, HX1 + 2, HY0 + 3, ch.primary[0])   # brim
        c.rect(HX0 + 1, HY0, HX1 - 1, HY0 + 1, ch.primary[1])
        c.rect(HX0 + 3, HY0 - 2, HX1 - 3, HY0 - 1, ch.primary[1])
        c.put(HX0 + 3, HY0 - 3, ch.primary[1])               # bent tip
        c.put(HX0 + 2, HY0 - 3, ch.primary[0])
        return
    if ch.hat == "hood":
        c.rect(HX0 - 1, HY0 - 1, HX1 + 1, HY0 + 2, ch.primary[1])
        c.rect(HX0 - 1, HY0 + 3, HX0, HY1 + 1, ch.primary[1])
        c.rect(HX1, HY0 + 3, HX1 + 1, HY1 + 1, ch.primary[1])
        if back or side:
            c.rect(HX0, HY0, HX1, HY1, ch.primary[1])
        return
    # Hair-based styles.
    if back:
        c.rect(HX0, HY0, HX1, HY1, hair)
        if ch.hat == "long":
            c.rect(HX0 + 1, HY1 + 1, HX1 - 1, HY1 + 3, hair)
    elif side:
        c.rect(HX0, HY0, HX1, HY0 + 2, hair)
        c.rect(HX0, HY0 + 3, HX0 + 3, HY1 - 1, hair)         # back of head
        if ch.hat == "long":
            c.rect(HX0, HY1, HX0 + 2, HY1 + 3, hair)
    else:
        c.rect(HX0, HY0, HX1, HY0 + 2, hair)
        c.rect(HX0, HY0 + 3, HX0, HY0 + 4, hair)
        c.rect(HX1, HY0 + 3, HX1, HY0 + 4, hair)
        if ch.hat == "long":
            c.rect(HX0, HY0 + 3, HX0, HY1 + 2, hair)
            c.rect(HX1, HY0 + 3, HX1, HY1 + 2, hair)
    if ch.hat == "spiky":
        for x in (HX0 + 1, HX0 + 3, HX0 + 5, HX0 + 7):
            c.put(x, HY0 - 1, hair)
    if ch.hat == "bandana":
        c.rect(HX0, HY0, HX1, HY0 + 2, ch.secondary[1])
        if side or back:
            c.rect(HX0 - 1, HY0 + 2, HX0, HY0 + 4, ch.secondary[1])  # knot tails
    if ch.hat == "headband":
        c.rect(HX0, HY0 + 2, HX1, HY0 + 2, ch.secondary[1])


def _draw_cape(c: Canvas, ch: Character, p: Pose) -> None:
    if not ch.cape:
        return
    cape = ch.secondary[1]
    if p.dir == "up":
        c.rect(12, 13, 19, 23, cape)
        c.rect(12, 22, 19, 23, ch.secondary[0])
    elif p.dir == "right":
        c.rect(10, 13, 12, 22 + p.stride, cape)
    else:
        c.rect(11, 13, 11, 20, cape)
        c.rect(20, 13, 20, 20, cape)


# ------------------------------------------------------------------ weapons

def _swing_axes(direction: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """(rest_axis, facing_axis) of the swing plane.

    weapon_angle rotates from rest (0deg) toward facing (90deg). For side
    view rest = up; for down/up views rest = outward to the weapon-hand side.
    """
    if direction == "right":
        return (0, -1), (1, 0)
    if direction == "down":
        return (1, 0), (0, 1)   # right hand at x=21, weapon sweeps out->down
    return (-1, 0), (0, -1)     # up: left side visible, sweeps out->up


def _weapon_tip(hand: tuple[int, int], direction: str, angle: float,
                length: float) -> tuple[int, int]:
    (rx, ry), (fx, fy) = _swing_axes(direction)
    rad = math.radians(angle)
    dx = math.cos(rad) * rx + math.sin(rad) * fx
    dy = math.cos(rad) * ry + math.sin(rad) * fy
    return (round(hand[0] + dx * length), round(hand[1] + dy * length))


def _draw_weapon(c: Canvas, ch: Character, p: Pose) -> None:
    if not p.weapon or ch.weapon == "fists":
        return
    fx, fy = _facing_vec(p.dir)
    if p.dir == "right":
        hand = (20 + p.weapon_reach, 15)
        if p.arms == "raise":
            hand = (17, 8)
        elif p.arms == "guard":
            hand = (16, 11)
        elif p.arms == "down":
            hand = (17, 17)
    elif p.dir == "down":
        hand = (21, 17 + p.weapon_reach)
        if p.arms == "raise":
            hand = (21, 8)
    else:  # up
        hand = (10, 17 - p.weapon_reach)
        if p.arms == "raise":
            hand = (10, 8)
    angle = p.weapon_angle
    # A raised weapon is held overhead pointing straight up in every
    # direction; the side-view axes give exactly that for angle 0.
    tip_dir = "right" if p.arms == "raise" else p.dir

    def tip(length: float) -> tuple[int, int]:
        return _weapon_tip(hand, tip_dir, angle, length)

    if ch.weapon == "sword":
        gx, gy = tip(-2)
        c.line(hand[0], hand[1], gx, gy, WOOD[1])            # grip
        bx, by = tip(8)
        c.line(hand[0], hand[1], bx, by, STEEL[2])
        mx, my = tip(2)
        c.rect(mx - 1, my, mx + 1, my, GOLD[1])              # crossguard
    elif ch.weapon == "axe":
        bx, by = tip(7)
        c.line(hand[0], hand[1], bx, by, WOOD[1])
        hx2, hy2 = tip(5)
        c.rect(hx2 - 2, hy2 - 2, hx2 + 1, hy2 + 1, STEEL[1])
    elif ch.weapon == "staff":
        gx, gy = tip(-3)
        bx, by = tip(8)
        c.line(gx, gy, bx, by, WOOD[1])
        c.rect(bx - 1, by - 1, bx, by, FX_MAGIC[2])
        c.put(bx, by - 1, FX_MAGIC[1])
    elif ch.weapon == "mace":
        bx, by = tip(6)
        c.line(hand[0], hand[1], bx, by, WOOD[1])
        c.rect(bx - 1, by - 1, bx + 1, by + 1, STEEL[1])
        c.put(bx, by, GOLD[1])
    elif ch.weapon == "dagger":
        bx, by = tip(5)
        c.line(hand[0], hand[1], bx, by, STEEL[2])
        mx, my = tip(1)
        c.put(mx, my, GOLD[1])


# ------------------------------------------------------------------ effects

def _fx_layer(p: Pose) -> Image.Image | None:
    if p.fx is None:
        return None
    kind, f = p.fx
    img = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    px = img.load()

    def put(x: int, y: int, color) -> None:
        if 0 <= x < FRAME and 0 <= y < FRAME:
            px[x, y] = (*color, 255)

    fxv = _facing_vec(p.dir)
    cx, cy = 16 + fxv[0] * 10, 16 + fxv[1] * 10  # effect focus, in front

    if kind == "slash":
        # Crescent arc sweeping in front of the character.
        col = FX_SLASH[min(f, len(FX_SLASH) - 1)]
        for deg in range(-60, 61, 6):
            a = math.radians(deg)
            r = 7 - f
            ox = math.cos(a) * r * fxv[0] + math.sin(a) * r * abs(fxv[1])
            oy = math.cos(a) * r * fxv[1] + math.sin(a) * r * abs(fxv[0])
            put(cx + round(ox), cy + round(oy), col)
            put(cx + round(ox * 0.75), cy + round(oy * 0.75),
                FX_SLASH[min(f + 1, 2)])
    elif kind == "special":
        if f < 2:
            # Charge-up: a small glow ring gathering around the character.
            r = 4 - f
            for i in range(0, 360, 30):
                a = math.radians(i + f * 15)
                put(16 + round(math.cos(a) * (r + 4)),
                    16 + round(math.sin(a) * (r + 4)), FX_SPECIAL[3 - f])
        elif f < 4:
            # Burst: a wide double crescent, bigger than a normal slash.
            for ri, col in ((9, FX_SPECIAL[f - 1]), (11, FX_SPECIAL[0])):
                for deg in range(-80, 81, 5):
                    a = math.radians(deg)
                    ox = math.cos(a) * ri * fxv[0] + math.sin(a) * ri * abs(fxv[1])
                    oy = math.cos(a) * ri * fxv[1] + math.sin(a) * ri * abs(fxv[0])
                    put(cx - fxv[0] * 4 + round(ox), cy - fxv[1] * 4 + round(oy), col)
        if f >= 3:
            # Radial sparks flying outward as the burst fades.
            for i in range(8):
                a = math.radians(i * 45 + f * 12)
                d = 9 + (f - 3) * 3
                put(cx + round(math.cos(a) * d), cy + round(math.sin(a) * d),
                    FX_SPECIAL[(i + f) % 2])
    elif kind == "magic":
        col = FX_MAGIC[f % len(FX_MAGIC)]
        # Magic circle under the feet.
        w = 8 + f
        for i in range(0, 360, 12):
            a = math.radians(i)
            put(16 + round(math.cos(a) * w / 2), 28 + round(math.sin(a) * 2), col)
        # Rising sparkles, deterministic per frame.
        for i in range(6):
            sx = 8 + (i * 37 + f * 11) % 17
            sy = 24 - ((i * 23 + f * 7) % 20)
            put(sx, sy, FX_MAGIC[(i + f) % len(FX_MAGIC)])
            if (i + f) % 2 == 0:
                put(sx, sy - 1, FX_MAGIC[0])
    return img


# ------------------------------------------------------------------- render

def render_frame(ch: Character, p: Pose) -> Image.Image:
    mirrored = p.dir == "left"
    direction = "right" if mirrored else p.dir
    p2 = Pose(**{**p.__dict__, "dir": direction})
    side = direction == "right"

    c = Canvas()
    if direction != "up":
        _draw_cape(c, ch, p2)
    _draw_legs(c, ch, p2, side)
    _draw_torso(c, ch, p2, side)
    if direction == "up":
        _draw_cape(c, ch, p2)
    _draw_arms(c, ch, p2)
    _draw_head(c, ch, p2)
    _draw_weapon(c, ch, p2)

    frame = c.finish()

    if p2.bob or p2.lean:
        shifted = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
        shifted.paste(frame, (p2.lean, p2.bob))
        frame = shifted
    if p2.flat:
        flat = frame.crop((8, 2, 24, 30)).rotate(90, expand=True)
        frame = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
        frame.paste(flat, (2, 12))
    if mirrored:
        frame = frame.transpose(Image.FLIP_LEFT_RIGHT)

    fx = _fx_layer(p)  # effects use the original direction (incl. 'left')
    if fx is not None:
        frame = Image.alpha_composite(frame, fx)
    return frame
