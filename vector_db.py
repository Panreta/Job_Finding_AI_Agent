import chromadb
from chromadb.config import Settings

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

def add_job_to_db(job_id, job_title, company, location, description, url = None):
    """Add a single job to the vector database"""
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

# Test function
if __name__ == "__main__":
    print("Testing ChromaDB setup...")
    
    # Test adding a job
    result = add_job_to_db(
        job_id="Nujades",
        job_title="Python Developer",
        company="TestCorp",
        location="Seattle",
        description="Looking for Python developer with AI experience",
        url="https://example.com/job1"
    )
    print(result)
    
    # Test search
    results = search_jobs_by_similarity("python machine learning", n_results=1)
    print(f"Found {len(results)} jobs")
    print(results)