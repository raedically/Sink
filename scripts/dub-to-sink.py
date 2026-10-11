#!/usr/bin/env python3
"""Convert a Dub dashboard CSV export without publishing private link targets."""

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


def convert(rows, domain):
    links = []
    seen = set()
    skipped = {"other_domain": 0, "root": 0}
    for row in rows:
        short = row["Short link"].strip()
        parsed = urlsplit(short if "://" in short else "https://" + short)
        if parsed.hostname != domain:
            skipped["other_domain"] += 1
            continue
        slug = parsed.path.removeprefix("/")
        if not slug:
            skipped["root"] += 1
            continue
        if not re.fullmatch(r"[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*", slug):
            raise ValueError("A slug cannot be represented by Sink; inspect the private export")
        if slug.lower() == "dashboard" or slug in seen:
            raise ValueError("Reserved or duplicate slug; refusing a partial migration")
        seen.add(slug)
        if row.get("Archived", "No").lower() not in ("no", "false", "0", ""):
            raise ValueError("Archived links require manual review")
        if row.get("Tags", "").strip():
            raise ValueError("Tagged links require a reviewed tag mapping")
        target = row["Destination URL"].strip()
        if urlsplit(target).scheme not in ("http", "https") or not urlsplit(target).hostname:
            raise ValueError("Unsupported destination URL")
        link = {
            "id": hashlib.sha256(short.encode()).hexdigest()[:26],
            "slug": slug,
            "url": target,
            "tags": [],
        }
        for source, dest in (("Created at", "createdAt"), ("Updated at", "updatedAt")):
            if row.get(source):
                link[dest] = int(datetime.fromisoformat(row[source].replace("Z", "+00:00")).timestamp())
        links.append(link)
    if not links:
        raise ValueError("No links matched the requested domain")
    return {"version": "0.3.1", "exportedAt": datetime.now(timezone.utc).isoformat(),
            "count": len(links), "links": links}, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--domain", required=True)
    args = parser.parse_args()
    with args.source.open(encoding="utf-8-sig", newline="") as source:
        data, skipped = convert(csv.DictReader(source), args.domain)
    # Exclusive creation protects earlier exports; private permissions protect targets.
    with args.destination.open("x", encoding="utf-8") as destination:
        args.destination.chmod(0o600)
        json.dump(data, destination, indent=2, ensure_ascii=False)
        destination.write("\n")
    print(json.dumps({"converted": data["count"], "skipped": skipped}))


if __name__ == "__main__":
    main()
