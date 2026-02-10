

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
from vector_db import add_job_to_db, verify_job_stored, count_jobs, get_all_jobs,clear_jobs_db

def scrape_first_job_from_github():
    """Scrape first job from GitHub README table"""
    
    driver = webdriver.Edge()
    
    try:
        # Open the GitHub repo
        url = "https://github.com/speedyapply/2026-AI-College-Jobs?tab=readme-ov-file"
        driver.get(url)
        
        time.sleep(3)
        
        # Scroll down to see the table
        driver.execute_script("window.scrollTo(0, 1200);") ## 1200 is my setting about how much to scroll
        time.sleep(2)
        
        # Find the table
        table = driver.find_element(By.CSS_SELECTOR, "article table")#artic
        first_row = table.find_element(By.CSS_SELECTOR, "tbody tr:first-child")
        cells = first_row.find_elements(By.TAG_NAME, "td") #td is the acronym of table data
        
        company = cells[0].text
        position = cells[1].text
        location = cells[2].text
        salary = cells[3].text
        posting = cells[4].text
        age = cells[5].text
        
        apply_button = cells[4].find_element(By.TAG_NAME, "a")
        apply_url = apply_button.get_attribute("href")
        
        job_data = {
            "company": company,
            "position": position,
            "location": location,
            "salary": salary,
            "posting": posting,
            "age": age,
            "apply_url": apply_url
        }
        


        driver.get(apply_url) ## Navigate to the job posting page, like company web
        time.sleep(5)
        
        # Get the JSON script,now driver is the agent of the job posting page
        script_element = driver.find_element(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        script_content = script_element.get_attribute('textContent')#
        
        # Parse JSON
        job_json = json.loads(script_content)#loads returns

        print("\nAvailable JSON keys:")
        print(list(job_json.keys()))
        
        # # Extract ALL fields from JSON
        job_data["description"] = job_json.get('description', 'N/A')
        job_data["responsibilities"] = job_json.get('responsibilities', 'N/A')
        job_data["qualifications"] = job_json.get('qualifications', 'N/A')


        job_data["hiringOrganization"] = job_json.get('hiringOrganization', {}).get('name', 'N/A')
        job_data["employmentType"] = job_json.get('employmentType', 'N/A')
        job_data["datePosted"] = job_json.get('datePosted', 'N/A')

        # Search for span containing salary text
        salary_element = driver.find_element(By.XPATH, "//span[contains(text(), '/month') or contains(text(), '/hour')]")
        detailed_salary = salary_element.text
        job_data["detailed_salary"] = detailed_salary


         # Combine all text for the description field
        full_text = f"""
        {job_data['description']}
        
        Responsibilities: {job_data['responsibilities']}
        
        Qualifications: {job_data['qualifications']}
        """
        
        # Generate unique ID
        job_id = f"{company.replace(' ', '_')}_{int(time.time())}_{apply_url.split('/')[-1]}"
        
        # Add to ChromaDB using your existing function
        add_job_to_db(
            job_id=job_id,
            job_title=position,
            company=company,
            location=location,
            description=full_text,
            url=apply_url
        )

        # Verify storage
        verify_job_stored(job_id)
        print(f"\nTotal jobs in database: {count_jobs()}")

        job_data["job_id"] = job_id
                        
        return job_data
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # # Clear existing jobs in database before running
    clear_jobs_db()
    
    # Run scraper
    job = scrape_first_job_from_github()

    print("\nJob scraped and stored successfully!")

    # Show all jobs
    print("\n" + "="*80)
    print("ALL JOBS IN DATABASE:")
    print("="*80)
    all_jobs = get_all_jobs()
    for i, j in enumerate(all_jobs, 1):
        print(f"{i}. {j['title']} at {j['company']}")
