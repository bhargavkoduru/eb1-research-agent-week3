"""Separate EB-1A / EB-1B policy text while retaining page provenance."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLES = {2: "Extraordinary Ability", 3: "Outstanding Professor or Researcher"}
NAMES = {2: "eb1a", 3: "eb1b"}
HEADING = re.compile(r"(?m)^#{0,6}\s*Chapter\s+([234])\s*[-\u2013\u2014:]\s*[^\n]+")


def main():
    records = []
    for batch in ("pilot", "eb1_remainder"):
        records.extend(json.loads((ROOT / "data" / "parsed" / batch / "pages.json").read_text(encoding="utf-8")))
    records.sort(key=lambda page: page["source_pdf_page"])
    if [p["source_pdf_page"] for p in records] != list(range(2, 25)):
        raise ValueError("Expected source PDF pages 2 through 24 exactly once")
    source_hash = hashlib.sha256((ROOT / "Policy Manual_USCIS_eb.pdf").read_bytes()).hexdigest()
    if any(p["source_sha256"] != source_hash for p in records):
        raise ValueError("A parsed page comes from a different source snapshot")
    active = None
    segments = []
    starts = {}
    for page in records:
        text = page["markdown"]
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
            raise ValueError("Control characters found in OCR output")
        markers = list(HEADING.finditer(text))
        cursor = 0
        for marker in markers + [None]:
            stop = marker.start() if marker else len(text)
            if active in TITLES and text[cursor:stop].strip():
                footer = page.get("footer") or ""
                printed = re.search(r"\b(\d+)\s*/\s*1737\b", footer)
                segments.append({
                    "document_id": NAMES[active], "chapter": active, "chapter_title": TITLES[active],
                    "source_pdf_page": page["source_pdf_page"],
                    "printed_manual_page": int(printed.group(1)) if printed else None,
                    "source_file": page["source_file"], "source_sha256": source_hash,
                    "snapshot_date": page["snapshot_date"],
                    "source_url": f"https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-{active}",
                    "text": text[cursor:stop].strip(),
                })
            if marker:
                active = int(marker.group(1))
                starts.setdefault(active, page["source_pdf_page"])
                cursor = marker.start()
    if set(starts) != {2, 3, 4}:
        raise ValueError("Could not verify all three chapter boundaries")
    target = ROOT / "data" / "corpus"
    target.mkdir(parents=True, exist_ok=True)
    details = []
    for chapter, title in TITLES.items():
        selected = [s for s in segments if s["chapter"] == chapter]
        body = "\n\n".join(f"<!-- Source PDF page {s['source_pdf_page']} -->\n\n{s['text']}" for s in selected)
        path = target / f"{NAMES[chapter]}.md"
        path.write_text(f"# USCIS Policy Manual: {title}\n\nSource: https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-{chapter}\n\nSnapshot: 2026-09-23 (print date, not effective date). OCR-derived; verify cited text against the PDF.\n\n{body}\n", encoding="utf-8")
        details.append({"document_id": NAMES[chapter], "file": path.name, "chapter": chapter,
                        "source_pdf_pages": sorted({s["source_pdf_page"] for s in selected}),
                        "characters": sum(len(s["text"]) for s in selected)})
    (target / "pages.json").write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {"source_file": "Policy Manual_USCIS_eb.pdf", "source_sha256": source_hash,
                "snapshot_date": "2026-09-23", "chapter_start_pages": starts,
                "documents": details,
                "validation": "Automated page sequence, source hash, control-character and chapter-boundary checks passed. Manual review is recorded separately in docs/SOURCE_AUDIT.md."}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == "__main__":
    main()
