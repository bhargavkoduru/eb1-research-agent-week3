"""Create an OCR input from selected public policy pages without modifying the original."""
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True, help="First source PDF page, 1-based")
    parser.add_argument("--end", type=int, required=True, help="Last source PDF page, inclusive")
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if not args.name.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Use a simple name containing letters, numbers, hyphens or underscores")
    source = ROOT / "Policy Manual_USCIS_eb.pdf"
    folder = ROOT / "data" / "prepared"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{args.name}.pdf"
    manifest_path = folder / f"{args.name}.manifest.json"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    doc = pymupdf.open(source)
    if not 1 <= args.start <= args.end <= len(doc):
        raise ValueError("Invalid source page range")
    manifest = {
        "source_file": source.name, "source_sha256": source_hash,
        "source_total_pages": len(doc), "source_snapshot_date": "2026-09-23",
        "snapshot_date_basis": "Visible browser print header; not the policy effective date",
        "source_url": "https://www.uscis.gov/book/export/html/68600",
        "operation": "Render at 220 DPI after a 90-degree clockwise correction; image-only PDF forces OCR",
        "page_map": [{"prepared_page": n, "source_pdf_page": p}
                     for n, p in enumerate(range(args.start, args.end + 1), 1)],
    }
    if target.exists() or manifest_path.exists():
        if target.exists() and manifest_path.exists() and json.loads(manifest_path.read_text()) == manifest:
            print(json.dumps({"prepared": str(target.relative_to(ROOT)), "status": "already_prepared"}))
            return
        raise FileExistsError("Existing preparation differs; choose a new name")
    output = pymupdf.open()
    for number in range(args.start - 1, args.end):
        page = doc[number]
        page.set_rotation((page.rotation + 90) % 360)
        pix = page.get_pixmap(dpi=220, alpha=False)
        rendered = output.new_page(width=page.rect.width, height=page.rect.height)
        rendered.insert_image(rendered.rect, stream=pix.tobytes("png"))
    output.set_metadata({"title": "USCIS public policy research excerpt"})
    output.save(target, garbage=4, deflate=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"prepared": str(target.relative_to(ROOT)), "pages": len(output), "bytes": target.stat().st_size}))


if __name__ == "__main__":
    main()

