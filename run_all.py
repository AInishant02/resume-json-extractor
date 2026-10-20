"""Runs the pipeline on every file in samples/ and saves a results table."""
import time
from pathlib import Path

from extractor import extract, ExtractionError
from schemas import Resume


def main():
    files = sorted(Path("samples").glob("*.txt"))
    Path("output").mkdir(exist_ok=True)
    rows = []

    for i, f in enumerate(files):
        print(f"\n=== {f.name} ===")
        start = time.time()
        try:
            result = extract(f.read_text(encoding="utf-8"), Resume)
            out = Path("output") / f"{f.stem}.json"
            out.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            status = "PASS - valid JSON saved"
        except ExtractionError as e:
            msg = str(e)
            print(f"  {msg[:250]}")
            if "does not look like a resume" in msg:
                status = "REJECTED - not a resume"
            elif "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                status = "API ERROR - quota exceeded"
            elif "503" in msg or "UNAVAILABLE" in msg:
                status = "API ERROR - model overloaded"
            else:
                status = "REJECTED - validation failed"
        rows.append((f.name, status, time.time() - start))
        if "quota exceeded" in status:
            print("\nQuota exhausted - stopping so no more requests are wasted.")
            break
        if i < len(files) - 1:
            time.sleep(10)  

    lines = [
        "| File | Result | Time |",
        "|---|---|---|",
        *[f"| `{n}` | {s} | {t:.1f}s |" for n, s, t in rows],
    ]
    table = "\n".join(lines)
    Path("output/results.md").write_text(table + "\n", encoding="utf-8")

    print("\n" + table)
    print("\nSaved to output/results.md")


if __name__ == "__main__":
    main()