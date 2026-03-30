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
