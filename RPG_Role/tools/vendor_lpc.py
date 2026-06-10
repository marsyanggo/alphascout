"""Vendor the LPC assets used by rpg_role into assets/lpc/.

Usage:
    git clone --depth 1 --filter=blob:none --sparse \
        https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator /tmp/lpc
    (cd /tmp/lpc && git sparse-checkout set spritesheets sheet_definitions)
    python3 tools/vendor_lpc.py /tmp/lpc

Copies only the files referenced by rpg_role/lpc_manifest.py and writes an
ATTRIBUTION.md from the upstream sheet_definitions credits.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rpg_role.lpc_manifest import all_asset_paths

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "lpc"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    sheets = src / "spritesheets"
    missing = []
    for rel in sorted(all_asset_paths()):
        s = sheets / rel
        if not s.exists():
            missing.append(rel)
            continue
        d = DEST / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    if missing:
        sys.exit("missing upstream files:\n  " + "\n  ".join(missing))

    write_attribution(src)
    n = len(list(DEST.rglob("*.png")))
    print(f"vendored {n} sheets into {DEST}")


def write_attribution(src: Path) -> None:
    """Collect upstream credits for every vendored asset."""
    defs = src / "sheet_definitions"
    vendored = all_asset_paths()
    entries: dict[str, dict] = {}
    for jf in defs.glob("*.json"):
        try:
            data = json.loads(jf.read_text())
        except json.JSONDecodeError:
            continue
        for credit in data.get("credits", []):
            file = credit.get("file", "")
            if any(v.startswith(file) for v in vendored):
                entries[file] = credit

    lines = [
        "# Attribution\n",
        "Pixel art in this directory comes from the Universal LPC Spritesheet",
        "collection (https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator),",
        "licensed under CC-BY-SA 3.0 and/or GPL 3.0 (per-file licenses below).",
        "If you distribute a game using these sprites you must credit the",
        "authors below and license the derived art under the same terms.\n",
    ]
    for file in sorted(entries):
        c = entries[file]
        lines.append(f"## {file}")
        lines.append(f"- Authors: {', '.join(c.get('authors', []))}")
        lines.append(f"- Licenses: {', '.join(c.get('licenses', []))}")
        for url in c.get("urls", []):
            lines.append(f"- {url}")
        lines.append("")
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "ATTRIBUTION.md").write_text("\n".join(lines))
    print(f"wrote {DEST / 'ATTRIBUTION.md'} ({len(entries)} credited sources)")


if __name__ == "__main__":
    main()
