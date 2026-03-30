#!/usr/bin/env python3
"""Stage 4b: Export approved images to public/images/ with attributions."""

import csv
import json
import re
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PUBLIC_IMAGES = Path(__file__).parent.parent.parent / "public" / "images"


def get_next_number(prefix, images_dir):
    """Find the next available number for a given prefix (e.g., mmvt-029)."""
    existing = sorted(images_dir.glob(f"{prefix}-*"))
    if not existing:
        return 1

    max_num = 0
    for f in existing:
        match = re.match(rf"{prefix}-(\d+)", f.stem)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return max_num + 1


def main():
    selections_path = DATA_DIR / "selections.json"
    if not selections_path.exists():
        print("Error: selections.json not found.")
        print("Open gallery.html, approve images, and click 'Export selections.json'.")
        print(f"Then move the downloaded file to: {selections_path}")
        return

    with open(selections_path) as f:
        selections = json.load(f)

    metadata_path = DATA_DIR / "filtered" / "metadata.csv"
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path) as f:
            for row in csv.DictReader(f):
                metadata[row["filename"]] = row

    approved = {fn: sel for fn, sel in selections.items() if sel.get("status") == "approved"}

    if not approved:
        print("No approved images found in selections.json.")
        return

    print(f"Exporting {len(approved)} approved images...")

    counters = {}
    attributions = []

    for filename, sel in sorted(approved.items()):
        category = sel.get("category") or metadata.get(filename, {}).get("category", "mmvt")
        meta = metadata.get(filename, {})

        if category not in counters:
            counters[category] = get_next_number(category, PUBLIC_IMAGES)

        num = counters[category]
        counters[category] += 1

        source = DATA_DIR / "filtered" / meta.get("category", category) / filename
        if not source.exists():
            print(f"  Warning: {source} not found, skipping")
            continue

        ext = source.suffix.lower()
        if ext in (".tif", ".tiff", ".bmp"):
            ext = ".png"

        dest_name = f"{category}-{num:03d}{ext}"
        dest_path = PUBLIC_IMAGES / dest_name

        shutil.copy2(source, dest_path)
        print(f"  {dest_name} <- {filename}")

        attributions.append(
            f"{dest_name}: {meta.get('article_title', 'Unknown')}. "
            f"{meta.get('pmcid', '')}. "
            f"License: {meta.get('license', 'unknown')}."
        )

    attr_path = PUBLIC_IMAGES.parent / "ATTRIBUTIONS.md"
    mode = "a" if attr_path.exists() else "w"
    with open(attr_path, mode) as f:
        if mode == "w":
            f.write("# Image Attributions\n\n")
            f.write("Images sourced from PubMed Central Open Access Subset.\n\n")
        f.write(f"\n## Batch exported {len(attributions)} images\n\n")
        for line in attributions:
            f.write(f"- {line}\n")

    print(f"\nExported {len(attributions)} images to {PUBLIC_IMAGES}")
    print(f"Attributions written to {attr_path}")

    for cat in sorted(counters):
        count = sum(1 for fn, s in approved.items()
                    if (s.get("category") or metadata.get(fn, {}).get("category")) == cat)
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
