"""
Resume Storage: .tex files -> 2 JSON files
==========================================
Produces:
  1. resume_template.json  -> LaTeX skeleton (main.tex + resume.cls) with placeholders
  2. resume_content.json   -> Your actual experience, structured by category

Later, your pipeline does:
  template + selected content + job requirements -> Ollama -> new tailored .tex
  
pip install pylatexenc
"""

import re
import json
from pathlib import Path
from pylatexenc.latex2text import LatexNodes2Text

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
RESUME_DIR = Path(r"D:\Github\Job_Finding_AI_Agent\agent_orchestration\Resume_fix\CV\CV__AI_INFRA")
OUTPUT_DIR = Path(r"D:\Github\Job_Finding_AI_Agent\agent_orchestration\Resume_fix")

# What each file contains
CONTENT_FILES = {
    "background.tex":   "education",
    "internship.tex":   "work_experience",
    "projects.tex":     "projects",
    "publication.tex":  "publications",
    "research.tex":     "research",
    "skills.tex":       "skills",
}

TEMPLATE_FILES = ["main.tex", "resume.cls"]


# ─────────────────────────────────────────────
# LaTeX Cleaner
# ─────────────────────────────────────────────
def latex_to_text(latex: str):
    """Convert LaTeX -> readable text, handling resume-specific patterns."""
    try:
        text = LatexNodes2Text().latex_to_text(latex)
    except Exception:
        text = latex

    # Extra cleanup
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_items(latex: str):
    """
    Try to extract individual items (jobs, degrees, projects)
    from a LaTeX section. Splits on common resume entry patterns.
    
    This helps the LLM understand each experience as a separate unit.
    """
    # Try splitting on common resume entry commands
    # Adjust these patterns based on what your .cls uses
    patterns = [
        r'\\(?:cventry|entry|experience|position|education)\b',
        r'\\(?:item|resumeItem|project)\b',
        r'\\textbf\{[^}]+\}.*?(?=\\textbf\{|$)',
    ]

    for pattern in patterns:
        splits = re.split(f'(?={pattern})', latex)
        splits = [s.strip() for s in splits if s.strip() and len(s.strip()) > 20]
        if len(splits) > 1:
            return [latex_to_text(s) for s in splits]

    # Fallback: split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', latex)
    paragraphs = [latex_to_text(p) for p in paragraphs if p.strip() and len(p.strip()) > 20]

    if len(paragraphs) > 1:
        return paragraphs

    # Last resort: return as one block
    return [latex_to_text(latex)]


# ─────────────────────────────────────────────
# Main Extraction
# ─────────────────────────────────────────────
def extract_resume():
    """Read .tex files -> produce template.json + content.json"""

    print(f"Reading from: {RESUME_DIR}\n")

    # ── 1. Template ──
    template = {}
    for fname in TEMPLATE_FILES:
        fpath = RESUME_DIR / fname
        if fpath.exists():
            template[fname] = fpath.read_text(encoding="utf-8")
            print(f"{fname} (template)")

    template_out = OUTPUT_DIR / "resume_template.json"
    with open(template_out, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    print(f"\nTemplate -> {template_out}")

    # ── 2. Content ──
    content = {}
    for fname, category in CONTENT_FILES.items():
        fpath = RESUME_DIR / fname
        if not fpath.exists():
            print(f"{fname} not found, skipping")
            continue

        raw = fpath.read_text(encoding="utf-8")
        items = extract_items(raw)

        content[category] = {
            "raw_latex": raw,
            "items": items,                      # individual entries
            "full_text": latex_to_text(raw),     # entire section as text
        }
        print(f"{fname:20s} -> {category:20s} ({len(items)} items)")

    content_out = OUTPUT_DIR / "resume_content.json"
    with open(content_out, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    print(f"\n Content  -> {content_out}")

    # ── 3. Preview ──
    print("\n" + "=" * 60)
    print("  YOUR RESUME CONTENT (preview)")
    print("=" * 60)
    for category, data in content.items():
        print(f"\n {category.upper()} ({len(data['items'])} items)")
        print("-" * 40)
        for i, item in enumerate(data["items"], 1):
            preview = item[:150].replace('\n', ' ')
            print(f"  {i}. {preview}{'...' if len(item) > 150 else ''}")

    return template, content


# ─────────────────────────────────────────────
# Helper functions for your pipeline
# ─────────────────────────────────────────────
def load_content():
    """Load resume content from JSON."""
    with open(OUTPUT_DIR / "resume_content.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_template():
    """Load LaTeX template from JSON."""
    with open(OUTPUT_DIR / "resume_template.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_llm_prompt_context():
    """
    Build a clean context string from your resume content.
    Pass this directly into your Ollama prompt.
    
    Usage:
        from resume_store import get_llm_prompt_context, load_template
        
        context = get_llm_prompt_context()
        template = load_template()
        
        prompt = f'''
        Candidate background:
        {context}
        
        LaTeX template (main.tex):
        {template["main.tex"]}
        
        Now tailor for this job: ...
        '''
    """
    content = load_content()

    lines = ["=== CANDIDATE BACKGROUND ===\n"]
    for category, data in content.items():
        lines.append(f"[{category.upper()}]")
        for item in data["items"]:
            lines.append(f"  - {item}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
if __name__ == "__main__":
    extract_resume()

    print("\n" + "=" * 60)
    print("  NEXT STEP USAGE")
    print("=" * 60)
    print("""
Your resume is now stored as:

  resume_template.json   <- main.tex + resume.cls
  resume_content.json    <- all your experience by category

Each category has:
  "raw_latex"  -> original LaTeX (for rebuilding the .tex file)
  "items"      -> individual entries as clean text (for LLM)
  "full_text"  -> entire section as clean text

In your job-tailoring code:

    from resume_store import get_llm_prompt_context, load_template, load_content
    
    # For LLM: your full background as text
    my_background = get_llm_prompt_context()
    
    # For generation: LaTeX template to follow
    template = load_template()
    
    # For selective use: pick specific sections
    content = load_content()
    my_skills = content["skills"]["items"]
    my_research = content["research"]["raw_latex"]  # keep LaTeX for rebuild
""")