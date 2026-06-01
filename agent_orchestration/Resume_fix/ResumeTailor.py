

import json
import sqlite3
import os
import re
import ollama
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DB_PATH = r"D:\Github\Job_Finding_AI_Agent\job_search.db"
CONTENT_PATH = r"D:\Github\Job_Finding_AI_Agent\Resume_fix\resume_content.json"
TEMPLATE_PATH = r"D:\Github\Job_Finding_AI_Agent\Resume_fix\resume_template.json"
OUTPUT_DIR = r"D:\Github\Job_Finding_AI_Agent\Resume_fix\tailored_output"
OLLAMA_MODEL = "llama3.2"


# ─────────────────────────────────────────────
# Load inputs
# ─────────────────────────────────────────────
def load_resume_content() -> dict:
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_resume_template() -> dict:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_job_from_db(job_id: int) -> dict:
    """Load job info + keywords from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        raise ValueError(f"No job found with id={job_id}")

    keywords = conn.execute(
        "SELECT keyword, category, is_required FROM job_keywords WHERE job_id = ?",
        (job_id,)
    ).fetchall()
    conn.close()

    job_dict = dict(job)
    job_dict["keywords"] = {}
    for kw in keywords:
        cat = kw["category"]
        if cat not in job_dict["keywords"]:
            job_dict["keywords"][cat] = []
        job_dict["keywords"][cat].append(kw["keyword"])

    return job_dict


def list_jobs():
    """Show available jobs to pick from."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, title, company FROM jobs ORDER BY scraped_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# Build prompt for each section
# ─────────────────────────────────────────────
def build_section_prompt(
    section_name: str,
    raw_latex: str,
    job: dict,
) -> str:
    """
    Ask Ollama to rewrite one section of your resume,
    keeping your LaTeX structure but tailoring the content.
    """

    # Flatten keywords into a readable string
    kw_lines = []
    for cat, kw_list in job.get("keywords", {}).items():
        kw_lines.append(f"  {cat}: {', '.join(kw_list)}")
    keywords_str = "\n".join(kw_lines)

    prompt = f"""You are an expert resume writer. You will rewrite ONE section of a LaTeX resume
to better match a target job posting.

RULES:
1. Keep the EXACT same LaTeX commands and structure (\\cventry, \\item, \\textbf, etc.)
2. Do NOT add experience or skills the candidate doesn't have. Only reorganize and reword.
3. Emphasize experiences and skills that match the job keywords.
4. Use stronger action verbs where possible.
5. If the section has bullet points, reorder them so the most relevant ones come first.
6. Keep it concise. Do not make it longer than the original.
7. Output ONLY the rewritten LaTeX code. No explanation, no markdown.

TARGET JOB:
  Title: {job.get('title', 'N/A')}
  Company: {job.get('company', 'N/A')}
  Required education: {job.get('required_education', 'N/A')}
  Required experience: {job.get('required_experience', 'N/A')}
  Preferred experience: {job.get('preferred_experience', 'N/A')}

JOB KEYWORDS TO EMPHASIZE:
{keywords_str}

RESUME SECTION TO REWRITE [{section_name}]:
---
{raw_latex}
---

Rewritten LaTeX (same structure, tailored content):"""

    return prompt


# ─────────────────────────────────────────────
# Tailor each section
# ─────────────────────────────────────────────
def tailor_section(section_name: str, raw_latex: str, job: dict) -> str:
    """Send one section to Ollama, get tailored LaTeX back."""

    # Skip sections that don't need tailoring
    if section_name in ("Career Objective",):
        # Rewrite objective completely for this job
        return tailor_objective(raw_latex, job)

    prompt = build_section_prompt(section_name, raw_latex, job)

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response["message"]["content"].strip()

    # Strip markdown code fences if LLM added them
    content = re.sub(r'^```(?:latex|tex)?\s*\n?', '', content)
    content = re.sub(r'\n?```\s*$', '', content)

    return content


