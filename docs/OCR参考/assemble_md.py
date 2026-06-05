"""
Merge batch OCR results into a single markdown file.
Usage: python assemble_md.py <results_dir> --output <output_path>
"""
import os
import sys
import re
import argparse


def find_result_files(results_dir):
    """Find all batch result files, sorted by batch number.
    Returns list of (batch_num, filename, page_range_str)."""
    pattern = re.compile(r"^batch_(\d+)_p(\d+)-p(\d+)_result\.md$")
    files = []
    for fname in os.listdir(results_dir):
        m = pattern.match(fname)
        if m:
            batch_num = int(m.group(1))
            page_start = int(m.group(2))
            page_end = int(m.group(3))
            page_range = f"第{page_start}-{page_end}页"
            files.append((batch_num, fname, page_range))
    files.sort()
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Merge batch OCR results into a single markdown file"
    )
    parser.add_argument(
        "results_dir",
        help="Directory containing batch_*_result.md files (from ocr_batch.py)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output path for the merged markdown file"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.results_dir):
        print(f"ERROR: Directory not found: {args.results_dir}")
        sys.exit(1)

    result_files = find_result_files(args.results_dir)
    if not result_files:
        print(f"ERROR: No batch_*_result.md files found in: {args.results_dir}")
        sys.exit(1)

    total_chars = 0
    parts = []
    for batch_num, fname, page_range in result_files:
        file_path = os.path.join(args.results_dir, fname)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        total_chars += len(content)
        parts.append(f"<!-- ======== {page_range} ======== -->\n\n{content}")
        print(f"  [{batch_num}] {fname}: {len(content)} chars  ({page_range})")

    full_content = "\n\n".join(parts)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"\nMerged  : {args.output}")
    print(f"Parts   : {len(parts)}")
    print(f"Total   : {total_chars} chars")
    print(f"Size    : {os.path.getsize(args.output) / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
