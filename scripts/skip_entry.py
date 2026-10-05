#!/usr/bin/env python3
import sys
import os

TIMELINE = os.path.expanduser("~/.openclaw/workspace/journal/TIMELINE.md")

if len(sys.argv) < 2:
    print("Usage: python3 skip_entry.py 'YYYY-MM-DD HH:MM UTC'")
    sys.exit(1)

timestamp = sys.argv[1]

with open(TIMELINE, "a") as f:
    f.write(f"\n# SKIP [{timestamp}]\n")

print(f"Skipping entry: {timestamp}")
