#!/usr/bin/env python3
"""Stage 2: Download and extract OA packages from PMC."""

import argparse
import json
import os
import tarfile
import time
from pathlib import Path

import requests
from lxml import etree

OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
DATA_DIR = Path(__file__).parent / "data"


def get_package_url(pmcid):
    """Query OA Web Service for the .tar.gz download link and license."""
    params = {"id": pmcid, "format": "tgz"}
    resp = requests.get(OA_URL, params=params, timeout=30)
    resp.raise_for_status()

    root = etree.fromstring(resp.content)
    error = root.find(".//error")
    if error is not None:
        return None, None

    link = root.find(".//link[@format='tgz']")
    if link is None:
        return None, None

    href = link.get("href", "")
    if href.startswith("ftp://"):
        href = href.replace("ftp://ftp.ncbi.nlm.nih.gov/",
                            "https://ftp.ncbi.nlm.nih.gov/")

    license_node = root.find(".//record")
    license_text = license_node.get("license", "unknown") if license_node is not None else "unknown"

    return href, license_text


def download_and_extract(url, pmcid, extract_dir):
    """Download .tar.gz and extract to extract_dir/PMCID/."""
    dest = extract_dir / pmcid
    if dest.exists() and any(dest.iterdir()):
        return True

    resp = requests.get(url, timeout=120, stream=True)
    resp.raise_for_status()

    tgz_path = extract_dir / f"{pmcid}.tar.gz"
    tgz_path.parent.mkdir(parents=True, exist_ok=True)

    with open(tgz_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    dest.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(tgz_path, "r:gz") as tar:
            tar.extractall(path=dest, filter="data")
    except (tarfile.TarError, EOFError) as e:
        print(f"  Error extracting {pmcid}: {e}")
        return False
    finally:
        tgz_path.unlink(missing_ok=True)

    return True


def main():
    parser = argparse.ArgumentParser(description="Download OA packages from PMC")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max articles to download (0 = all)")
    parser.add_argument("--category", default=None,
                        help="Only download articles from this category")
    args = parser.parse_args()

    manifest_path = DATA_DIR / "manifest.json"
    if not manifest_path.exists():
        print("Error: manifest.json not found. Run search.py first.")
        return

    with open(manifest_path) as f:
        manifest = json.load(f)

    if args.category:
        manifest = [m for m in manifest if m["category"] == args.category]

    extract_dir = DATA_DIR / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    for i, entry in enumerate(manifest):
        if args.limit and downloaded >= args.limit:
            break

        pmcid = entry["pmcid"]
        dest = extract_dir / pmcid

        if dest.exists() and any(dest.iterdir()):
            skipped += 1
            continue

        print(f"[{i+1}/{len(manifest)}] {pmcid}: {entry.get('title', '')[:60]}...")

        url, license_text = get_package_url(pmcid)
        if not url:
            print(f"  No OA package available, skipping")
            entry["license"] = "unavailable"
            failed += 1
            time.sleep(0.35)
            continue

        entry["license"] = license_text

        success = download_and_extract(url, pmcid, extract_dir)
        if success:
            downloaded += 1
        else:
            failed += 1

        time.sleep(0.35)

    all_manifest_path = DATA_DIR / "manifest.json"
    with open(all_manifest_path) as f:
        full_manifest = json.load(f)

    license_map = {e["pmcid"]: e.get("license", "") for e in manifest}
    for entry in full_manifest:
        if entry["pmcid"] in license_map:
            entry["license"] = license_map[entry["pmcid"]]

    with open(all_manifest_path, "w") as f:
        json.dump(full_manifest, f, indent=2)

    print(f"\nDone. Downloaded: {downloaded}, Skipped (already had): {skipped}, Failed: {failed}")


if __name__ == "__main__":
    main()
