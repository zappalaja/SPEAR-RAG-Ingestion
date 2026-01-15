#!/usr/bin/env python3
"""Merge Nougat outputs into cleaned Markdown.

- Finds Nougat-produced markdown-like files under NOUGAT_OUT_DIR.
- For each source PDF, chooses the best matching markdown file (largest).
- Applies boilerplate filtering ONCE (so RAG stage stays clean).
- Writes cleaned .md files into MERGED_MD_DIR.

Usage:
  python merge_nougat_md.py --pdf_dir INPUT_PDF_DIR --nougat_out NOUGAT_OUT_DIR --merged_out MERGED_MD_DIR
"""

import argparse, hashlib, json, re
from pathlib import Path

BOILERPLATE_PATTERNS = [
    r"^references\s*$",
    r"^acknowledg(e)?ments\s*$",
    r"copyright\s*©",
    r"all\s+rights\s+reserved",
    r"published\s+by",
    r"\bdoi:\s*",
]

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def clean_text(text: str) -> str:
    out_lines = []
    for line in text.splitlines():
        if any(re.search(pat, line, flags=re.IGNORECASE) for pat in BOILERPLATE_PATTERNS):
            continue
        out_lines.append(line.rstrip())
    cleaned = "\n".join(out_lines)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned.strip() + "\n"

def safe_name(stem: str) -> str:
    stem = re.sub(r"[\\/:*?\"<>|]", "_", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem[:180] if len(stem) > 180 else stem

def find_best_md(nougat_out: Path, pdf_stem: str) -> Path | None:
    candidates = []
    for ext in ("*.mmd", "*.md", "*.markdown", "*.txt"):
        for p in nougat_out.rglob(ext):
            if pdf_stem.lower() in p.stem.lower():
                candidates.append(p)
    if not candidates:
        for d in nougat_out.rglob("*"):
            if d.is_dir() and pdf_stem.lower() in d.name.lower():
                for ext in ("*.mmd", "*.md", "*.markdown", "*.txt"):
                    candidates.extend(list(d.rglob(ext)))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf_dir", required=True)
    ap.add_argument("--nougat_out", required=True)
    ap.add_argument("--merged_out", required=True)
    args = ap.parse_args()

    pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    nougat_out = Path(args.nougat_out).expanduser().resolve()
    merged_out = Path(args.merged_out).expanduser().resolve()
    merged_out.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    pdf_hashes = {}
    manifest = []

    for pdf in pdfs:
        pdf_hash = sha256_file(pdf)
        pdf_hashes[pdf.name] = pdf_hash

        best_md = find_best_md(nougat_out, pdf.stem)
        if best_md is None:
            manifest.append({
                "pdf": pdf.name,
                "pdf_sha256": pdf_hash,
                "status": "missing_md",
                "nougat_md": None,
                "merged_md": None
            })
            continue

        text = best_md.read_text(errors="ignore")
        cleaned = clean_text(text)

        out_name = safe_name(pdf.stem) + ".md"
        out_path = merged_out / out_name
        out_path.write_text(cleaned, encoding="utf-8")

        manifest.append({
            "pdf": pdf.name,
            "pdf_sha256": pdf_hash,
            "status": "ok",
            "nougat_md": str(best_md),
            "merged_md": str(out_path),
        })

    (merged_out / "pdf_sha256.json").write_text(json.dumps(pdf_hashes, indent=2), encoding="utf-8")
    (merged_out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    ok = sum(1 for m in manifest if m["status"] == "ok")
    missing = len(manifest) - ok
    print(f"Merged+cleaned markdown: ok={ok}, missing={missing}")
    print(f"Wrote: {merged_out/'pdf_sha256.json'}")
    print(f"Wrote: {merged_out/'manifest.json'}")

if __name__ == "__main__":
    main()
