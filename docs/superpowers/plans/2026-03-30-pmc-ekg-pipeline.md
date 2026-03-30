# PMC EKG Image Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI pipeline that searches PubMed Central for open-access case reports, downloads figure images, filters for 12-lead EKGs, and provides a curation UI for selecting images to add to the widecomplextachycardia.com drill.

**Architecture:** Four-stage pipeline (search, download, filter, export) at `scripts/pmc-ekgs/`. Each stage reads from the previous stage's output files, making the pipeline resumable. A static HTML gallery serves as the curation UI.

**Tech Stack:** Python 3 (requests, lxml), HTML/JS (curation gallery)

---

### Task 1: Project scaffolding and requirements

**Files:**
- Create: `scripts/pmc-ekgs/requirements.txt`
- Create: `scripts/pmc-ekgs/data/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Create the scripts directory structure**

```bash
mkdir -p "scripts/pmc-ekgs/data"
```

- [ ] **Step 2: Create requirements.txt**

Create `scripts/pmc-ekgs/requirements.txt`:
```
requests>=2.31
lxml>=5.0
```

- [ ] **Step 3: Create .gitkeep for data directory**

Create an empty file at `scripts/pmc-ekgs/data/.gitkeep` so git tracks the directory.

- [ ] **Step 4: Add data directory to .gitignore**

Append to `.gitignore`:
```
scripts/pmc-ekgs/data/*
!scripts/pmc-ekgs/data/.gitkeep
```

- [ ] **Step 5: Install dependencies**

```bash
cd scripts/pmc-ekgs && pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add scripts/pmc-ekgs/requirements.txt scripts/pmc-ekgs/data/.gitkeep .gitignore
git commit -m "feat: scaffold PMC EKG pipeline project"
```

---

### Task 2: Search script (search.py)

**Files:**
- Create: `scripts/pmc-ekgs/search.py`

- [ ] **Step 1: Create search.py with argument parsing and query definitions**

Create `scripts/pmc-ekgs/search.py`:

```python
#!/usr/bin/env python3
"""Stage 1: Search PMC for open-access case reports with EKG images."""

import argparse
import json
import os
import time
from pathlib import Path

import requests

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
DATA_DIR = Path(__file__).parent / "data"

QUERIES = {
    "mmvt": (
        '("monomorphic ventricular tachycardia"'
        ' OR ("ventricular tachycardia" NOT "polymorphic" NOT "torsades"))'
        ' AND ("12-lead" OR "electrocardiogram" OR "ECG")'
        ' AND "case report"'
        " AND open access[filter]"
    ),
    "pmvt": (
        '("polymorphic ventricular tachycardia"'
        ' OR "torsades de pointes" OR "torsade de pointes")'
        ' AND ("12-lead" OR "electrocardiogram" OR "ECG")'
        ' AND "case report"'
        " AND open access[filter]"
    ),
    "notvt": (
        '("SVT with aberrancy"'
        ' OR ("supraventricular tachycardia" AND "wide complex")'
        ' OR "wide complex tachycardia" OR "antidromic"'
        ' OR "pre-excited atrial fibrillation")'
        ' AND ("12-lead" OR "electrocardiogram" OR "ECG")'
        ' AND "case report"'
        " AND open access[filter]"
    ),
}


def search_pmc(query, api_key=None, batch_size=500):
    """Search PMC and return all matching PMCIDs."""
    pmcids = []
    retstart = 0
    params = {
        "db": "pmc",
        "term": query,
        "retmode": "json",
        "retmax": batch_size,
    }
    if api_key:
        params["api_key"] = api_key

    delay = 0.1 if api_key else 0.34

    while True:
        params["retstart"] = retstart
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        result = data.get("esearchresult", {})
        ids = result.get("idlist", [])
        total = int(result.get("count", 0))

        pmcids.extend(ids)
        print(f"  Fetched {len(pmcids)}/{total} IDs...")

        if len(pmcids) >= total or not ids:
            break

        retstart += batch_size
        time.sleep(delay)

    return pmcids


def fetch_summaries(pmcids, api_key=None, batch_size=200):
    """Fetch article titles for a list of PMCIDs."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    titles = {}
    delay = 0.1 if api_key else 0.34

    for i in range(0, len(pmcids), batch_size):
        batch = pmcids[i : i + batch_size]
        params = {
            "db": "pmc",
            "id": ",".join(batch),
            "retmode": "json",
        }
        if api_key:
            params["api_key"] = api_key

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        for uid, info in data.get("result", {}).items():
            if uid == "uids":
                continue
            titles[uid] = info.get("title", "")

        print(f"  Fetched summaries {min(i + batch_size, len(pmcids))}/{len(pmcids)}...")
        time.sleep(delay)

    return titles


def main():
    parser = argparse.ArgumentParser(description="Search PMC for EKG case reports")
    parser.add_argument("--api-key", default=os.environ.get("NCBI_API_KEY"),
                        help="NCBI API key (or set NCBI_API_KEY env var)")
    parser.add_argument("--categories", nargs="+", default=list(QUERIES.keys()),
                        choices=list(QUERIES.keys()),
                        help="Which categories to search (default: all)")
    args = parser.parse_args()

    seen = set()
    manifest = []

    for category in args.categories:
        query = QUERIES[category]
        print(f"\nSearching [{category}]...")
        pmcids = search_pmc(query, api_key=args.api_key)
        new_ids = [pid for pid in pmcids if pid not in seen]
        seen.update(new_ids)
        print(f"  Found {len(pmcids)} results, {len(new_ids)} new (after dedup)")

        if new_ids:
            print(f"  Fetching titles...")
            titles = fetch_summaries(new_ids, api_key=args.api_key)

            for pid in new_ids:
                manifest.append({
                    "pmcid": f"PMC{pid}",
                    "uid": pid,
                    "title": titles.get(pid, ""),
                    "category": category,
                })

    out_path = DATA_DIR / "manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to {out_path}")
    print(f"Total articles: {len(manifest)}")
    for cat in args.categories:
        count = sum(1 for m in manifest if m["category"] == cat)
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test search with a small query**

```bash
cd scripts/pmc-ekgs && python search.py --categories mmvt
```

Expected: prints progress, writes `data/manifest.json` with MMVT results. Check the file has entries with pmcid, title, category fields.

- [ ] **Step 3: Run full search across all categories**

```bash
cd scripts/pmc-ekgs && python search.py
```

Expected: searches all three categories, deduplicates across them, writes complete manifest. Should find 500+ articles total.

- [ ] **Step 4: Commit**

```bash
git add scripts/pmc-ekgs/search.py
git commit -m "feat: add PMC search script (stage 1)"
```

---

### Task 3: Download script (download.py)

**Files:**
- Create: `scripts/pmc-ekgs/download.py`

- [ ] **Step 1: Create download.py**

Create `scripts/pmc-ekgs/download.py`:

```python
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
    # Convert FTP URLs to HTTPS
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
        return True  # Already downloaded

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

    # Update manifest with license info
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
```

- [ ] **Step 2: Test with a small batch**

```bash
cd scripts/pmc-ekgs && python download.py --limit 5
```

Expected: downloads and extracts 5 article packages into `data/extracted/PMC*/`. Each directory contains XML, images, and possibly PDF files. Manifest updated with license info.

- [ ] **Step 3: Verify extracted contents**

```bash
ls data/extracted/ | head -5
ls data/extracted/PMC*/  # Check one has .nxml and image files
```

Expected: directories named by PMCID, each containing article files.

- [ ] **Step 4: Commit**

```bash
git add scripts/pmc-ekgs/download.py
git commit -m "feat: add PMC download script (stage 2)"
```

---

### Task 4: Filter script (filter.py)

**Files:**
- Create: `scripts/pmc-ekgs/filter.py`

- [ ] **Step 1: Create filter.py**

Create `scripts/pmc-ekgs/filter.py`:

```python
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
                "filename": dest_name,
                "category": category,
                "pmcid": pmcid,
                "caption": caption[:500],
                "license": license_text,
                "article_title": entry.get("title", ""),
                "doi": entry.get("doi", ""),
            })

    # Write metadata CSV
    csv_path = filtered_dir / "metadata.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "category", "pmcid", "caption",
            "license", "article_title", "doi",
        ])
        writer.writeheader()
        writer.writerows(metadata_rows)

    # Write gallery-data.js for the curation gallery
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
```

- [ ] **Step 2: Test filter on downloaded articles**

```bash
cd scripts/pmc-ekgs && python filter.py
```

Expected: prints count of checked articles and matched EKG images. Creates `data/filtered/mmvt/`, `data/filtered/pmvt/`, `data/filtered/notvt/` with image files, plus `metadata.csv` and `gallery-data.js`.

- [ ] **Step 3: Spot-check results**

```bash
ls data/filtered/mmvt/ | head -5
open data/filtered/mmvt/$(ls data/filtered/mmvt/ | head -1)  # View one image on Mac
```

Expected: images are actual EKG figures, not echocardiograms or CT scans.

- [ ] **Step 4: Commit**

```bash
git add scripts/pmc-ekgs/filter.py
git commit -m "feat: add caption-based EKG filter (stage 3)"
```

---

### Task 5: Curation gallery (gallery.html)

**Files:**
- Create: `scripts/pmc-ekgs/gallery.html`

- [ ] **Step 1: Create gallery.html**

Create `scripts/pmc-ekgs/gallery.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EKG Image Curation</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f5; padding: 20px; }
    h1 { margin-bottom: 8px; }
    .stats { margin-bottom: 20px; color: #666; }
    .stats span { font-weight: 700; margin-right: 16px; }
    .filters { margin-bottom: 20px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .filters button { padding: 6px 14px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; }
    .filters button.active { background: #2563eb; color: #fff; border-color: #2563eb; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
    .card { background: #fff; border-radius: 8px; border: 1px solid #ddd; overflow: hidden; }
    .card.approved { border-color: #16a34a; border-width: 2px; }
    .card.rejected { opacity: 0.4; }
    .card img { width: 100%; cursor: pointer; display: block; }
    .card-body { padding: 12px; }
    .card-caption { font-size: 12px; color: #555; margin-bottom: 8px; max-height: 60px; overflow: hidden; }
    .card-meta { font-size: 11px; color: #999; margin-bottom: 8px; }
    .card-meta a { color: #2563eb; }
    .card-actions { display: flex; gap: 6px; align-items: center; }
    .card-actions button { padding: 4px 10px; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; font-size: 12px; background: #fff; }
    .btn-approve { color: #16a34a; border-color: #16a34a; }
    .btn-approve.active { background: #16a34a; color: #fff; }
    .btn-reject { color: #dc2626; border-color: #dc2626; }
    .btn-reject.active { background: #dc2626; color: #fff; }
    .card-actions select { font-size: 12px; padding: 3px 6px; border-radius: 4px; border: 1px solid #ccc; }
    .lightbox { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; justify-content: center; align-items: center; cursor: pointer; }
    .lightbox.open { display: flex; }
    .lightbox img { max-width: 95%; max-height: 95%; }
    .toolbar { position: sticky; top: 0; background: #f5f5f5; padding: 12px 0; z-index: 100; border-bottom: 1px solid #ddd; margin-bottom: 20px; }
    .toolbar button { padding: 8px 16px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; }
    .toolbar button.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
    .sep { color: #999; margin: 0 8px; }
  </style>
</head>
<body>
  <div class="toolbar">
    <h1>EKG Image Curation</h1>
    <div class="stats" id="stats"></div>
    <div class="filters">
      <button class="active" data-filter="all">All</button>
      <button data-filter="mmvt">MMVT</button>
      <button data-filter="pmvt">PMVT</button>
      <button data-filter="notvt">NotVT</button>
      <span class="sep">|</span>
      <button data-filter="pending">Pending</button>
      <button data-filter="approved">Approved</button>
      <button data-filter="rejected">Rejected</button>
      <span class="sep">|</span>
      <button class="primary" id="exportBtn">Export selections.json</button>
    </div>
  </div>
  <div class="grid" id="grid"></div>
  <div class="lightbox" id="lightbox"><img id="lightboxImg" alt=""></div>

  <script src="data/filtered/gallery-data.js"></script>
  <script>
    const selections = JSON.parse(localStorage.getItem('ekg-selections') || '{}');

    function save() {
      localStorage.setItem('ekg-selections', JSON.stringify(selections));
      updateStats();
    }

    function updateStats() {
      const total = GALLERY_DATA.length;
      const approved = Object.values(selections).filter(s => s.status === 'approved').length;
      const rejected = Object.values(selections).filter(s => s.status === 'rejected').length;
      const pending = total - approved - rejected;
      const el = document.getElementById('stats');
      el.textContent = '';
      const parts = [
        ['Total: ' + total, null],
        ['Approved: ' + approved, '#16a34a'],
        ['Rejected: ' + rejected, '#dc2626'],
        ['Pending: ' + pending, null],
      ];
      for (const [text, color] of parts) {
        const span = document.createElement('span');
        span.textContent = text;
        if (color) span.style.color = color;
        el.appendChild(span);
      }
    }

    function getStatus(filename) {
      return (selections[filename] || {}).status || 'pending';
    }

    function getCategory(filename, original) {
      return (selections[filename] || {}).category || original;
    }

    let activeFilter = 'all';

    function buildCard(item) {
      const status = getStatus(item.filename);
      const category = getCategory(item.filename, item.category);

      if (activeFilter !== 'all') {
        if (['mmvt','pmvt','notvt'].includes(activeFilter) && category !== activeFilter) return null;
        if (['pending','approved','rejected'].includes(activeFilter) && status !== activeFilter) return null;
      }

      const card = document.createElement('div');
      card.className = 'card ' + status;

      const img = document.createElement('img');
      img.src = 'data/filtered/' + item.category + '/' + item.filename;
      img.loading = 'lazy';
      img.alt = 'EKG figure';
      img.addEventListener('click', function() { openLightbox(this.src); });
      card.appendChild(img);

      const body = document.createElement('div');
      body.className = 'card-body';

      const captionDiv = document.createElement('div');
      captionDiv.className = 'card-caption';
      captionDiv.textContent = item.caption || '';
      body.appendChild(captionDiv);

      const metaDiv = document.createElement('div');
      metaDiv.className = 'card-meta';
      const link = document.createElement('a');
      link.href = 'https://pmc.ncbi.nlm.nih.gov/articles/' + encodeURIComponent(item.pmcid) + '/';
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = item.pmcid;
      metaDiv.appendChild(link);
      metaDiv.appendChild(document.createTextNode(' \u00b7 ' + (item.license || 'unknown')));
      body.appendChild(metaDiv);

      const actions = document.createElement('div');
      actions.className = 'card-actions';

      const approveBtn = document.createElement('button');
      approveBtn.className = 'btn-approve' + (status === 'approved' ? ' active' : '');
      approveBtn.textContent = 'Approve';
      approveBtn.addEventListener('click', function() { setStatus(item.filename, 'approved'); });
      actions.appendChild(approveBtn);

      const rejectBtn = document.createElement('button');
      rejectBtn.className = 'btn-reject' + (status === 'rejected' ? ' active' : '');
      rejectBtn.textContent = 'Reject';
      rejectBtn.addEventListener('click', function() { setStatus(item.filename, 'rejected'); });
      actions.appendChild(rejectBtn);

      const select = document.createElement('select');
      for (const cat of ['mmvt', 'pmvt', 'notvt']) {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat.toUpperCase();
        if (cat === category) opt.selected = true;
        select.appendChild(opt);
      }
      select.addEventListener('change', function() {
        setCategory(item.filename, this.value);
      });
      actions.appendChild(select);

      body.appendChild(actions);
      card.appendChild(body);
      return card;
    }

    function render() {
      const grid = document.getElementById('grid');
      grid.textContent = '';
      for (const item of GALLERY_DATA) {
        const card = buildCard(item);
        if (card) grid.appendChild(card);
      }
      updateStats();
    }

    function setStatus(filename, status) {
      if (!selections[filename]) selections[filename] = {};
      selections[filename].status = selections[filename].status === status ? 'pending' : status;
      save();
      render();
    }

    function setCategory(filename, category) {
      if (!selections[filename]) selections[filename] = {};
      selections[filename].category = category;
      save();
    }

    function openLightbox(src) {
      document.getElementById('lightboxImg').src = src;
      document.getElementById('lightbox').classList.add('open');
    }

    document.getElementById('lightbox').addEventListener('click', function() {
      this.classList.remove('open');
    });

    document.querySelectorAll('.filters button[data-filter]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        document.querySelectorAll('.filters button[data-filter]').forEach(function(b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        render();
      });
    });

    document.getElementById('exportBtn').addEventListener('click', function() {
      const blob = new Blob([JSON.stringify(selections, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'selections.json';
      a.click();
    });

    render();
  </script>
</body>
</html>
```

- [ ] **Step 2: Test the gallery**

```bash
cd scripts/pmc-ekgs && open gallery.html
```

Expected: opens in browser, shows image grid with thumbnails, approve/reject buttons, category dropdown, filter tabs, and export button. Click an image to see it full-size.

- [ ] **Step 3: Commit**

```bash
git add scripts/pmc-ekgs/gallery.html
git commit -m "feat: add curation gallery UI (stage 4a)"
```

---

### Task 6: Export script (export.py)

**Files:**
- Create: `scripts/pmc-ekgs/export.py`

- [ ] **Step 1: Create export.py**

Create `scripts/pmc-ekgs/export.py`:

```python
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

    # Load metadata for attribution info
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

    # Track next numbers per category
    counters = {}
    attributions = []

    for filename, sel in sorted(approved.items()):
        category = sel.get("category") or metadata.get(filename, {}).get("category", "mmvt")
        meta = metadata.get(filename, {})

        if category not in counters:
            counters[category] = get_next_number(category, PUBLIC_IMAGES)

        num = counters[category]
        counters[category] += 1

        # Determine source path and extension
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

    # Write attributions
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
```

- [ ] **Step 2: Test export (dry run)**

After curating a few images in the gallery and exporting `selections.json`, move it to `data/selections.json` and run:

```bash
cd scripts/pmc-ekgs && python export.py
```

Expected: copies approved images to `public/images/` with sequential naming (`mmvt-029.png`, etc.), creates/appends `public/ATTRIBUTIONS.md`.

- [ ] **Step 3: Verify exported files**

```bash
ls ../../public/images/mmvt-* | tail -5
cat ../../public/ATTRIBUTIONS.md | tail -10
```

Expected: new images appear with correct naming, attributions are listed.

- [ ] **Step 4: Commit**

```bash
git add scripts/pmc-ekgs/export.py
git commit -m "feat: add export script with attribution tracking (stage 4b)"
```

---

### Task 7: End-to-end run and full download

**Files:** None (this is a run-and-verify task)

- [ ] **Step 1: Run full search**

```bash
cd scripts/pmc-ekgs && python search.py
```

Expected: manifest.json with 500+ articles across all three categories.

- [ ] **Step 2: Run full download**

This will take a while (potentially hours for 500+ articles). Run it and let it go:

```bash
cd scripts/pmc-ekgs && python download.py
```

Expected: downloads and extracts all available OA packages. Some will fail (no OA package available); that's normal.

- [ ] **Step 3: Run filter**

```bash
cd scripts/pmc-ekgs && python filter.py
```

Expected: prints count of EKG images found per category. Images copied to `data/filtered/`.

- [ ] **Step 4: Curate in the gallery**

```bash
cd scripts/pmc-ekgs && open gallery.html
```

Review images. Approve good 12-lead EKGs, reject rhythm strips, blurry images, and non-EKG figures. Recategorize any misclassified images. Click "Export selections.json" when done and move it to `data/selections.json`.

- [ ] **Step 5: Export approved images**

```bash
cd scripts/pmc-ekgs && python export.py
```

- [ ] **Step 6: Deploy**

```bash
cd ../.. && npx wrangler deploy
```

- [ ] **Step 7: Commit exported images and attributions**

```bash
git add public/images/ public/ATTRIBUTIONS.md
git commit -m "feat: add batch of curated EKG images from PMC"
```
