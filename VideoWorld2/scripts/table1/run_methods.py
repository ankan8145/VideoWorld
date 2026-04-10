#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_metrics_path(base_dir: Path, metrics_path: str) -> Path:
    p = Path(metrics_path)
    return p if p.is_absolute() else (base_dir / p)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Table-1 methods from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory for run logs.")
    parser.add_argument("--only", nargs="*", default=None, help="Run only selected method names.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(manifest_path)

    common = manifest.get("common", {})
    methods = manifest.get("methods", [])
    if not methods:
        print("No methods found in manifest.", file=sys.stderr)
        return 1

    selected = set(args.only) if args.only else None
    repo_root = manifest_path.parents[2] if (manifest_path.parent.name == "table1" and manifest_path.parent.parent.name == "scripts") else Path.cwd()
    env = os.environ.copy()
    for k, v in common.items():
        if isinstance(v, (str, int, float)):
            env[f"TABLE1_{str(k).upper()}"] = str(v)

    failures = []
    for item in methods:
        name = item["name"]
        if selected is not None and name not in selected:
            continue

        cmd = item["command"]
        metrics_file = item.get("metrics_file")
        log_file = output_dir / f"{name}.log"

        print(f"[RUN] {name}: {cmd}")
        if args.dry_run:
            continue

        with log_file.open("w", encoding="utf-8") as lf:
            proc = subprocess.run(cmd, shell=True, cwd=str(repo_root), env=env, stdout=lf, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            failures.append((name, f"command failed ({proc.returncode})"))
            continue

        if metrics_file:
            mf = normalize_metrics_path(manifest_path.parent, metrics_file)
            if not mf.exists():
                failures.append((name, f"metrics file missing: {mf}"))

    if failures:
        print("\nFailures:")
        for name, reason in failures:
            print(f"- {name}: {reason}")
        return 2

    print("All selected methods completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

