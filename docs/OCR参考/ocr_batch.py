"""
OCR batch-process PDF files using the GLM-OCR API.
Usage:
  python ocr_batch.py <batches_dir> [--output-dir <dir>] [--api-key <key>] [--sleep <s>]

API key is resolved in this order:
  1. --api-key CLI argument
  2. GLM_API_KEY environment variable
  3. .env file in the same directory as this script
"""
import os
import sys
import re
import time
import json
import base64
import argparse
import requests

API_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
DEFAULT_SLEEP = 5


def load_env_file(script_dir):
    """Load GLM_API_KEY from .env file if present."""
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GLM_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def get_api_key(cli_key):
    """Resolve API key from CLI, env var, or .env file."""
    if cli_key:
        return cli_key
    env_key = os.environ.get("GLM_API_KEY")
    if env_key:
        return env_key
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_key = load_env_file(script_dir)
    if file_key:
        return file_key
    return None


def find_batch_files(batches_dir):
    """Find all batch PDF files, sorted by batch number."""
    pattern = re.compile(r"^batch_(\d+)_.*\.pdf$")
    batch_files = []
    for fname in os.listdir(batches_dir):
        m = pattern.match(fname)
        if m and not fname.endswith("_result.md"):
            batch_files.append((int(m.group(1)), fname))
    batch_files.sort()
    return [f[1] for f in batch_files]


def ocr_pdf(file_path, api_key):
    """Send a PDF to GLM-OCR API, return markdown text."""
    with open(file_path, "rb") as f:
        file_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": "glm-ocr",
        "file": f"data:application/pdf;base64,{file_b64}",
    }
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    size_mb = len(file_b64) / 1024 / 1024
    print(f"    Sending {size_mb:.1f} MB...")
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=600)
    resp.raise_for_status()

    data = resp.json()
    md_results = data.get("md_results", "")
    if not md_results:
        print(f"    WARNING: No md_results in response. Keys: {list(data.keys())}")
        md_results = json.dumps(data, ensure_ascii=False, indent=2)

    usage = data.get("usage", {})
    if usage:
        print(f"    Tokens: {usage.get('total_tokens', '?')} "
              f"(prompt: {usage.get('prompt_tokens', '?')}, "
              f"completion: {usage.get('completion_tokens', '?')})")
    return md_results


def result_name(batch_name):
    """Derive result filename from batch PDF name."""
    base = os.path.splitext(batch_name)[0]
    return f"{base}_result.md"


def main():
    parser = argparse.ArgumentParser(
        description="OCR batch-process PDF files using GLM-OCR API"
    )
    parser.add_argument(
        "batches_dir",
        help="Directory containing batch_*.pdf files (from split_pdf.py)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Output directory for OCR results (default: same as batches_dir)"
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="GLM API key (or set GLM_API_KEY env var)"
    )
    parser.add_argument(
        "--sleep", "-s",
        type=int,
        default=DEFAULT_SLEEP,
        help=f"Seconds to sleep between API calls (default: {DEFAULT_SLEEP})"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Re-OCR batches that already have result files"
    )
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)
    if not api_key:
        print("ERROR: No API key found. Provide --api-key, set GLM_API_KEY env var, "
              "or create .env file with GLM_API_KEY=xxx")
        sys.exit(1)

    if not os.path.isdir(args.batches_dir):
        print(f"ERROR: Directory not found: {args.batches_dir}")
        sys.exit(1)

    out_dir = args.output_dir or args.batches_dir
    os.makedirs(out_dir, exist_ok=True)

    batch_files = find_batch_files(args.batches_dir)
    if not batch_files:
        print(f"ERROR: No batch_*.pdf files found in: {args.batches_dir}")
        sys.exit(1)

    print(f"GLM-OCR batch processing")
    print(f"Input dir : {args.batches_dir}")
    print(f"Output dir: {out_dir}")
    print(f"Batches   : {len(batch_files)}")
    print(f"API key   : {api_key[:8]}...{api_key[-4:]}")
    print()

    results = []
    for i, batch_name in enumerate(batch_files):
        out_name = result_name(batch_name)
        out_path = os.path.join(out_dir, out_name)
        in_path = os.path.join(args.batches_dir, batch_name)

        if os.path.exists(out_path) and not args.force:
            fsize = os.path.getsize(out_path)
            print(f"[{i+1}/{len(batch_files)}] SKIP {batch_name} "
                  f"(result exists, {fsize} bytes)")
            results.append({"batch": batch_name, "status": "skipped"})
            continue

        fsize_mb = os.path.getsize(in_path) / 1024 / 1024
        print(f"[{i+1}/{len(batch_files)}] {batch_name} ({fsize_mb:.1f} MB)")

        try:
            md_content = ocr_pdf(in_path, api_key)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            print(f"    Saved: {out_name} ({len(md_content)} chars)")
            results.append({"batch": batch_name, "status": "ok", "size": len(md_content)})
        except requests.exceptions.HTTPError as e:
            print(f"    HTTP ERROR {e.response.status_code}: {e.response.text[:300]}")
            results.append({"batch": batch_name, "status": "error", "error": str(e)})
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"batch": batch_name, "status": "error", "error": str(e)})

        if i < len(batch_files) - 1:
            print(f"    Sleeping {args.sleep}s...")
            time.sleep(args.sleep)
        print()

    print("=" * 60)
    ok = sum(1 for r in results if r["status"] in ("ok", "skipped"))
    for r in results:
        icon = "[OK]" if r["status"] == "ok" else "[SKIP]" if r["status"] == "skipped" else "[FAIL]"
        detail = ""
        if r["status"] == "ok":
            detail = f"({r['size']} chars)"
        elif r["status"] == "error":
            detail = f"- {r.get('error', '')[:80]}"
        print(f"  {icon} {r['batch']} {detail}")
    print(f"\nDone: {ok}/{len(batch_files)} batches processed")


if __name__ == "__main__":
    main()
