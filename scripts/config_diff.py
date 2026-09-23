#!/usr/bin/env python3
"""config_diff.py — Compare MikroTik RouterOS config backups against baselines.

Reads one current backup per device (RouterOS `/export` output), normalizes
volatile header lines (timestamps, software ids, serial numbers), diffs each
file against its baseline with difflib, and writes a Markdown drift report.

Exit codes: 0 = no drift detected, 1 = drift detected, 2 = runtime error.
This makes the script directly usable as a CI/scheduled audit step:
any non-zero exit means "a human should look at the report".

Usage:
    python3 scripts/config_diff.py \
        --baselines baselines/ \
        --current backups/ \
        --output reports/drift-report.md
"""

import argparse
import difflib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Header lines emitted by `/export` that change on every run and carry no
# configuration meaning. Everything else is compared verbatim.
VOLATILE_PATTERNS = [
    r"^\#\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+by RouterOS",
    r"^\#\s+software id\s*=",
    r"^\#\s+model\s*=",
    r"^\#\s+serial number\s*=",
]
VOLATILE = [re.compile(p) for p in VOLATILE_PATTERNS]


def normalize(lines):
    """Drop volatile header lines and trailing whitespace."""
    out = []
    for line in lines:
        stripped = line.rstrip()
        if any(p.match(stripped) for p in VOLATILE):
            continue
        if stripped == "#":
            continue
        out.append(stripped)
    # Collapse runs of blank lines to one so formatting noise doesn't count.
    compacted = []
    for line in out:
        if line == "" and compacted and compacted[-1] == "":
            continue
        compacted.append(line)
    return compacted


def diff_device(device, baseline_lines, current_lines):
    """Return (added, removed, diff_text) for one device."""
    diff = list(
        difflib.unified_diff(
            baseline_lines,
            current_lines,
            fromfile=f"{device} (baseline)",
            tofile=f"{device} (current)",
            lineterm="",
        )
    )
    # Skip the --- / +++ header lines when counting.
    body = [l for l in diff if not l.startswith(("---", "+++"))]
    added = sum(1 for l in body if l.startswith("+"))
    removed = sum(1 for l in body if l.startswith("-"))
    return added, removed, "\n".join(diff)


def main():
    ap = argparse.ArgumentParser(description="Diff RouterOS backups against baselines.")
    ap.add_argument("--baselines", required=True, help="Directory with baseline .rsc files")
    ap.add_argument("--current", required=True, help="Directory with current backup .rsc files")
    ap.add_argument("--output", required=True, help="Markdown report to write")
    args = ap.parse_args()

    base_dir = Path(args.baselines)
    curr_dir = Path(args.current)
    out_path = Path(args.output)

    try:
        devices = sorted(
            {p.stem for p in base_dir.glob("*.rsc")}
            | {p.stem for p in curr_dir.glob("*.rsc")}
        )
        if not devices:
            print("No .rsc files found in baselines/ or current.", file=sys.stderr)
            return 2

        sections = []
        total_added = total_removed = 0
        drifted = []

        for device in devices:
            b_file, c_file = base_dir / f"{device}.rsc", curr_dir / f"{device}.rsc"
            if not b_file.exists():
                sections.append(f"## {device}\n\nNo baseline found — cannot assess drift.\n")
                continue
            if not c_file.exists():
                sections.append(f"## {device}\n\nNo current backup found — device unreachable?\n")
                continue
            base = normalize(b_file.read_text().splitlines())
            curr = normalize(c_file.read_text().splitlines())
            added, removed, text = diff_device(device, base, curr)
            total_added += added
            total_removed += removed
            if added or removed:
                drifted.append(device)
                sections.append(
                    f"## {device} — DRIFT DETECTED (+{added}/-{removed})\n\n"
                    f"```diff\n{text}\n```\n"
                )
            else:
                sections.append(f"## {device} — clean, no changes vs baseline.\n")

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        status = (
            f"**DRIFT DETECTED** on {', '.join(drifted)}"
            if drifted
            else "**CLEAN** — all devices match their baselines."
        )
        report = (
            f"# Configuration drift report\n\n"
            f"Generated: {stamp}\n\n"
            f"Devices checked: {len(devices)} | "
            f"Lines added: {total_added} | Lines removed: {total_removed}\n\n"
            f"## Verdict\n\n{status}\n\n"
            + "\n".join(sections)
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report)

        print(f"Checked {len(devices)} device(s): {status}")
        print(f"Report: {out_path}")
        return 1 if drifted else 0

    except Exception as exc:  # noqa: BLE001 — report and exit 2, don't traceback in CI
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
