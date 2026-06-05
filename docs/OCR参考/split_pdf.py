"""
Split a PDF into smaller batches for OCR processing.
Usage: python split_pdf.py <pdf_path> [--output-dir <dir>] [--pages-per-batch <n>]
"""
import os
import sys
import argparse
from PyPDF2 import PdfReader, PdfWriter


def main():
    parser = argparse.ArgumentParser(
        description="Split a PDF into smaller batches for OCR processing"
    )
    parser.add_argument("pdf_path", help="Path to the input PDF file")
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Output directory for batch files (default: <pdf_dir>/batches/)"
    )
    parser.add_argument(
        "--pages-per-batch", "-n",
        type=int,
        default=84,
        help="Number of pages per batch (default: 84)"
    )
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"ERROR: PDF not found: {args.pdf_path}")
        sys.exit(1)

    reader = PdfReader(args.pdf_path)
    total = len(reader.pages)
    print(f"PDF: {args.pdf_path}")
    print(f"Total pages: {total}")

    if args.output_dir is None:
        args.output_dir = os.path.join(os.path.dirname(args.pdf_path) or ".", "batches")
    os.makedirs(args.output_dir, exist_ok=True)

    batch_num = 0
    for start in range(0, total, args.pages_per_batch):
        batch_num += 1
        end = min(start + args.pages_per_batch, total)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out_name = f"batch_{batch_num:02d}_p{start+1}-p{end}.pdf"
        out_path = os.path.join(args.output_dir, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)
        print(f"  [{batch_num}] pages {start+1}-{end} -> {out_name} ({end-start} pages)")

    print(f"\nDone. {batch_num} batch(es) written to: {args.output_dir}")


if __name__ == "__main__":
    main()
