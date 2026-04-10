#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def to_percent(v):
    if v is None:
        return ""
    if v <= 1:
        return round(v * 100, 2)
    return round(v, 2)


def main():
    parser = argparse.ArgumentParser(description="Aggregate per-method metrics into Table-1 files.")
    parser.add_argument("--manifest", required=True, help="Manifest JSON used for runs.")
    parser.add_argument("--output-csv", required=True, help="Output CSV path.")
    parser.add_argument("--output-md", required=True, help="Output Markdown path.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    manifest = read_json(manifest_path)
    methods = manifest.get("methods", [])
    base_dir = manifest_path.parent

    rows = []
    for item in methods:
        metrics_path = item.get("metrics_file")
        if not metrics_path:
            continue
        p = Path(metrics_path)
        if not p.is_absolute():
            p = base_dir / p
        if not p.exists():
            continue
        m = read_json(p)
        rows.append(
            {
                "method": item.get("name", ""),
                "condition": item.get("condition", ""),
                "success_rate_percent": to_percent(m.get("success_rate")),
                "variance": m.get("variance", ""),
                "ci95": m.get("ci95", ""),
                "notes": m.get("notes", ""),
            }
        )

    out_csv = Path(args.output_csv)
    out_md = Path(args.output_md)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["method", "condition", "success_rate_percent", "variance", "ci95", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)

    with out_md.open("w", encoding="utf-8") as f:
        f.write("| Method | Condition | Success Rate (%) | Variance | CI95 | Notes |\n")
        f.write("|---|---|---:|---:|---:|---|\n")
        for r in rows:
            f.write(
                f"| {r['method']} | {r['condition']} | {r['success_rate_percent']} | {r['variance']} | {r['ci95']} | {r['notes']} |\n"
            )

    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()

