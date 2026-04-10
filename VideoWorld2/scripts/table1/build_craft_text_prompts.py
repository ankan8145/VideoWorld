#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_items(path: Path):
    with path.open("r", encoding="utf-8") as f:
        if path.suffix == ".jsonl":
            return [json.loads(line) for line in f if line.strip()]
        return json.load(f)


def build_step_string(steps, step_format):
    if not isinstance(steps, list):
        return ""
    lines = [str(s).strip() for s in steps if str(s).strip()]
    return " ".join(step_format.format(index=i + 1, step=line) for i, line in enumerate(lines))


def main():
    parser = argparse.ArgumentParser(description="Build craft-text prompts from step annotations.")
    parser.add_argument("--input", required=True, help="Input annotations (.json or .jsonl).")
    parser.add_argument("--output", required=True, help="Output prompt file (.jsonl).")
    parser.add_argument("--id-key", default="id", help="Sample ID key in input.")
    parser.add_argument("--steps-key", default="steps", help="Steps key in input.")
    parser.add_argument("--prefix", default="A high-definition video captures the scene of handicraft production.", help="Prefix text.")
    parser.add_argument(
        "--step-format",
        default="Step {index}: {step}",
        help="Formatting template for each step. Supports {index} and {step}.",
    )
    args = parser.parse_args()

    items = load_items(Path(args.input))
    if isinstance(items, dict):
        items = items.get("data", [])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in items:
            sample_id = item.get(args.id_key)
            steps = item.get(args.steps_key, [])
            prompt = f"{args.prefix} {build_step_string(steps, args.step_format)}".strip()
            f.write(json.dumps({"id": sample_id, "craft_text_prompt": prompt}, ensure_ascii=False) + "\n")

    print(f"Wrote prompts to {out_path}")


if __name__ == "__main__":
    main()
