"""32x32 pixel canvas with automatic shading and outlining.

Body parts are drawn as flat base colors; `finish()` then applies a simple
top-light/bottom-shadow pass and a 1px dark outline around the silhouette,
which is what gives the sprites their retro look without hand-shading.
"""

from __future__ import annotations

from PIL import Image

from . import FRAME
from .palettes import OUTLINE, shift


class Canvas:
    def __init__(self) -> None:
        self.img = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
        self.px = self.img.load()

    def put(self, x: int, y: int, color) -> None:
        if 0 <= x < FRAME and 0 <= y < FRAME:
            self.px[x, y] = (*color, 255)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color) -> None:
        """Filled rectangle, inclusive coordinates."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color) -> None:
        """Bresenham line — used for weapon shafts at arbitrary angles."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.put(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def finish(self) -> Image.Image:
        """Apply shading + outline and return the composed frame."""
        src = self.img
        spx = src.load()
        out = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
        opx = out.load()

        def opaque(x: int, y: int) -> bool:
            return 0 <= x < FRAME and 0 <= y < FRAME and spx[x, y][3] > 0

        for y in range(FRAME):
            for x in range(FRAME):
                if opaque(x, y):
                    r, g, b, a = spx[x, y]
                    if not opaque(x, y - 1):
                        r, g, b = shift((r, g, b), 35)
                    elif not opaque(x, y + 1) or not opaque(x + 1, y):
                        r, g, b = shift((r, g, b), -30)
                    opx[x, y] = (r, g, b, a)
                else:
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if opaque(nx, ny):
                            opx[x, y] = (*OUTLINE, 255)
                            break
        return out
