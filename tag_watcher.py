#!/usr/bin/env python3
"""
tag_watcher.py — Pinboard new tag detector

Fetches all tags from Pinboard, diffs against a stored baseline,
and reports any net-new tags since last run.

Usage:
  python tag_watcher.py --report       # show new tags, don't update baseline
  python tag_watcher.py --update       # report + update baseline
  python tag_watcher.py --init         # set baseline from current state (first run)
  python tag_watcher.py --full         # dump full tag list with counts
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

PINBOARD_TOKEN = os.getenv("PINBOARD_TOKEN")
API_BASE = "https://api.pinboard.in/v1"
BASELINE_FILE = Path(__file__).parent / "tags_baseline.json"


def get_tags() -> dict[str, int]:
    """Fetch all tags from Pinboard. Returns {tag: count}."""
    if not PINBOARD_TOKEN:
        print("ERROR: PINBOARD_TOKEN not set. Add to .env or environment.", file=sys.stderr)
        sys.exit(1)

    url = f"{API_BASE}/tags/get"
    params = {"auth_token": PINBOARD_TOKEN, "format": "json"}

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # API returns {"tag": "count_string", ...}
    return {tag: int(count) for tag, count in data.items()}


def load_baseline() -> dict[str, int] | None:
    """Load the stored baseline. Returns None if not initialized."""
    if not BASELINE_FILE.exists():
        return None
    with open(BASELINE_FILE) as f:
        data = json.load(f)
    return data.get("tags", {})


def save_baseline(tags: dict[str, int]) -> None:
    """Save current tag list as the new baseline."""
    payload = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "count": len(tags),
        "tags": tags,
    }
    with open(BASELINE_FILE, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    print(f"Baseline saved: {len(tags)} tags → {BASELINE_FILE}")


def find_new_tags(baseline: dict[str, int], current: dict[str, int]) -> list[str]:
    """Return tags in current that are not in baseline."""
    return sorted(set(current.keys()) - set(baseline.keys()))


def cmd_init(args):
    current = get_tags()
    save_baseline(current)
    print(f"Initialized baseline with {len(current)} tags.")


def cmd_report(args):
    baseline = load_baseline()
    if baseline is None:
        print("No baseline found. Run --init first.")
        sys.exit(1)

    current = get_tags()
    new_tags = find_new_tags(baseline, current)

    if not new_tags:
        print("No new tags since last baseline.")
        return

    print(f"\n{len(new_tags)} new tag(s) since last baseline:\n")
    for tag in new_tags:
        count = current[tag]
        print(f"  {tag}  ({count} bookmark{'s' if count != 1 else ''})")

    if args.update:
        save_baseline(current)


def cmd_full(args):
    current = get_tags()
    print(f"\nFull tag list ({len(current)} tags):\n")
    for tag, count in sorted(current.items(), key=lambda x: -x[1]):
        print(f"  {tag:<40} {count}")


def main():
    parser = argparse.ArgumentParser(description="Pinboard tag watcher")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", action="store_true", help="Initialize baseline from current tags")
    group.add_argument("--report", action="store_true", help="Report new tags since baseline")
    group.add_argument("--full", action="store_true", help="Dump full tag list")
    parser.add_argument("--update", action="store_true", help="Update baseline after reporting (use with --report)")

    args = parser.parse_args()

    if args.init:
        cmd_init(args)
    elif args.report:
        cmd_report(args)
    elif args.full:
        cmd_full(args)


if __name__ == "__main__":
    main()