def tailor_objective(raw_latex: str, job: dict) -> str:
    """Rewrite the career objective / wish statement for this specific job."""

    kw_all = []
    for kw_list in job.get("keywords", {}).values():
        kw_all.extend(kw_list)

    prompt = f"""Rewrite this career objective LaTeX section for a {job.get('title', '')} position
at {job.get('company', '')}.

Keep the same LaTeX commands/structure. Make it specific to this role.
Mention relevant keywords naturally: {', '.join(kw_all[:15])}
Output ONLY the LaTeX code.

Original:
---
{raw_latex}
---

Rewritten LaTeX:"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = response["message"]["content"].strip()
    content = re.sub(r'^```(?:latex|tex)?\s*\n?', '', content)
    content = re.sub(r'\n?```\s*$', '', content)
    return content


# ─────────────────────────────────────────────
# Assemble final .tex file
# ─────────────────────────────────────────────
def assemble_tex(template: dict, tailored_sections: dict) -> str:
    main_tex = template.get("main.tex", "")

    if not main_tex:
        parts = []
        for section_name, data in tailored_sections.items():
            parts.append(f"% --- {section_name} ---")
            parts.append(data["latex"])
        return "\n\n".join(parts)

    result = main_tex
    for section_name, data in tailored_sections.items():
        filename = data["filename"]
        bare_name = filename.replace(".tex", "")
        replacement = f"% --- {section_name} (tailored) ---\n{data['latex']}"

        old1 = f"\\input{{{bare_name}}}"
        old2 = f"\\input{{{bare_name}.tex}}"

        if old1 in result:
            result = result.replace(old1, replacement)
        elif old2 in result:
            result = result.replace(old2, replacement)

    return result


# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────
def tailor_resume(job_id: int):
    """Full pipeline: load content + job → tailor each section → output .tex"""

    # Load everything
    print("Loading resume content...")
    content = load_resume_content()

    print("Loading resume template...")
    template = load_resume_template()

    print(f"Loading job id={job_id} from database...")
    job = load_job_from_db(job_id)
    print(f"  Target: {job['title']} @ {job['company']}")

    # Show keywords
    print(f"\n  Keywords to match:")
    for cat, kws in job.get("keywords", {}).items():
        print(f"    {cat}: {', '.join(kws)}")

    # Tailor each section
    print("\nTailoring sections...")
    tailored = {}
    sections = content.get("sections", content)  # handle both formats

    for section_name, section_data in sections.items():
        raw_latex = section_data.get("raw_latex", "")
        filename = section_data.get("filename", f"{section_name}.tex")

        if not raw_latex.strip():
            print(f"  [SKIP] {section_name} (empty)")
            continue

        print(f"  Tailoring: {section_name}...", end=" ", flush=True)
        tailored_latex = tailor_section(section_name, raw_latex, job)
        tailored[section_name] = {
            "filename": filename,
            "latex": tailored_latex,
        }
        print("done")

    # Assemble
    print("\nAssembling final .tex file...")
    final_tex = assemble_tex(template, tailored)

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_company = re.sub(r'[^\w\-]', '_', job.get('company', 'unknown'))
    safe_title = re.sub(r'[^\w\-]', '_', job.get('title', 'unknown'))
    output_filename = f"resume_{safe_company}_{safe_title}.tex"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_tex)

    # Also copy resume.cls to output dir so it compiles
    cls_content = template.get("resume.cls", "")
    if cls_content:
        cls_path = os.path.join(OUTPUT_DIR, "resume.cls")
        if not os.path.exists(cls_path):
            with open(cls_path, "w", encoding="utf-8") as f:
                f.write(cls_content)
            print(f"  Copied resume.cls to output dir")

    print(f"\nOutput: {output_path}")
    print(f"Compile with: cd {OUTPUT_DIR} && pdflatex {output_filename}")

    return output_path


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Resume Tailor")
    print("=" * 50)

    # Show available jobs
    jobs = list_jobs()
    if not jobs:
        print("\nNo jobs in database. Run the scraper first.")
        exit()

    print("\nAvailable jobs:")
    for j in jobs:
        print(f"  [{j['id']}] {j['title']} @ {j['company']}")

    print("\nCommands:")
    print("  Enter a job ID to tailor your resume")
    print("  Type 'quit' to exit")
    print()

    while True:
        user_input = input(">> ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Done.")
            break

        try:
            job_id = int(user_input)
            tailor_resume(job_id)
            print()
        except ValueError:
            print("Enter a job ID number.")
        except Exception as e:
            import traceback
            traceback.print_exc()