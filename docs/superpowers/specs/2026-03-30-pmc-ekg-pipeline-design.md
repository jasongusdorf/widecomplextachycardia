# PMC EKG Image Pipeline

## Purpose

Programmatically source hundreds of 12-lead EKG images from PubMed Central's open-access subset for use in the widecomplextachycardia.com drill. Target: ~150-200 MMVT, ~50-80 PMVT, ~150-200 NotVT (SVT with aberrancy / WCT mimics).

## Architecture

A Python CLI tool at `scripts/pmc-ekgs/` with four independent stages. Each stage reads from the previous stage's output, so the pipeline can be stopped, inspected, and resumed at any point.

```
search --> download --> filter --> curate --> export
 (API)     (FTP/HTTP)   (XML)     (browser)   (copy)
```

### Directory structure

```
scripts/pmc-ekgs/
  search.py          # Stage 1: query PMC, produce manifest
  download.py        # Stage 2: fetch .tar.gz packages, extract images
  filter.py          # Stage 3: parse XML captions, keep EKG figures only
  export.py          # Stage 4: copy approved images, generate attributions
  gallery.html        # Curation UI (static, opens in browser)
  requirements.txt   # requests, lxml
  data/              # Working directory (gitignored)
    manifest.json    # PMCIDs + metadata from search
    packages/        # Downloaded .tar.gz files
    extracted/       # Extracted images + XML, organized by PMCID
    filtered/        # EKG images only, with metadata CSV
    selections.json  # Approve/reject decisions from curation
```

## Stage 1: Search

Query PMC E-utilities API (`esearch.fcgi`) for open-access case reports. Three search categories:

**MMVT:**
```
("monomorphic ventricular tachycardia" OR ("ventricular tachycardia" NOT "polymorphic" NOT "torsades"))
AND ("12-lead" OR "electrocardiogram" OR "ECG")
AND "case report"
AND open access[filter]
```

**PMVT:**
```
("polymorphic ventricular tachycardia" OR "torsades de pointes" OR "torsade de pointes")
AND ("12-lead" OR "electrocardiogram" OR "ECG")
AND "case report"
AND open access[filter]
```

**NotVT:**
```
("SVT with aberrancy" OR "supraventricular tachycardia" "wide complex"
OR "wide complex tachycardia" OR "antidromic" OR "pre-excited atrial fibrillation")
AND ("12-lead" OR "electrocardiogram" OR "ECG")
AND "case report"
AND open access[filter]
```

Pagination: E-utilities returns batches of 500 (`retmax=500`, increment `retstart`). Deduplicate across categories (an article may match multiple queries; keep the first category match).

Rate limiting: 10 req/sec with API key, 3 req/sec without. The script accepts an optional `--api-key` argument.

Output: `data/manifest.json` containing an array of objects:
```json
{
  "pmcid": "PMC1234567",
  "title": "Article title",
  "category": "mmvt",
  "query": "the query that matched"
}
```

## Stage 2: Download

For each PMCID in the manifest:

1. Call the OA Web Service (`oa.fcgi?id=PMC{ID}&format=tgz`) to get the FTP/HTTP link and license.
2. Download the `.tar.gz` package.
3. Extract contents into `data/extracted/{PMCID}/`.
4. Record the license in the manifest.

Rate limiting: 3 req/sec for OA service. Downloads are sequential with a 0.35s delay between requests. Resume support: skip PMCIDs that already have an extracted directory.

The OA service may not have a package for every PMCID (some OA articles lack downloadable packages). Log these as skipped.

## Stage 3: Filter

For each extracted article:

1. Parse the article XML (JATS format) to build a map of figure filenames to captions.
2. Apply caption keyword matching.

**Include if caption matches any of:** electrocardiogram, electrocardiograph, ECG, EKG, 12-lead, twelve-lead, tachycardia, rhythm strip.

**Exclude if caption matches any of:** echocardiogram, angiogram, angiography, CT scan, MRI, X-ray, xray, ultrasound, histology, pathology, catheterization, coronary, Doppler, photograph, gross specimen.

3. Copy matching images to `data/filtered/{category}/` with a descriptive filename: `{PMCID}_{fig_id}.{ext}`.
4. Write `data/filtered/metadata.csv` with columns: filename, pmcid, category, caption, license, article_title, doi.

Images without a matching caption entry (e.g., inline images not wrapped in a `<fig>` element) are skipped.

## Stage 4: Curate and export

### Curation gallery (gallery.html)

A self-contained HTML file. The filter stage also generates a `data/filtered/gallery-data.js` file (a JS variable assignment wrapping the metadata array) that the HTML loads via a script tag. Features:

- Thumbnail grid grouped by category (MMVT / PMVT / NotVT)
- Click to enlarge
- Caption text, article title, PMCID (linked to PMC), license badge
- Approve / Reject / Recategorize (dropdown to move between MMVT/PMVT/NotVT) buttons
- Selections persisted to `data/selections.json` via localStorage export

### Export (export.py)

Reads `data/selections.json`. For each approved image:

1. Determine the next available number in the naming sequence (e.g., `mmvt-029.png` if 28 exist).
2. Copy the image to `public/images/` with the correct name.
3. Append an entry to `public/ATTRIBUTIONS.md`:
   ```
   mmvt-029.png: [Article Title]. Authors. Journal, Year. PMC1234567. DOI. License: CC BY 4.0.
   ```

## Dependencies

```
requests
lxml
```

No heavy dependencies. Standard library handles tarfile extraction, CSV, JSON. The curation gallery is pure HTML/JS with no build step.

## API key

The NCBI E-utilities API key is free. Register at https://www.ncbi.nlm.nih.gov/account/ and find it under Settings. Pass it to the scripts via `--api-key` or the `NCBI_API_KEY` environment variable. The pipeline works without one (slower rate limit).

## Licensing compliance

All images come from PMC's open-access subset. The pipeline tracks license type per article. The export step generates `ATTRIBUTIONS.md` with full citation and license for every image used. Images under CC BY require attribution only. Images under CC BY-NC additionally require non-commercial use (the site is educational/non-commercial).

## Estimated yield

| Category | OA articles | Articles with 12-lead figure | After quality curation |
|----------|------------|-----------------------------|-----------------------|
| MMVT     | ~649       | ~400-500                    | ~150-200              |
| PMVT     | ~400-800   | ~300-500                    | ~50-80                |
| NotVT    | ~300-600   | ~150-350                    | ~150-200              |

PMVT yield is lower after curation because many PMVT images show rhythm strips (monitor captures during the acute event) rather than full 12-lead printouts.
