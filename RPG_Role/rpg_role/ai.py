"""AI image generation backend for battle art and portraits.

AI generation is great for one-off illustrations (DQ-style battle monster
art, character portraits) but bad at frame-consistent animation — so this
complements the LPC/HD sprite pipeline instead of replacing it.

Providers (picked automatically by available credentials/network):
  openai      — gpt-image-1, needs OPENAI_API_KEY
  stability   — Stable Image Core, needs STABILITY_API_KEY
  pollinations — free, no key (needs network access to image.pollinations.ai)

Post-processing turns raw AI output into game-ready assets: background
removal (corner flood fill), optional pixelation to a retro grid with
palette quantization, and the HD outline/drop-shadow treatment so AI art
sits next to the sprite pipeline output without clashing.
"""

from __future__ import annotations

import base64
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

UA = {"User-Agent": "rpg-role/0.1 (sprite generator)"}

PROMPTS = {
    "monster": (
        "Classic JRPG monster illustration in the style of a retro Dragon "
        "Quest enemy: {subject}. Akira-Toriyama-inspired character design, "
        "bold clean outlines, cel shading, vibrant saturated colors, "
        "full body, facing the viewer, centered composition, "
        "plain solid white background, no text, no watermark"),
    "portrait": (
        "JRPG character portrait, bust shot: {subject}. Retro 90s anime "
        "style, bold clean outlines, cel shading, vibrant colors, "
        "centered, plain solid white background, no text, no watermark"),
    "item": (
        "Single RPG item icon illustration: {subject}. Bold clean outlines, "
        "cel shading, slight 3/4 view, centered on a plain solid white "
        "background, no text, no watermark"),
    "scene": (
        "Retro JRPG concept art: {subject}. HD-2D style, painterly pixel "
        "art aesthetic, dramatic lighting, vibrant colors, no text"),
}


class ProviderError(RuntimeError):
    pass


# ------------------------------------------------------------- providers

def _gen_openai(prompt: str, size: int, seed: int) -> bytes:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ProviderError("OPENAI_API_KEY not set")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1024x1024",
            "n": 1,
        }).encode(),
        headers={**UA, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    return base64.b64decode(data["data"][0]["b64_json"])


def _gen_stability(prompt: str, size: int, seed: int) -> bytes:
    key = os.environ.get("STABILITY_API_KEY")
    if not key:
        raise ProviderError("STABILITY_API_KEY not set")
    boundary = "----rpgrole"
    parts = []
    for name, value in (("prompt", prompt), ("output_format", "png"),
                        ("seed", str(seed % 4294967294))):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                     f"name=\"{name}\"\r\n\r\n{value}\r\n")
    body = ("".join(parts) + f"--{boundary}--\r\n").encode()
    req = urllib.request.Request(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        data=body,
        headers={**UA, "Authorization": f"Bearer {key}",
                 "Accept": "image/*",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def _gen_pollinations(prompt: str, size: int, seed: int) -> bytes:
    url = ("https://image.pollinations.ai/prompt/"
           + urllib.parse.quote(prompt)
           + f"?width={size}&height={size}&seed={seed}&nologo=true")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


PROVIDERS = {
    "openai": _gen_openai,
    "stability": _gen_stability,
    "pollinations": _gen_pollinations,
}


def pick_provider() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("STABILITY_API_KEY"):
        return "stability"
    return "pollinations"


def generate_raw(prompt: str, size: int = 1024, seed: int = 0,
                 provider: str = "auto") -> Image.Image:
    name = pick_provider() if provider == "auto" else provider
    if name not in PROVIDERS:
        raise ValueError(f"unknown provider {name!r}")
    try:
        png = PROVIDERS[name](prompt, size, seed)
    except urllib.error.HTTPError as e:
        raise ProviderError(
            f"{name} returned HTTP {e.code} — check the API key and that "
            f"this environment's network policy allows the host") from e
    except urllib.error.URLError as e:
        raise ProviderError(f"{name} unreachable: {e.reason}") from e
    return Image.open(io.BytesIO(png)).convert("RGBA")


# -------------------------------------------------------- post-processing

def remove_background(img: Image.Image, tolerance: int = 28) -> Image.Image:
    """Flood-fill transparency in from the corners (white-ish backdrop)."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
             (w // 2, 0), (0, h // 2), (w - 1, h // 2), (w // 2, h - 1)]
    refs = [px[x, y][:3] for x, y in seeds]

    def is_bg(c) -> bool:
        return any(sum(abs(a - b) for a, b in zip(c[:3], ref)) < tolerance * 3
                   for ref in refs)

    seen = bytearray(w * h)
    todo = [s for s in seeds if is_bg(px[s[0], s[1]])]
    for x, y in todo:
        seen[y * w + x] = 1
    while todo:
        x, y = todo.pop()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                if is_bg(px[nx, ny]):
                    seen[ny * w + nx] = 1
                    todo.append((nx, ny))
    return img


def pixelate(img: Image.Image, grid: int = 96, colors: int = 48) -> Image.Image:
    """Downscale to a retro pixel grid and quantize the palette."""
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    scale = grid / max(img.size)
    small = img.resize((max(1, round(img.width * scale)),
                        max(1, round(img.height * scale))), Image.LANCZOS)
    alpha = small.getchannel("A").point(lambda v: 255 if v > 96 else 0)
    quant = small.convert("RGB").quantize(colors=colors,
                                          method=Image.MEDIANCUT)
    out = quant.convert("RGBA")
    out.putalpha(alpha)
    return out


def stylize(img: Image.Image, pixel_grid: int | None = 96,
            shadow: bool = True) -> Image.Image:
    """Full post pipeline: bg removal -> optional pixelation -> HD finish."""
    from .hd import _drop_shadow, _outline, _scale2x

    img = remove_background(img)
    if pixel_grid:
        img = pixelate(img, grid=pixel_grid)
        img = _scale2x(_scale2x(img))
    img = _outline(img)
    if shadow:
        canvas = Image.new("RGBA",
                           (img.width + 16, img.height + 16), (0, 0, 0, 0))
        canvas.alpha_composite(img, (8, 4))
        img = _drop_shadow(canvas)
    return img


def export_ai_art(subject: str, kind: str, out_dir: str | Path,
                  seed: int = 0, provider: str = "auto",
                  pixel_grid: int | None = 96) -> Path:
    if kind not in PROMPTS:
        raise ValueError(f"kind must be one of {sorted(PROMPTS)}")
    prompt = PROMPTS[kind].format(subject=subject)
    raw = generate_raw(prompt, seed=seed, provider=provider)

    slug = "".join(ch if ch.isalnum() else "_" for ch in subject.lower())[:40]
    root = Path(out_dir) / "ai" / f"{kind}_{slug}_{seed}"
    root.mkdir(parents=True, exist_ok=True)
    raw.save(root / "raw.png")
    if kind == "scene":
        styled = raw  # scenes keep their full backdrop
    else:
        styled = stylize(raw, pixel_grid=pixel_grid)
    styled.save(root / "art.png")
    (root / "meta.json").write_text(json.dumps(
        {"subject": subject, "kind": kind, "seed": seed,
         "prompt": prompt, "provider": (pick_provider() if provider == "auto"
                                        else provider)}, indent=2))
    return root
