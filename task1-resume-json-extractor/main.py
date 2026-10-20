"""CLI entry point.

Usage:
    python main.py samples/resume1.txt
    python main.py samples/resume1.txt --out output/custom.json
    python main.py samples/resume1.txt --quiet
"""
import argparse
import json
import sys
from pathlib import Path

from extractor import extract, ExtractionError
from schemas import Resume


def main():
    parser = argparse.ArgumentParser(
        description="Extract validated JSON from unstructured resume text using Gemini."
    )
    parser.add_argument("input_file", help="Path to a .txt file containing the resume text")
    parser.add_argument("--out", help="Where to save the JSON (default: output/<input name>.json)")
    parser.add_argument("--quiet", action="store_true", help="Only print the final JSON")
    args = parser.parse_args()

    # 1. Read the input file
    path = Path(args.input_file)
    if not path.is_file():
        sys.exit(f"Error: file not found: {path}")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        sys.exit(f"Error: {path} is empty")

    # 2. Run the pipeline
    if not args.quiet:
        print(f"Extracting from {path} ...")
    try:
        result = extract(text, Resume, doc_type="resume", verbose=not args.quiet)
    except ExtractionError as e:
        sys.exit(f"Extraction failed: {e}")

    # 3. Print + save
    output = result.model_dump()
    print(json.dumps(output, indent=2, ensure_ascii=False))

    out_path = Path(args.out) if args.out else Path("output") / f"{path.stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.quiet:
        print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()