"""DQ-style tile map generator: overworld (noise-based continents, biomes,
castle/towns/caves with connecting paths) and dungeons (rooms + corridors).

Tiles are drawn procedurally at 32px in the same retro palette as the mini
sprites. Output: map.png (rendered), map.json (tile grid + features, ready
for a game engine) and tileset.png (one frame per tile type).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image

TILE = 32

PAL = {
    "deep": (38, 70, 140), "water": (58, 100, 180), "wave": (120, 160, 220),
    "sand": (222, 198, 140), "sand_d": (196, 168, 110),
    "grass": (96, 160, 80), "grass_d": (74, 134, 64),
    "forest": (52, 110, 58), "trunk": (104, 70, 40), "leaf": (40, 90, 46),
    "leaf_l": (78, 140, 70),
    "rock": (134, 126, 122), "rock_d": (104, 96, 94), "snow": (235, 238, 245),
    "swamp": (70, 104, 84), "murk": (52, 80, 66),
    "path": (180, 150, 100), "path_d": (152, 124, 80),
    "roof": (190, 70, 50), "wall_h": (226, 214, 190), "door": (90, 60, 36),
    "keep": (168, 164, 172), "keep_d": (128, 124, 134), "flag": (210, 60, 50),
    "cave": (30, 26, 36),
    "floor": (140, 132, 124), "floor_d": (118, 110, 104),
    "dwall": (70, 62, 70), "dwall_d": (52, 46, 54),
    "stair": (96, 90, 86), "wood": (122, 82, 46), "gold": (220, 180, 70),
}


# ------------------------------------------------------------------ tiles

def _speckle(px, rng, color, n=14):
    for _ in range(n):
        x, y = rng.randrange(TILE), rng.randrange(TILE)
        px[x, y] = (*color, 255)


def draw_tile(name: str, variant_seed: int = 0) -> Image.Image:
    """One 32px tile; variant_seed varies the texture, not the layout."""
    rng = random.Random(f"{name}:{variant_seed}")
    img = Image.new("RGBA", (TILE, TILE))
    px = img.load()

    def fill(color):
        for y in range(TILE):
            for x in range(TILE):
                px[x, y] = (*color, 255)

    def rect(x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(TILE, y1 + 1)):
            for x in range(max(0, x0), min(TILE, x1 + 1)):
                px[x, y] = (*color, 255)

    if name in ("water", "deep"):
        fill(PAL[name])
        for _ in range(4):                       # wave dashes
            x, y = rng.randrange(2, 26), rng.randrange(2, 30)
            rect(x, y, x + rng.randrange(3, 6), y, PAL["wave"])
    elif name == "sand":
        fill(PAL["sand"])
        _speckle(px, rng, PAL["sand_d"])
    elif name == "grass":
        fill(PAL["grass"])
        _speckle(px, rng, PAL["grass_d"], 20)
    elif name == "forest":
        fill(PAL["forest"])
        for _ in range(3):                       # tree clumps
            cx, cy = rng.randrange(4, 28), rng.randrange(6, 28)
            rect(cx - 1, cy, cx, cy + 3, PAL["trunk"])
            rect(cx - 4, cy - 6, cx + 3, cy - 1, PAL["leaf"])
            rect(cx - 3, cy - 7, cx + 2, cy - 6, PAL["leaf"])
            rect(cx - 3, cy - 5, cx - 1, cy - 4, PAL["leaf_l"])
    elif name == "mountain":
        fill(PAL["grass"])
        _speckle(px, rng, PAL["grass_d"], 10)
        for cx, cy, h in ((10, 26, 14), (22, 28, 18)):   # two peaks
            for i in range(h):
                w = round((h - i) * 0.7)
                rect(cx - w, cy - i, cx + w, cy - i,
                     PAL["rock"] if i < h - 4 else PAL["snow"])
            for i in range(0, h - 4, 3):         # ridge shading
                px[min(cx, 31), cy - i] = (*PAL["rock_d"], 255)
    elif name == "swamp":
        fill(PAL["swamp"])
        for _ in range(5):
            x, y = rng.randrange(2, 24), rng.randrange(2, 28)
            rect(x, y, x + rng.randrange(4, 8), y + 1, PAL["murk"])
    elif name == "path":
        fill(PAL["path"])
        _speckle(px, rng, PAL["path_d"])
    elif name == "town":
        fill(PAL["grass"])
        _speckle(px, rng, PAL["grass_d"], 10)
        rect(6, 14, 25, 27, PAL["wall_h"])       # house
        rect(4, 8, 27, 13, PAL["roof"])
        rect(6, 6, 25, 7, PAL["roof"])
        rect(13, 19, 18, 27, PAL["door"])
        rect(8, 17, 11, 20, PAL["water"])        # window
        rect(20, 17, 23, 20, PAL["water"])
    elif name == "castle":
        fill(PAL["grass"])
        rect(4, 10, 27, 28, PAL["keep"])
        for tx in (4, 24):                       # towers
            rect(tx, 5, tx + 3, 28, PAL["keep_d"])
            rect(tx, 4, tx + 3, 4, PAL["keep"])
        rect(13, 18, 18, 28, PAL["cave"])        # gate
        rect(15, 0, 15, 4, PAL["keep_d"])        # flagpole
        rect(16, 1, 20, 3, PAL["flag"])
        for bx in range(6, 24, 4):               # battlements
            rect(bx, 8, bx + 1, 9, PAL["keep_d"])
    elif name == "cave":
        fill(PAL["grass"])
        for i in range(12):                      # rocky mound
            w = 12 - i
            rect(16 - w, 26 - i, 15 + w, 26 - i, PAL["rock"])
        rect(12, 18, 19, 26, PAL["cave"])        # entrance
    elif name == "floor":
        fill(PAL["floor"])
        for gx in (0, 16):
            for gy in (0, 16):
                rect(gx, gy, gx + 15, gy, PAL["floor_d"])
                rect(gx, gy, gx, gy + 15, PAL["floor_d"])
        _speckle(px, rng, PAL["floor_d"], 6)
    elif name == "wall":
        fill(PAL["dwall"])
        for row in range(4):                     # brick courses
            y = row * 8
            rect(0, y, 31, y, PAL["dwall_d"])
            off = 8 if row % 2 else 0
            for bx in range(off, 32, 16):
                rect(bx, y, bx, y + 7, PAL["dwall_d"])
    elif name == "door":
        img = draw_tile("floor", variant_seed)
        px = img.load()
        rect = None  # re-bind helpers to the new image
        for y in range(6, 28):
            for x in range(10, 22):
                px[x, y] = (*PAL["door"], 255)
        for x in range(10, 22):
            px[x, 6] = (*PAL["wood"], 255)
        px[19, 17] = (*PAL["gold"], 255)         # handle
        return img
    elif name in ("stairs_down", "stairs_up"):
        img = draw_tile("floor", variant_seed)
        px = img.load()
        steps = range(4) if name == "stairs_down" else range(3, -1, -1)
        for i, s in enumerate(steps):
            shade = 60 - s * 18
            for y in range(6 + i * 5, 11 + i * 5):
                for x in range(7 + s * 2, 25 - s * 2):
                    px[x, y] = (PAL["stair"][0] - shade,
                                PAL["stair"][1] - shade,
                                PAL["stair"][2] - shade, 255)
        return img
    elif name == "chest":
        img = draw_tile("floor", variant_seed)
        px = img.load()
        for y in range(12, 26):
            for x in range(7, 25):
                px[x, y] = (*PAL["wood"], 255)
        for x in range(7, 25):
            px[x, 12] = (*PAL["gold"], 255)
            px[x, 17] = (*PAL["gold"], 255)
        for y in range(14, 21):
            px[15, y] = (*PAL["gold"], 255)
            px[16, y] = (*PAL["gold"], 255)
        return img
    else:
        raise ValueError(f"unknown tile {name!r}")
    return img


OVERWORLD_TILES = ["deep", "water", "sand", "grass", "forest", "mountain",
                   "swamp", "path", "town", "castle", "cave"]
DUNGEON_TILES = ["wall", "floor", "door", "stairs_up", "stairs_down", "chest"]


# ------------------------------------------------------------------ noise

def value_noise(w: int, h: int, seed: int, scale: int = 8,
                octaves: int = 3) -> list[list[float]]:
    """Simple multi-octave value noise in [0, 1] (no numpy needed)."""
    rng = random.Random(seed)
    total = [[0.0] * w for _ in range(h)]
    amp_sum = 0.0
    for o in range(octaves):
        step = max(2, scale >> o)
        amp = 1.0 / (2 ** o)
        amp_sum += amp
        gw, gh = w // step + 2, h // step + 2
        lattice = [[rng.random() for _ in range(gw)] for _ in range(gh)]
        for y in range(h):
            gy, fy = divmod(y, step)
            ty = fy / step
            ty = ty * ty * (3 - 2 * ty)          # smoothstep
            for x in range(w):
                gx, fx = divmod(x, step)
                tx = fx / step
                tx = tx * tx * (3 - 2 * tx)
                a = lattice[gy][gx] * (1 - tx) + lattice[gy][gx + 1] * tx
                b = lattice[gy + 1][gx] * (1 - tx) + lattice[gy + 1][gx + 1] * tx
                total[y][x] += (a * (1 - ty) + b * ty) * amp
    return [[v / amp_sum for v in row] for row in total]


# --------------------------------------------------------------- overworld

def generate_overworld(width: int, height: int, seed: int) -> dict:
    elev = value_noise(width, height, seed * 7 + 1, scale=max(8, width // 6))
    moist = value_noise(width, height, seed * 13 + 5, scale=max(6, width // 8))
    rng = random.Random(f"features:{seed}")

    # Fade elevation at the borders so the world is an island chain.
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            ex = min(x, width - 1 - x) / (width * 0.5)
            ey = min(y, height - 1 - y) / (height * 0.5)
            edge = min(1.0, min(ex, ey) * 3.2)
            e = elev[y][x] * edge
            m = moist[y][x]
            if e < 0.28:
                t = "deep"
            elif e < 0.40:
                t = "water"
            elif e < 0.45:
                t = "sand"
            elif e > 0.72:
                t = "mountain"
            elif m > 0.70 and e < 0.55:
                t = "swamp"
            elif m > 0.55:
                t = "forest"
            else:
                t = "grass"
            row.append(t)
        grid.append(row)

    def land_cells(kind="grass"):
        return [(x, y) for y in range(height) for x in range(width)
                if grid[y][x] == kind]

    features = []
    grass = land_cells()
    rng.shuffle(grass)

    def place(kind, n, min_dist):
        placed = []
        for x, y in grass:
            if len(placed) >= n:
                break
            if grid[y][x] != "grass":            # already used by a feature
                continue
            if all(abs(x - f["x"]) + abs(y - f["y"]) >= min_dist
                   for f in features):
                grid[y][x] = kind
                placed.append((x, y))
                features.append({"type": kind, "x": x, "y": y})
        return placed

    castle = place("castle", 1, 0)
    towns = place("town", max(3, width // 12), max(6, width // 6))
    # Caves sit on grass next to mountains.
    cave_spots = [(x, y) for x, y in land_cells()
                  if any(0 <= x + dx < width and 0 <= y + dy < height
                         and grid[y + dy][x + dx] == "mountain"
                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    rng.shuffle(cave_spots)
    for x, y in cave_spots[:max(2, width // 16)]:
        grid[y][x] = "cave"
        features.append({"type": "cave", "x": x, "y": y})

    # L-shaped dirt paths from the castle to each town.
    if castle:
        cx, cy = castle[0]
        for tx, ty, *_ in towns:
            x, y = cx, cy
            while x != tx:
                x += 1 if tx > x else -1
                if grid[y][x] in ("grass", "forest", "swamp", "sand"):
                    grid[y][x] = "path"
            while y != ty:
                y += 1 if ty > y else -1
                if grid[y][x] in ("grass", "forest", "swamp", "sand"):
                    grid[y][x] = "path"

    return {"kind": "overworld", "seed": seed, "width": width,
            "height": height, "tiles": grid, "features": features}


# ----------------------------------------------------------------- dungeon

def generate_dungeon(width: int, height: int, seed: int) -> dict:
    rng = random.Random(f"dungeon:{seed}")
    grid = [["wall"] * width for _ in range(height)]
    rooms: list[tuple[int, int, int, int]] = []

    for _ in range(60):                          # try to place rooms
        if len(rooms) >= max(5, (width * height) // 90):
            break
        rw, rh = rng.randint(4, 8), rng.randint(3, 6)
        rx = rng.randint(1, width - rw - 2)
        ry = rng.randint(1, height - rh - 2)
        if any(rx < x + w + 1 and x < rx + rw + 1 and
               ry < y + h + 1 and y < ry + rh + 1 for x, y, w, h in rooms):
            continue
        rooms.append((rx, ry, rw, rh))
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = "floor"

    centers = [(x + w // 2, y + h // 2) for x, y, w, h in rooms]
    for (x0, y0), (x1, y1) in zip(centers, centers[1:]):   # L corridors
        x, y = x0, y0
        while x != x1:
            x += 1 if x1 > x else -1
            grid[y][x] = "floor"
        while y != y1:
            y += 1 if y1 > y else -1
            grid[y][x] = "floor"

    features = []
    if centers:
        sx, sy = centers[0]
        ex, ey = centers[-1]
        grid[sy][sx] = "stairs_up"
        grid[ey][ex] = "stairs_down"
        features += [{"type": "stairs_up", "x": sx, "y": sy},
                     {"type": "stairs_down", "x": ex, "y": ey}]
        for rx, ry, rw, rh in rng.sample(rooms, min(3, len(rooms))):
            cxx, cyy = rx + rng.randrange(rw), ry + rng.randrange(rh)
            if grid[cyy][cxx] == "floor":
                grid[cyy][cxx] = "chest"
                features.append({"type": "chest", "x": cxx, "y": cyy})

    return {"kind": "dungeon", "seed": seed, "width": width,
            "height": height, "tiles": grid, "features": features}


# ------------------------------------------------------------------ export

def render_map(data: dict) -> Image.Image:
    grid = data["tiles"]
    h, w = len(grid), len(grid[0])
    img = Image.new("RGBA", (w * TILE, h * TILE))
    cache: dict[tuple[str, int], Image.Image] = {}
    for y in range(h):
        for x in range(w):
            name = grid[y][x]
            variant = (x * 7 + y * 13) % 4       # texture variation
            key = (name, variant)
            if key not in cache:
                cache[key] = draw_tile(name, variant)
            img.paste(cache[key], (x * TILE, y * TILE))
    return img


def export_map(kind: str, width: int, height: int, seed: int,
               out_dir: str | Path) -> Path:
    if kind == "overworld":
        data = generate_overworld(width, height, seed)
        tiles = OVERWORLD_TILES
    elif kind == "dungeon":
        data = generate_dungeon(width, height, seed)
        tiles = DUNGEON_TILES
    else:
        raise ValueError("kind must be 'overworld' or 'dungeon'")

    root = Path(out_dir) / f"{kind}_{seed}"
    root.mkdir(parents=True, exist_ok=True)
    render_map(data).save(root / "map.png")
    (root / "map.json").write_text(json.dumps(data, indent=1))

    tileset = Image.new("RGBA", (len(tiles) * TILE, TILE))
    for i, t in enumerate(tiles):
        tileset.paste(draw_tile(t, 0), (i * TILE, 0))
    tileset.save(root / "tileset.png")
    return root
