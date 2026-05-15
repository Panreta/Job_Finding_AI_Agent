import chromadb
from chromadb.config import Settings

# Method to initial and use ChromaDB
# Initialize ChromaDB client
# client = chromadb.Client(Settings(
#     persist_directory="./data/chroma_db",
#     anonymized_telemetry=False
# ))

client = chromadb.PersistentClient(path="./data/chroma_db")## persistent: save to disk, default is in-memory


# Create or get collections
jobs_collection = client.get_or_create_collection(
    name="jobs",
    metadata={"description": "Job postings collection"}
)

resume_collection = client.get_or_create_collection(
    name="resume",
    metadata={"description": "User resume and skills"}
)

def job_exists(job_id):
    """Check if job already exists in database"""
    try:
        result = jobs_collection.get(ids=[job_id])
        return len(result['ids']) > 0
    except:
        return False

def add_job_to_db(job_id, job_title, company, location, description, url = None):
    """Add a single job to the vector database"""

        # CHECK IF ALREADY EXISTS
    if job_exists(job_id):
        print(f"Job already exists: {job_title} at {company} (ID: {job_id}) - SKIPPED")
        return f"Job already exists: {job_id}"
    
    # Combine text for embedding
    job_text = f"{job_title} at {company}. Location: {location}. {description}"
    
    jobs_collection.add( # doc:explicit data info, metadatas:structural data form
        documents=[job_text],
        metadatas=[{
            "job_title": job_title,
            "company": company,
            "location": location,
            "url": url
        }],
        ids=[job_id]
    )
    
    return f"Added job: {job_title} at {company}"

def add_resume_to_db(resume_text):
    """Add user resume to vector database"""
    resume_collection.add(
        documents=[resume_text],
        metadatas=[{"type": "resume"}],
        ids=["user_resume"]
    )
    
    return "Resume added to vector database"

def search_jobs_by_similarity(query, n_results=5):
    """Search jobs using semantic similarity"""
    results = jobs_collection.query(
        query_texts=[query],
        n_results=n_results
    )
    # n_results determines how many similar jobs to return
    
    # Format results just give out a format way to show, but the results are determined
    jobs = []
    if results['ids'] and len(results['ids'][0]) > 0:
        for i in range(len(results['ids'][0])):
            job = {
                "id": results['ids'][0][i],
                "title": results['metadatas'][0][i]['job_title'],
                "company": results['metadatas'][0][i]['company'],
                "location": results['metadatas'][0][i]['location'],
                "url": results['metadatas'][0][i]['url'],
                "similarity_score": 1 - results['distances'][0][i]  # Convert distance to similarity
            }
            jobs.append(job)
    
    return jobs

def match_resume_to_jobs(n_results=5):
    """Find jobs that match user's resume"""
    # Get resume from collection
    resume_results = resume_collection.get(ids=["user_resume"])
    
    if not resume_results['documents']:
        return []
    
    resume_text = resume_results['documents'][0]
    
    # Search for matching jobs
    return search_jobs_by_similarity(resume_text, n_results)

def get_all_jobs():
    """Get all jobs from database"""
    all_jobs = jobs_collection.get()
    
    jobs = []
    if all_jobs['ids']:
        for i in range(len(all_jobs['ids'])):
            job = {
                "id": all_jobs['ids'][i],
                "title": all_jobs['metadatas'][i]['job_title'],
                "company": all_jobs['metadatas'][i]['company'],
                "location": all_jobs['metadatas'][i]['location'],
                "url": all_jobs['metadatas'][i]['url']
            }
            jobs.append(job)
    
    return jobs

def clear_jobs_db():
    """Clear all jobs from database"""
    global jobs_collection
    client.delete_collection("jobs")
    jobs_collection = client.get_or_create_collection(name="jobs")
    return "Jobs database cleared"

def get_job_by_id(job_id):
    """Retrieve a specific job by ID"""
    result = jobs_collection.get(ids=[job_id])
    
    if result['ids']:
        return {
            "id": result['ids'][0],
            "document": result['documents'][0],
            "title": result['metadatas'][0]['job_title'],
            "company": result['metadatas'][0]['company'],
            "location": result['metadatas'][0]['location'],
            "url": result['metadatas'][0]['url']
        }
    else:
        return None

def count_jobs():
    """Count total jobs in database"""
    return jobs_collection.count()

def verify_job_stored(job_id):
    """Verify if a job was successfully stored"""
    job = get_job_by_id(job_id)
    if job:
        print("\n" + "="*80)
        print("JOB FOUND IN DATABASE!")
        print("="*80)
        print(f"ID: {job['id']}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")
        print(f"\nDocument (first 300 chars):\n{job['document'][:300]}...")
        print("="*80)
        return True
    else:
        print(f"Job with ID '{job_id}' not found in database")
        return False

def printJobInfo(job):
    if job:
        print("\n" + "="*80)
    print("COMPLETE JOB DATA:")
    print("="*80)
    print(f"Company: {job['company']}")
    print(f"Position: {job['position']}")
    print(f"Location: {job['location']}")
    print(f"Salary: {job['salary']}")
    print(f"Age: {job['age']}")
    print(f"Date Posted: {job.get('datePosted', 'N/A')}")
    print(f"Employment Type: {job.get('employmentType', 'N/A')}")
    print(f"URL: {job['apply_url']}")
    
    print("\n" + "-"*80)
    print("FULL DESCRIPTION (All Sections):")
    print("-"*80)
    print(job['description'])
    
    # If responsibilities and qualifications are separate fields
    if job.get('responsibilities') != 'N/A':
        print("\n" + "-"*80)
        print("RESPONSIBILITIES:")
        print("-"*80)
        print(job.get('responsibilities'))

    if job.get('qualifications') != 'N/A':
        print("\n" + "-"*80)
        print("qualifications:")
        print("-"*80)
        print(job.get('qualifications'))


    if job.get('educationRequirements') != 'N/A':
        print("\n" + "-"*80)
        print("EDUCATION REQUIREMENTS:")
        print("-"*80)
        print(job.get('educationRequirements'))

    if job.get('experienceRequirements') != 'N/A':
        print("\n" + "-"*80)
        print("EXPERIENCE REQUIREMENTS:")
        print("-"*80)
        print(job.get('experienceRequirements'))

    if job.get('skills') != 'N/A':
        print("\n" + "-"*80)
        print("REQUIRED SKILLS:")
        print("-"*80)
        print(job.get('skills'))   #job_data["detailed_salary"] = detailed_salary


    if job.get('detailed_salary') != 'N/A':
        print("\n" + "-"*80)
        print("SALARY INFORMATION:")
        print("-"*80)
        print(job.get('detailed_salary'))

    print("="*80)
