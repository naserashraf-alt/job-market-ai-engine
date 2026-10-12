import requests
import json
import os
import sys
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Force unbuffered UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def is_job_closed(job: dict, headers: dict) -> tuple[dict, bool]:
    """
    Checks if a job posting is closed or expired.
    Returns (job, is_closed_flag).
    """
    source_api = job.get("source_api", "")
    url = job.get("source_url", "")
    job_id = job.get("job_id", "")
    
    # 1. LinkedIn Job Check
    if "LinkedIn" in source_api or "linkedin" in job_id:
        import re
        id_match = re.search(r'(\d+)', job_id)
        if id_match:
            detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{id_match.group(1)}"
            try:
                res = requests.get(detail_url, headers=headers, timeout=5)
                if res.status_code in [404, 410]:
                    return job, True
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    text = soup.get_text().lower()
                    if "no longer accepting applications" in text or "this job is no longer available" in text:
                        return job, True
            except Exception:
                pass
                
    # 2. General URL HTTP Status Check (Remotive / Arbeitnow / Others)
    if url:
        try:
            res = requests.head(url, headers=headers, timeout=4, allow_redirects=True)
            if res.status_code in [404, 410]:
                return job, True
        except Exception:
            pass
            
    return job, False

def clean_all_closed_jobs(max_workers: int = 15):
    """
    Checks ALL jobs in dataset concurrently, purges closed jobs, and saves updated dataset.
    """
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "jobs_dataset.json")
    
    if not os.path.exists(dataset_path):
        print("❌ Dataset file not found.", flush=True)
        return
        
    with open(dataset_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
        
    total_initial = len(jobs)
    print("=" * 65, flush=True)
    print(f"🧹 Starting FULL Closed Jobs Cleaner for ALL {total_initial} jobs", flush=True)
    print("=" * 65, flush=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    active_jobs = []
    closed_jobs_count = 0
    checked_count = 0
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for fast concurrent HTTP checks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {
            executor.submit(is_job_closed, job, headers): job for job in jobs
        }
        
        for future in as_completed(future_to_job):
            checked_count += 1
            job, closed = future.result()
            
            if closed:
                closed_jobs_count += 1
                title = job.get('title', 'N/A')
                company = job.get('company', 'N/A')
                print(f"  ❌ Purged Closed Job [{checked_count}/{total_initial}]: {title} at {company}", flush=True)
            else:
                active_jobs.append(job)
                
            if checked_count % 250 == 0 or checked_count == total_initial:
                print(f"  ⏳ Progress: Checked {checked_count}/{total_initial} jobs...", flush=True)
                
    elapsed = round(time.time() - start_time, 2)
    
    print("\n" + "=" * 65, flush=True)
    print(f"📊 FULL CLEANING COMPLETE (Time: {elapsed} seconds):", flush=True)
    print(f"  ├ Total Jobs Checked: {total_initial}", flush=True)
    print(f"  ├ Closed / Expired Jobs Purged: {closed_jobs_count}", flush=True)
    print(f"  └ Active Jobs Retained: {len(active_jobs)}", flush=True)
    print("=" * 65, flush=True)
    
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(active_jobs, f, ensure_ascii=False, indent=4)
        
    print(f"[SUCCESS] Cleaned dataset saved to: {dataset_path}", flush=True)

if __name__ == "__main__":
    # Checks ALL jobs in dataset concurrently
    clean_all_closed_jobs(max_workers=15)
