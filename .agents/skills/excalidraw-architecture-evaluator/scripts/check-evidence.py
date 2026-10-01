"""Check extracted data and tile coverage/pixels: python check-evidence.py OUTPUT_DIR.

Requires Pillow for image inspection; does not render or evaluate the architecture.
"""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageChops

out = Path(sys.argv[1])
manifest = json.loads((out / "render-manifest.json").read_text(encoding="utf-8"))
evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
raw = Path(manifest["source"]).read_bytes()
scene = json.loads(raw.decode("utf-8-sig"))
assert manifest["status"] == "complete"
assert manifest["sha256"] == evidence["sha256"] == hashlib.sha256(raw).hexdigest()
assert evidence["elements"] == [e for e in scene["elements"] if not e.get("isDeleted")]
width, height = manifest["dimensions"]["width"], manifest["dimensions"]["height"]
tiles = manifest["tiles"]
overview = Image.open(out / "overview.png").convert("RGBA")
for tile in tiles:
    image = Image.open(out / tile["file"]).convert("RGBA")
    assert image.size == (tile["width"], tile["height"])
    if manifest["overviewScale"] == 1:
        x, y = tile["x"], tile["y"]
        expected = overview.crop((x, y, x + tile["width"], y + tile["height"]))
        assert ImageChops.difference(image, expected).getbbox(alpha_only=False) is None, tile["file"]
# Check every horizontal band where tile coverage can change, including scene edges.
ys = sorted({0, height, *(t["y"] for t in tiles), *(t["y"] + t["height"] for t in tiles)})
for y in ys[:-1]:
    covered = 0
    for lo, hi in sorted((t["x"], t["x"] + t["width"]) for t in tiles if t["y"] <= y < t["y"] + t["height"]):
        assert lo <= covered, (lo, covered, y)
        covered = max(covered, hi)
    assert covered >= width, (covered, width, y)
print(f"Verified source hash, active elements, {len(tiles)} tiles, coverage, and full-scale crop pixels.")
