"""
JSON → PDF Converter
====================
Reads a tailored_resume_*.json (output of tailor_resume.py),
writes each key as a .tex file into a temp folder,
then compiles main.tex with pdflatex to produce a PDF.

Requirements:
  - MiKTeX or TeX Live installed (pdflatex must be on PATH)
    Windows: https://miktex.org/download
  
Usage:
  python convert_to_pdf.py                          # auto-finds latest tailored JSON
  python convert_to_pdf.py path/to/tailored.json   # specific file
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUTPUT_DIR = Path(r"D:\Github\Job_Finding_AI_Agent\agent_orchestration\Resume_fix\output")


def find_latest_json(output_dir: Path) -> Path:
    """Find the most recently modified tailored_*.json file."""
    files = sorted(output_dir.glob("tailored_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No tailored_*.json found in {output_dir}")
    return files[0]


def json_to_pdf(json_path: Path) -> Path:
    """
    Given a tailored resume JSON, write .tex files and compile to PDF.
    Returns the path to the output PDF.
    """
    with open(json_path, encoding="utf-8") as f:
        resume = json.load(f)

    # Build output PDF name from metadata
    meta = resume.get("_meta", {})
    company = re.sub(r"[^\w]", "_", meta.get("company", "resume"))
    job_id  = meta.get("job_id", "job")
    pdf_name = f"resume_{company}_{job_id}.pdf"

    # Write all .tex and .cls files into a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        for filename, content in resume.items():
            if filename.startswith("_"):
                continue  # skip _meta
            if not isinstance(content, str):
                continue
            filepath = tmp / filename
            filepath.write_text(content, encoding="utf-8")
            print(f"  [write] {filename}")

        # Run pdflatex twice (needed for references/layout to settle)
        main_tex = tmp / "main.tex"
        if not main_tex.exists():
            raise FileNotFoundError("main.tex not found in JSON — check template structure")

        print("\n  [compile] Running pdflatex (pass 1)...")
        _run_pdflatex(main_tex, tmp)

        print("  [compile] Running pdflatex (pass 2)...")
        _run_pdflatex(main_tex, tmp)

        # Copy PDF out of temp dir to output folder
        compiled_pdf = tmp / "main.pdf"
        if not compiled_pdf.exists():
            raise RuntimeError("pdflatex ran but main.pdf was not produced. Check LaTeX errors above.")

        output_dir = json_path.parent
        final_pdf = output_dir / pdf_name
        shutil.copy2(compiled_pdf, final_pdf)

    return final_pdf


def _run_pdflatex(main_tex: Path, workdir: Path):
    """Run pdflatex, streaming output. Raises on failure."""
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-output-directory", str(workdir),
        str(main_tex)
    ]
    result = subprocess.run(cmd, cwd=workdir, capture_output=False)
    if result.returncode != 0:
        log = workdir / "main.log"
        if log.exists():
            # Print last 40 lines of log for debugging
            lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
            print("\n--- LaTeX log (last 40 lines) ---")
            print("\n".join(lines[-40:]))
            print("---------------------------------")
        raise RuntimeError(f"pdflatex failed with return code {result.returncode}")


def main():
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        print(f"[auto] Looking for latest tailored JSON in {OUTPUT_DIR}...")
        json_path = find_latest_json(OUTPUT_DIR)

    print(f"\n[1/2] Reading: {json_path.name}")
    pdf_path = json_to_pdf(json_path)

    print(f"\n{'='*60}")
    print(f"✅ PDF saved to:")
    print(f"   {pdf_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()