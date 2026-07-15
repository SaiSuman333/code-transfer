# src/uimon/differ_image.py
from PIL import Image, ImageChops, ImageStat, ImageEnhance
from pathlib import Path

def image_diff_and_score(base_path: Path, new_path: Path, out_path: Path):
    base = Image.open(base_path).convert("RGB")
    new = Image.open(new_path).convert("RGB")
    if base.size != new.size:
        new = new.resize(base.size)

    diff = ImageChops.difference(base, new)
    stat = ImageStat.Stat(diff)
    # Normalize RMS per channel (0 identical → ~higher = more change)
    distance = sum((s/255.0) for s in stat.rms) / len(stat.rms)

    highlight = ImageEnhance.Brightness(diff).enhance(2.5)
    highlight.save(out_path)
    return {"distance": float(distance), "diff_saved": str(out_path)}
