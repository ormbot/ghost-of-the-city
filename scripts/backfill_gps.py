#!/usr/bin/env python3
"""
Backfill GPS coordinates into existing TIMELINE.md entries that lack them.
1. First tries to match against GHOST_DATA.csv (accurate, no API needed)
2. Falls back to Photon geocoder (OSM data, no strict rate limit)
Run once manually; safe to re-run (skips entries that already have GPS).
"""
import csv
import json
import re
import urllib.request
import urllib.parse
import time
import os

TIMELINE = "/home/ubuntu/.openclaw/workspace/journal/TIMELINE.md"
GHOST_DATA = "/home/ubuntu/.openclaw/workspace/GHOST_DATA.csv"


def load_ghost_sites():
    """Load known sites from GHOST_DATA.csv as (keywords, lat, lon) tuples."""
    sites = []
    if not os.path.exists(GHOST_DATA):
        return sites
    with open(GHOST_DATA) as f:
        for row in csv.DictReader(f):
            name = row["name"].lower()
            tags = row.get("tags", "").lower()
            lat = round(float(row["latitude"]), 4)
            lon = round(float(row["longitude"]), 4)
            sites.append((name, tags, lat, lon))
    return sites


def match_ghost_site(text, sites):
    """Return (lat, lon) if the text clearly references a known GHOST_DATA site."""
    text_lower = text.lower()
    for name, tags, lat, lon in sites:
        # Check significant words from the site name (skip short words)
        name_words = [w for w in name.split() if len(w) > 3]
        if name_words and all(w in text_lower for w in name_words):
            return f"{lat}, {lon}"
    return None


def clean_location(text):
    """Strip conversational filler to extract a bare location string."""
    text = text.rstrip('.,!?')
    filler = r"^(so |now |and |also |I'?m |I am |standing |stood |looking at |in front of |at |near |on |in |the |a |an |by |outside |beside |next to |around |behind )"
    prev = None
    while text != prev:
        prev = text
        text = re.sub(filler, "", text.strip(), flags=re.IGNORECASE)
    # Strip trailing location qualifier e.g. "in Kings Cross", "near Barbican"
    text = re.sub(r"\s+(?:in|near|at|by|around)\s+[\w\s']+$", '', text, flags=re.IGNORECASE).strip()
    return text


def photon_geocode(query):
    """Geocode via Photon (komoot) — OSM data, no strict rate limit."""
    encoded = urllib.parse.quote(query)
    url = f"https://photon.komoot.io/api/?q={encoded}&limit=5&lang=en"
    req = urllib.request.Request(url, headers={"User-Agent": "GhostCityChronicle/1.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read())
    features = data.get("features", [])
    # Filter to UK results only
    for f in features:
        props = f.get("properties", {})
        if props.get("countrycode", "").upper() == "GB":
            coords = f["geometry"]["coordinates"]  # [lon, lat]
            return round(coords[1], 4), round(coords[0], 4)
    return None


def get_coordinates(text, sites):
    try:
        # 1. Try GHOST_DATA.csv match first (no API call needed)
        match = match_ghost_site(text, sites)
        if match:
            return match

        # 2. Clean the text and try Photon
        query = clean_location(text)
        if not query:
            return None

        result = photon_geocode(query + " London")
        if result:
            return f"{result[0]}, {result[1]}"

        # Retry: drop last word
        words = query.split()
        if len(words) > 1:
            result = photon_geocode(" ".join(words[:-1]) + " London")
            if result:
                return f"{result[0]}, {result[1]}"

        # Retry: drop last two words
        if len(words) > 2:
            result = photon_geocode(" ".join(words[:-2]) + " London")
            if result:
                return f"{result[0]}, {result[1]}"

    except Exception as e:
        print(f"  [error: {e}]")
    return None


def main():
    sites = load_ghost_sites()
    print(f"Loaded {len(sites)} known sites from GHOST_DATA.csv")

    with open(TIMELINE) as f:
        content = f.read()

    blocks = re.split(r'\n---\n', content)
    updated_blocks = []
    backfilled = 0
    skipped = 0

    for block in blocks:
        # Skip SKIP markers and empty blocks
        if not block.strip() or block.strip().startswith('#'):
            updated_blocks.append(block)
            continue

        # Skip entries that already have GPS
        if re.search(r'^GPS:', block, re.MULTILINE):
            updated_blocks.append(block)
            continue

        # Only process standard entries with a timestamp and You: line
        ts_match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)\]', block.strip())
        you_match = re.search(r'^You: (.+?)(?=Ghost:|$)', block, re.DOTALL | re.MULTILINE)

        if not ts_match or not you_match:
            updated_blocks.append(block)
            continue

        you_text = you_match.group(1).strip().split('\n')[0]
        coords = get_coordinates(you_text, sites)
        time.sleep(0.5)  # light throttle for Photon

        if coords:
            lines = block.strip().split('\n')
            insert_at = 1
            for i, line in enumerate(lines):
                if line.startswith('Weather:'):
                    insert_at = i + 1
                    break
                elif line.startswith('You:') or line.startswith('Ghost:'):
                    insert_at = i
                    break
            lines.insert(insert_at, f"GPS: {coords}")
            updated_blocks.append('\n' + '\n'.join(lines))
            print(f"  + GPS {coords}  [{you_text[:55]}]")
            backfilled += 1
        else:
            updated_blocks.append(block)
            skipped += 1
            print(f"  - no result   [{you_text[:55]}]")

    with open(TIMELINE, 'w') as f:
        f.write('\n---\n'.join(updated_blocks))

    print(f"\nDone. {backfilled} entries backfilled, {skipped} could not be geocoded.")


if __name__ == "__main__":
    main()
