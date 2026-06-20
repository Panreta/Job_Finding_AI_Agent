"""
Resume Tailoring Agent
======================
Reads:
  - jobs.csv                  → first row (row 0) for job description
  - resume_content.json       → your full resume content
  - resume_template.json      → output file structure (tex files)

Uses Ollama (llama3.2) to tailor each section to the job.

Outputs:
  - tailored_resume_<company>_<job_id>.json  (same structure as resume_template.json)
"""

import csv
import json
import re
import sys
from pathlib import Path
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# ── Config ────────────────────────────────────────────────────────────────────
JOBS_CSV       = Path(r"D:\Github\Job_Finding_AI_Agent\jobs.csv")
CONTENT_JSON   = Path(r"D:\Github\Job_Finding_AI_Agent\agent_orchestration\Resume_fix\resume_content.json")
TEMPLATE_JSON  = Path(r"D:\Github\Job_Finding_AI_Agent\agent_orchestration\Resume_fix\resume_template.json")
OUTPUT_DIR     = Path(r"D:\Github\Job_Finding_AI_Agent\agent_orchestration\Resume_fix\output")
OLLAMA_MODEL   = "llama3.2"
# ─────────────────────────────────────────────────────────────────────────────


def load_job(csv_path: Path) -> dict:
    """Read first data row from jobs.csv and return as dict."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return next(reader)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_job_summary(job: dict) -> str:
    """Build a readable job description string from CSV fields."""
    parts = []
    for field in ["title", "company", "location", "job_type", "description",
                  "company_description", "job_description"]:
        val = job.get(field, "")
        if val and str(val).strip() not in ("", "NaN", "nan"):
            parts.append(f"{field.upper()}: {val.strip()}")
    return "\n".join(parts)


# ── LLM Prompts ───────────────────────────────────────────────────────────────

SECTION_PROMPT = PromptTemplate(
    input_variables=["section_name", "original_content", "job_summary"],
    template="""You are an expert resume writer. Tailor the resume section below to better match the job.

RULES:
- Keep ALL facts truthful — never invent experience or metrics
- Mirror keywords from the job naturally
- Keep the EXACT same LaTeX formatting and structure
- Only reword/reorder bullets to emphasize relevant skills
- Output ONLY the updated raw_latex string content, nothing else — no explanation, no markdown

SECTION: {section_name}

ORIGINAL LATEX:
{original_content}

JOB:
{job_summary}

TAILORED LATEX:"""
)

SKILLS_PROMPT = PromptTemplate(
    input_variables=["original_skills_latex", "job_summary"],
    template="""You are an expert resume writer. Reorder and emphasize skills to match the job below.

RULES:
- Do NOT add skills the candidate does not have
- Put the most relevant skills first within each category
- Keep exact LaTeX formatting
- Output ONLY the updated raw_latex string, nothing else

ORIGINAL SKILLS LATEX:
{original_skills_latex}

JOB:
{job_summary}

TAILORED SKILLS LATEX:"""
)


def tailor_section(llm, section_name: str, raw_latex: str, job_summary: str) -> str:
    if section_name == "skills":
        chain = SKILLS_PROMPT | llm
        result = chain.invoke({
            "original_skills_latex": raw_latex,
            "job_summary": job_summary
        })
    else:
        chain = SECTION_PROMPT | llm
        result = chain.invoke({
            "section_name": section_name,
            "original_content": raw_latex,
            "job_summary": job_summary
        })
    return result.strip()


def inject_tailored_latex_into_template(template: dict, tailored_sections: dict) -> dict:
    """
    Rebuild the template JSON replacing each \\input{section} file's content
    with the tailored LaTeX from resume_content sections.

    template structure: { "main.tex": "...", "resume.cls": "...", 
                          "background.tex": "...", "skills.tex": "...", etc. }
    
    The mapping from template keys → content sections:
      background.tex  → education
      skills.tex      → skills  
      research.tex    → research
      projects.tex    → projects
      publication.tex → publications
    """
    SECTION_MAP = {
        "background.tex":   "education",
        "skills.tex":       "skills",
        "research.tex":     "research",
        "projects.tex":     "projects",
        "publication.tex":  "publications",
        "internship.tex":   "work_experience",
    }

    output = dict(template)  # copy all keys (main.tex, resume.cls stay unchanged)

    for tex_file, section_key in SECTION_MAP.items():
        if section_key in tailored_sections:
            output[tex_file] = tailored_sections[section_key]
            print(f"  [✓] {tex_file} ← {section_key}")
        else:
            # Keep original from template if exists, or skip
            if tex_file not in output:
                print(f"  [!] {tex_file} — no content found, skipping")

    return output


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Resume Tailoring Agent")
    print("=" * 60)

    # Load inputs
    print("\n[1/4] Loading inputs...")
    job      = load_job(JOBS_CSV)
    content  = load_json(CONTENT_JSON)
    template = load_json(TEMPLATE_JSON)

    company  = re.sub(r"[^\w]", "_", job.get("company", "company"))
    job_id   = job.get("id", "job")
    title    = job.get("title", "")
    print(f"      Job: {title} @ {job.get('company')} [{job_id}]")

    job_summary = build_job_summary(job)

    # Init LLM
    print(f"\n[2/4] Connecting to Ollama ({OLLAMA_MODEL})...")
    llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.3)

    # Tailor each section
    print("\n[3/4] Tailoring sections...")
    tailored_sections = {}

    # Sections to tailor with LLM
    SECTIONS_TO_TAILOR = ["research", "projects", "skills", "education", "publications"]

    for section_name in SECTIONS_TO_TAILOR:
        if section_name not in content:
            print(f"  [!] '{section_name}' not found in resume_content.json, skipping")
            continue

        raw_latex = content[section_name].get("raw_latex", "")
        if not raw_latex.strip():
            print(f"  [!] '{section_name}' has empty raw_latex, skipping")
            continue

        print(f"  [...] Tailoring: {section_name}")
        tailored_latex = tailor_section(llm, section_name, raw_latex, job_summary)
        tailored_sections[section_name] = tailored_latex
        print(f"{section_name} done")

    # Work experience — copy as-is (no tailoring needed for dated internship)
    if "work_experience" in content:
        tailored_sections["work_experience"] = content["work_experience"].get("raw_latex", "")

    # Build output JSON
    print("\n[4/4] Building output JSON...")
    output_json = inject_tailored_latex_into_template(template, tailored_sections)

    # Add metadata
    output_json["_meta"] = {
        "job_id":    job_id,
        "company":   job.get("company", ""),
        "title":     title,
        "location":  job.get("location", ""),
        "job_url":   job.get("job_url", ""),
        "tailored_sections": list(tailored_sections.keys()),
    }

    # Save
    output_path = OUTPUT_DIR / f"tailored_{company}_{job_id}.json"
    save_json(output_json, output_path)

    print(f"\n{'='*60}")
    print(f"Done! Output saved to:")
    print(f"   {output_path}")
    print(f"{'='*60}")
    print("\nNext step: run convert_to_pdf.py to compile the LaTeX into a PDF.")


if __name__ == "__main__":
    main()