# Source preparation report

Prepared September 23, 2026. This report concerns the source corpus; subsequent application results are recorded in the Week 2 and Week 3 evaluation reports.

## Source and scope

- Original: `Policy Manual_USCIS_eb.pdf`, 105 pages, preserved without modification.
- SHA-256: `cb8814dfed0d855edeac8f6bf160d9d686f2dddaf67fbecf73285e561db1143d`.
- Snapshot date: September 23, 2026, from the printed document. This is not a policy effective date or a claim that all provisions remain current.
- Selected source PDF pages: 2 through 24 inclusive, 23 unique pages.
- EB-1A: Volume 6, Part F, Chapter 2, beginning on source page 2 and ending on page 15.
- EB-1B: Volume 6, Part F, Chapter 3, beginning on source page 15 and ending on page 24.
- Material before Chapter 2 and from Chapter 4 onward was removed from the final corpus. Page 15 contributes text to both selected chapters.

Canonical chapter references: [Extraordinary Ability](https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-2) and [Outstanding Professor or Researcher](https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-3). The supplied PDF is the source used for this preparation; the live pages were not substituted for it.

## Parsing and usage

Direct extraction with two PDF readers produced garbled characters. Selected pages were rotated upright and rendered into image-only derivative PDFs for OCR. LlamaParse used the agentic tier, version `2026-09-13`, with English OCR and instructions to preserve headings, tables and footnotes.

Both parse jobs completed: one pilot page used 10 credits and the remaining 22 pages used 220 credits. Total actual usage was 230 credits. The subsequent LlamaCloud balance check returned 40,000 academy credits plus 9,770 free-plan credits, totaling 49,770. Balances can change with subsequent usage.

The local cache contains the completed results, so corpus rebuilding does not require another paid parse. Raw cloud responses are ignored by Git because they can contain private job metadata or temporary download links.

## Checks performed

- All 23 requested pages returned successfully, once each, in the expected sequence.
- Parsed source hashes match the unchanged original PDF.
- Chapter starts were detected at source pages 2, 15 and 24; adjacent chapter text was excluded.
- The resulting chapter text contains all ten EB-1A criterion numbers and all six EB-1B criterion numbers.
- No unreadable markers or disallowed control characters were found in the selected text.
- Visual checks covered the pilot page, the chapter transition on page 15, EB-1B criterion text on page 19, and the final chapter boundary/footnotes on page 24. Page 19's judging and research-contribution text, lists and footnote markers were compared against the rendered original.
- The three preparation scripts passed Python compilation checks.

These checks establish a usable initial corpus, not a word-by-word certification of OCR accuracy. Tables are represented using Markdown or HTML, and superscript formatting varies. Verify the passages used as gold evaluation evidence and any questionable numbers or footnotes against the original PDF.

## Outputs and next work

- `data/corpus/eb1a.md`: Chapter 2 with source PDF page markers.
- `data/corpus/eb1b.md`: Chapter 3 with source PDF page markers.
- `data/corpus/pages.json`: chapter/page text segments with source URLs, source hash, snapshot date and printed manual page references where parsed.
- `data/corpus/manifest.json`: reproducible corpus inventory and automated validation summary.

The subsequent build uses these outputs for both app milestones. See `WEEK2_EVALUATION.md`, `WEEK3_EVALUATION.md`, and `PROJECT_PLAN.md`.
