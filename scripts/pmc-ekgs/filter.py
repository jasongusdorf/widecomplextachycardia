#!/usr/bin/env python3
"""Stage 3: Filter extracted images by caption keywords to find EKGs."""

import csv
import json
import re
import shutil
from pathlib import Path

from lxml import etree

DATA_DIR = Path(__file__).parent / "data"

INCLUDE_KEYWORDS = [
    "electrocardiogram", "electrocardiograph", "electrocardiographic",
    "ecg", "ekg", "12-lead", "twelve-lead", "twelve lead",
    "tachycardia", "rhythm strip",
]

EXCLUDE_KEYWORDS = [
    "echocardiogram", "echocardiography", "angiogram", "angiography",
    "ct scan", "computed tomography", "mri", "magnetic resonance",
    "x-ray", "xray", "x ray", "radiograph", "ultrasound",
    "histology", "histological", "pathology", "pathological",
    "catheterization", "catheter", "coronary artery",
    "doppler", "photograph", "gross specimen", "microscopy",
    "immunostaining", "immunohistochemistry", "biopsy",
    "chest radiograph", "fluoroscopy",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".bmp"}


def caption_matches(caption):
    """Return True if caption suggests an EKG image."""
    lower = caption.lower()
    has_include = any(kw in lower for kw in INCLUDE_KEYWORDS)
    has_exclude = any(kw in lower for kw in EXCLUDE_KEYWORDS)
    return has_include and not has_exclude


def find_xml(pmcid_dir):
    """Find the JATS XML file in the extracted directory."""
    for xml_path in pmcid_dir.rglob("*.nxml"):
        return xml_path
    for xml_path in pmcid_dir.rglob("*.xml"):
        if xml_path.name != "tagmanifest.xml" and "META-INF" not in str(xml_path):
            return xml_path
    return None


def extract_figures(xml_path):
    """Parse JATS XML and return list of (graphic_filename, caption_text)."""
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError:
        return []

    figures = []
    for fig in tree.iter("fig"):
        caption_el = fig.find(".//caption")
        if caption_el is None:
            continue
        caption = etree.tostring(caption_el, method="text", encoding="unicode").strip()
        caption = re.sub(r"\s+", " ", caption)

        for graphic in fig.iter("graphic"):
            href = graphic.get("{http://www.w3.org/1999/xlink}href", "")
            if href:
                figures.append((href, caption))

    return figures


def find_image_file(pmcid_dir, href):
    """Find the actual image file matching the graphic href."""
    base = Path(href).stem if "/" in href else href

    for img in pmcid_dir.rglob("*"):
        if img.suffix.lower() in IMAGE_EXTENSIONS:
            if img.stem == base or img.stem == Path(href).name:
                return img
            if base in img.stem:
                return img

    return None


def main():
    manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        print("Error: manifest.json not found. Run search.py first.")
        return

    with open(manifest_path) as f:
        manifest = json.load(f)

    manifest_map = {m["pmcid"]: m for m in manifest}
    extracted_dir = DATA_DIR / "extracted"
    filtered_dir = DATA_DIR / "filtered"

    for cat in ["mmvt", "pmvt", "notvt"]:
        (filtered_dir / cat).mkdir(parents=True, exist_ok=True)

    metadata_rows = []
    total_checked = 0
    total_matched = 0

    for pmcid_dir in sorted(extracted_dir.iterdir()):
        if not pmcid_dir.is_dir():
            continue

        pmcid = pmcid_dir.name
        entry = manifest_map.get(pmcid, {})
        category = entry.get("category", "mmvt")
        license_text = entry.get("license", "unknown")

        xml_path = find_xml(pmcid_dir)
        if not xml_path:
            continue

        figures = extract_figures(xml_path)
        total_checked += 1

        for href, caption in figures:
            if not caption_matches(caption):
                continue

            img_file = find_image_file(pmcid_dir, href)
            if not img_file:
                continue

            fig_id = Path(href).stem.split(".")[-1] if "." in href else Path(href).stem
            ext = img_file.suffix.lower()
            dest_name = f"{pmcid}_{fig_id}{ext}"
            dest_path = filtered_dir / category / dest_name

            shutil.copy2(img_file, dest_path)
            total_matched += 1

            metadata_rows.append({
                "id": dest_name,
                "filename": dest_name,
                "category": category,
                "pmcid": pmcid,
                "caption": caption[:500],
                "license": license_text,
                "article_title": entry.get("title", ""),
                "doi": entry.get("doi", ""),
                "imageUrl": f"{category}/{dest_name}",
                "thumbUrl": f"{category}/{dest_name}",
            })

    csv_path = filtered_dir / "metadata.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "filename", "category", "pmcid", "caption",
            "license", "article_title", "doi", "imageUrl", "thumbUrl",
        ])
        writer.writeheader()
        writer.writerows(metadata_rows)

    js_path = filtered_dir / "gallery-data.js"
    with open(js_path, "w") as f:
        f.write("const GALLERY_DATA = ")
        json.dump(metadata_rows, f, indent=2)
        f.write(";\n")

    print(f"Checked {total_checked} articles, found {total_matched} EKG images")
    for cat in ["mmvt", "pmvt", "notvt"]:
        count = sum(1 for r in metadata_rows if r["category"] == cat)
        print(f"  {cat}: {count}")
    print(f"\nMetadata: {csv_path}")
    print(f"Gallery data: {js_path}")


if __name__ == "__main__":
    main()
