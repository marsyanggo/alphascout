"""HD enhancement pipeline — pushes composed sprites toward an HD-2D look.

Stages (deterministic; mask/filter based so most work runs in C):
  1. scale2x (EPX) applied twice -> 4x size with rounded pixel staircases
  2. selective edge anti-aliasing -> smooth silhouettes, crisp interiors
  3. vertical light grading + top rim light -> richer shading
  4. vividness boost (saturation/contrast) -> HD-2D color pop
  5. thin dark outline for readability on any background
  6. soft drop shadow under the feet (HD-2D signature grounding)
"""

from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

SHADOW_ALPHA = 80
OUTLINE = (28, 24, 40)


def _scale2x(img: Image.Image) -> Image.Image:
    """Classic EPX/Scale2x: doubles size, rounding staircase edges."""
    w, h = img.size
    src = img.load()
    out = Image.new("RGBA", (w * 2, h * 2))
    dst = out.load()

    def at(x: int, y: int):
        if x < 0:
            x = 0
        elif x >= w:
            x = w - 1
        if y < 0:
            y = 0
        elif y >= h:
            y = h - 1
        return src[x, y]

    for y in range(h):
        for x in range(w):
            p = src[x, y]
            a, b = at(x, y - 1), at(x + 1, y)
            c, d = at(x - 1, y), at(x, y + 1)
            e0 = a if c == a and c != d and a != b else p
            e1 = b if a == b and a != c and b != d else p
            e2 = c if d == c and d != b and c != a else p
            e3 = d if b == d and b != a and d != c else p
            dst[2 * x, 2 * y] = e0
            dst[2 * x + 1, 2 * y] = e1
            dst[2 * x, 2 * y + 1] = e2
            dst[2 * x + 1, 2 * y + 1] = e3
    return out


def _edge_aa(img: Image.Image) -> Image.Image:
    """Anti-alias only near color/silhouette boundaries: blend a blurred
    copy through an edge mask so flat interior areas stay crisp."""
    alpha = img.getchannel("A")
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
    edges = ImageChops.add(
        edges, ImageChops.difference(alpha.filter(ImageFilter.MaxFilter(3)),
                                     alpha.filter(ImageFilter.MinFilter(3))))
    edges = edges.point(lambda v: 140 if v > 24 else 0)
    soft = img.filter(ImageFilter.GaussianBlur(1.0))
    out = Image.composite(Image.blend(img, soft, 0.65), img, edges)
    out.putalpha(alpha)  # silhouette stays pixel-exact
    return out


def _light_grade(img: Image.Image) -> Image.Image:
    """Vertical light ramp over the sprite + rim light along top edges."""
    bbox = img.getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    w, h = img.size
    alpha = img.getchannel("A")

    # Multiply ramp: 255 (top of sprite) -> 222 (feet).
    grad = Image.linear_gradient("L").resize((1, max(y1 - y0, 1)))
    grad = grad.point(lambda v: 255 - v * 33 // 255)
    ramp = Image.new("L", (w, h), 255)
    ramp.paste(grad.resize((x1 - x0, y1 - y0)), (x0, y0))
    rgb = ImageChops.multiply(img, Image.merge(
        "RGBA", (ramp, ramp, ramp, Image.new("L", (w, h), 255))))

    # Additive ramp for the upper body: +26 at the top -> 0.
    grad2 = Image.linear_gradient("L").resize((1, max(y1 - y0, 1)))
    grad2 = grad2.point(lambda v: max(0, 26 - v * 26 * 2 // 255))
    add = Image.new("L", (w, h), 0)
    add.paste(grad2.resize((x1 - x0, y1 - y0)), (x0, y0))
    rgb = ImageChops.add(rgb, Image.merge(
        "RGBA", (add, add, add, Image.new("L", (w, h), 0))))

    # Rim light: 2px band where the pixel above is transparent.
    rim = ImageChops.subtract(alpha, ImageChops.offset(alpha, 0, 2))
    rim = rim.point(lambda v: 70 if v > 80 else 0)
    rgb = ImageChops.add(rgb, Image.merge(
        "RGBA", (rim, rim, rim, Image.new("L", (w, h), 0))))

    rgb.putalpha(alpha)
    return rgb


def _vivid(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    out = ImageEnhance.Color(img).enhance(1.14)
    out = ImageEnhance.Contrast(out).enhance(1.05)
    out.putalpha(alpha)
    return out


def _outline(img: Image.Image) -> Image.Image:
    alpha = img.getchannel("A")
    solid = alpha.point(lambda v: 255 if v > 60 else 0)
    ring = ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(3)), solid)
    out = img.copy()
    out.paste(OUTLINE, (0, 0), ring)
    new_alpha = ImageChops.lighter(alpha, ring)
    out.putalpha(new_alpha)
    return out


def _drop_shadow(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    x0, _, x1, y1 = bbox
    w, h = img.size
    cx = (x0 + x1) // 2
    sw = max(8, int((x1 - x0) * 0.42))
    sh = max(3, sw // 4)
    sy = min(h - sh * 2 - 1, y1 - sh)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(shadow)
    d.ellipse((cx - sw, sy, cx + sw, sy + sh * 2),
              fill=(10, 8, 20, SHADOW_ALPHA))
    shadow = shadow.filter(ImageFilter.GaussianBlur(w / 96))
    shadow.alpha_composite(img)
    return shadow


def enhance(frame: Image.Image, shadow: bool = True) -> Image.Image:
    """Full pipeline: NxN frame in -> 4Nx4N HD-2D style frame out."""
    img = _scale2x(_scale2x(frame))
    img = _edge_aa(img)
    img = _light_grade(img)
    img = _vivid(img)
    img = _outline(img)
    if shadow:
        img = _drop_shadow(img)
    return img
