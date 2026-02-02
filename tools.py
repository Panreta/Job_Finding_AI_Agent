# Tool functions that the agent can call
import json
import os
from datetime import datetime
import pypdf

# Define all available tools
TOOLS = {
    "search_jobs": {
        "description": "Search for jobs by keywords and location",
        "function": lambda kwargs: search_jobs(**kwargs)
    },
    "read_resume": {
        "description": "Read the user's resume from file",
        "function": lambda kwargs: read_resume()
    },
    "save_application": {
        "description": "Save a job application with cover letter",
        "function": lambda kwargs: save_application(**kwargs)
    },
    "list_applications": {
        "description": "List all saved job applications",
        "function": lambda kwargs: list_applications()
    }
}

def execute_tool(tool_name, args):
    """Execute a tool by name with arguments"""
    if tool_name in TOOLS:
        try:
            result = TOOLS[tool_name]["function"](args)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    else:
        return f"Tool '{tool_name}' not found"

# Tool implementations

def search_jobs(keywords="", location=""):
    """Search for jobs (mock data for now)"""
    # TODO: Integrate with real job APIs (Indeed, LinkedIn, etc.)
    mock_jobs = [
        {
            "title": "Software Engineer",
            "company": "TechCorp",
            "location": location or "Seattle",
            "description": "Looking for Python developer with AI experience",
            "url": "https://example.com/job1"
        },
        {
            "title": "Backend Developer",
            "company": "StartupXYZ",
            "location": location or "Remote",
            "description": "Node.js and database experience required",
            "url": "https://example.com/job2"
        }
    ]
    
    return json.dumps(mock_jobs, indent=2)

def read_resume():
    """Read resume from data folder (supports PDF and TXT)"""
  
    
    pdf_path = "D:\\Github\\Job_Finding_AI_Agent\\data\\CV.pdf"
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    
    return "Resume not found. Please add data/resume.pdf or data/resume.txt"

def save_application(job_title="", company="", cover_letter=""):
    """Save a job application"""
    os.makedirs("data/applications", exist_ok=True)
    
    filename = f"data/applications/{company}_{job_title}_{datetime.now().strftime('%Y%m%d')}.txt"
    filename = filename.replace(" ", "_").replace("/", "-")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Job: {job_title}\n")
        f.write(f"Company: {company}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"\n{'='*50}\n\n")
        f.write(cover_letter)
    
    return f"Application saved to {filename}"

def list_applications():
    """List all saved applications"""
    app_dir = "data/applications"
    
    if not os.path.exists(app_dir):
        return "No applications saved yet."
    
    files = os.listdir(app_dir)
    
    if not files:
        return "No applications saved yet."
    
    return "Saved applications:\n" + "\n".join([f"- {f}" for f in files])