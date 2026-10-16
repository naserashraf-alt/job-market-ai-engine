import requests
import json
import re
import os
import sys
import time
from bs4 import BeautifulSoup

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Include src in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.classifier import SeniorityClassifier

def clean_html(text: str) -> str:
    """Removes HTML tags and normalizes whitespace."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'&[a-zA-Z0-9#]+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def fetch_linkedin_egypt_jobs(limit_per_keyword: int = 15) -> list:
    """
    Fetches live LinkedIn jobs across all tech fields and experience levels in Egypt.
    """
    keywords = [
        # Juniors & Interns & Fresh Grads
        "Junior Software Engineer", "Junior Frontend Developer", "Junior Backend Developer",
        "Junior Mobile Developer", "Junior Data Analyst", "Junior QA Engineer",
        "Software Engineer Intern", "Fresh Graduate Developer",
        # Mid-level & General
        "Software Engineer", "Full Stack Developer", "Backend Developer", "Frontend Developer",
        "Data Engineer", "Data Scientist", "Machine Learning Engineer",
        "Flutter Developer", "Android Developer", "iOS Developer",
        "DevOps Engineer", "Cloud Engineer", "Cybersecurity Specialist", "QA Automation Engineer",
        ".NET Developer", "Java Developer", "Python Developer", "Node.js Developer",
        # Senior & Leads
        "Senior Software Engineer", "Senior Backend Developer", "Senior Frontend Developer",
        "Senior DevOps Engineer", "Senior Data Scientist", "Technical Lead", "Software Architect"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
    }
    
    all_jobs = []
    seen_ids = set()
    
    print("[1/5] Fetching live LinkedIn jobs in Egypt across ALL seniority levels...")
    
    for kw in keywords:
        search_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(kw)}&location=Egypt&start=0"
        
        try:
            res = requests.get(search_url, headers=headers, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                job_cards = soup.find_all("li")
                
                added_for_kw = 0
                for card in job_cards:
                    link_elem = card.find("a", class_="base-card__full-link")
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    
                    if link_elem and title_elem:
                        job_url = link_elem.get("href", "").split("?")[0]
                        job_id_match = re.search(r'-(\d+)$', job_url) or re.search(r'/view/(\d+)', job_url)
                        
                        job_id = f"linkedin_eg_{job_id_match.group(1)}" if job_id_match else f"linkedin_eg_{hash(job_url)}"
                            
                        if job_id not in seen_ids:
                            seen_ids.add(job_id)
                            
                            title = title_elem.text.strip()
                            company = company_elem.text.strip() if company_elem else "N/A"
                            location = location_elem.text.strip() if location_elem else "Egypt"
                            
                            detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id_match.group(1)}" if job_id_match else job_url
                            raw_desc = ""
                            try:
                                detail_res = requests.get(detail_url, headers=headers, timeout=8)
                                if detail_res.status_code == 200:
                                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                                    desc_elem = detail_soup.find("div", class_="show-more-less-html__markup") or detail_soup.find("section", class_="description")
                                    if desc_elem:
                                        raw_desc = desc_elem.text.strip()
                                time.sleep(0.1)
                            except Exception:
                                pass
                                
                            if not raw_desc:
                                raw_desc = f"{title} role at {company} in {location}. Full description available at source URL."
                                
                            cleaned_desc = clean_html(raw_desc)
                            exp_level = SeniorityClassifier.classify_job_level(title, cleaned_desc)
                            
                            all_jobs.append({
                                "job_id": job_id,
                                "title": title,
                                "company": company,
                                "location": location,
                                "category": kw,
                                "experience_level": exp_level,
                                "original_description": raw_desc,
                                "cleaned_description": cleaned_desc,
                                "job_type": "Full-time",
                                "source_url": job_url,
                                "source_api": "LinkedIn (Egypt)",
                                "country": "Egypt"
                            })
                            added_for_kw += 1
                            if added_for_kw >= limit_per_keyword:
                                break
                                
                print(f"  ├ LinkedIn Egypt ['{kw}']: {added_for_kw} jobs.")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ├ [WARNING] LinkedIn error for '{kw}': {e}")
            
    print(f"✅ Total LinkedIn Egypt jobs fetched: {len(all_jobs)}")
    return all_jobs

def fetch_jobicy_jobs(count: int = 50) -> list:
    """Fetch live remote jobs with explicit seniority levels from Jobicy API."""
    all_jobs = []
    seen_ids = set()
    print(f"\n[2/5] Fetching live tech jobs from Jobicy API...")
    
    industries = ["engineering", "data-science", "devops", "design-multimedia", "qa", "product"]
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for ind in industries:
        url = f"https://jobicy.com/api/v2/remote-jobs?count={count}&industry={ind}"
        try:
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                jobs = data.get("jobs", [])
                added = 0
                for job in jobs:
                    job_id = f"jobicy_{job.get('id')}"
                    if job_id not in seen_ids:
                        seen_ids.add(job_id)
                        title = job.get("jobTitle", "").strip()
                        raw_desc = job.get("jobDescription", "") or job.get("jobExcerpt", "")
                        level_hint = job.get("jobLevel", "")
                        
                        cleaned_desc = clean_html(raw_desc)
                        exp_level = SeniorityClassifier.classify_job_level(title, cleaned_desc, level_hint)
                        
                        all_jobs.append({
                            "job_id": job_id,
                            "title": title,
                            "company": job.get("companyName", "Tech Company").strip(),
                            "location": job.get("jobGeo", "Remote"),
                            "category": ind,
                            "experience_level": exp_level,
                            "original_description": raw_desc,
                            "cleaned_description": cleaned_desc,
                            "job_type": job.get("jobType", "Full-time"),
                            "source_url": job.get("url", ""),
                            "source_api": "Jobicy",
                            "country": "Global Remote"
                        })
                        added += 1
                print(f"  ├ Jobicy ['{ind}']: {added} jobs.")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ├ [WARNING] Jobicy error for '{ind}': {e}")
            
    print(f"✅ Total jobs fetched from Jobicy: {len(all_jobs)}")
    return all_jobs

def fetch_remoteok_jobs() -> list:
    """Fetch live remote developer, data, devops jobs from RemoteOK API."""
    all_jobs = []
    seen_ids = set()
    print(f"\n[3/5] Fetching live tech jobs from RemoteOK API...")
    
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "CareerMatchingEngine/2.0 (student project)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            # First item in RemoteOK is a legal disclaimer object
            for job in items[1:]:
                job_id = f"remoteok_{job.get('id') or job.get('slug')}"
                if job_id not in seen_ids:
                    seen_ids.add(job_id)
                    title = job.get("position", "").strip()
                    if not title:
                        continue
                    raw_desc = job.get("description", "")
                    tags = ", ".join(job.get("tags", []))
                    full_text = f"{raw_desc} Key Skills: {tags}"
                    cleaned_desc = clean_html(full_text)
                    
                    exp_level = SeniorityClassifier.classify_job_level(title, cleaned_desc)
                    
                    all_jobs.append({
                        "job_id": job_id,
                        "title": title,
                        "company": job.get("company", "Remote Tech").strip(),
                        "location": job.get("location", "Remote"),
                        "category": "Tech & Engineering",
                        "experience_level": exp_level,
                        "original_description": raw_desc,
                        "cleaned_description": cleaned_desc,
                        "job_type": "Full-time",
                        "source_url": job.get("url", f"https://remoteok.com/remote-jobs/{job.get('slug', '')}"),
                        "source_api": "RemoteOK",
                        "country": "Global Remote"
                    })
            print(f"  ├ RemoteOK fetched {len(all_jobs)} jobs.")
    except Exception as e:
        print(f"  ├ [WARNING] RemoteOK error: {e}")
        
    print(f"✅ Total jobs fetched from RemoteOK: {len(all_jobs)}")
    return all_jobs

def fetch_remotive_jobs() -> list:
    """Fetch live jobs across multiple tech categories from Remotive API."""
    categories = ["software-dev", "data", "devops-sysadmin", "qa", "design", "product"]
    all_jobs = []
    seen_ids = set()
    
    print("\n[4/5] Fetching live jobs from Remotive API (Global Tech)...")
    
    for category in categories:
        url = f"https://remotive.com/api/remote-jobs?category={category}"
        try:
            response = requests.get(url, timeout=12)
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                
                added = 0
                for job in jobs:
                    job_id = f"remotive_{job.get('id')}"
                    if job_id not in seen_ids:
                        seen_ids.add(job_id)
                        title = job.get("title", "").strip()
                        raw_desc = job.get("description", "")
                        cleaned_desc = clean_html(raw_desc)
                        exp_level = SeniorityClassifier.classify_job_level(title, cleaned_desc)
                        
                        all_jobs.append({
                            "job_id": job_id,
                            "title": title,
                            "company": job.get("company_name", "").strip(),
                            "location": job.get("candidate_required_location", "Remote"),
                            "category": category,
                            "experience_level": exp_level,
                            "original_description": raw_desc,
                            "cleaned_description": cleaned_desc,
                            "job_type": job.get("job_type", "Full-time"),
                            "source_url": job.get("url", ""),
                            "source_api": "Remotive",
                            "country": "Global Remote"
                        })
                        added += 1
                print(f"  ├ Remotive ['{category}']: {added} jobs.")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ├ [WARNING] Remotive error for '{category}': {e}")
            
    print(f"✅ Total jobs fetched from Remotive: {len(all_jobs)}")
    return all_jobs

def fetch_arbeitnow_jobs(pages: int = 8) -> list:
    """Fetch live tech jobs from Arbeitnow Global API."""
    all_jobs = []
    seen_ids = set()
    
    print(f"\n[5/5] Fetching live tech jobs from Arbeitnow API ({pages} pages)...")
    
    for page in range(1, pages + 1):
        url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
        try:
            response = requests.get(url, timeout=12)
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("data", [])
                if not jobs:
                    break
                
                added = 0
                for job in jobs:
                    job_slug = job.get("slug", "")
                    job_id = f"arbeitnow_{job_slug}"
                    if job_id not in seen_ids and job_slug:
                        seen_ids.add(job_id)
                        title = job.get("title", "").strip()
                        raw_desc = job.get("description", "")
                        tags = ", ".join(job.get("tags", []))
                        full_desc = f"{raw_desc} Key Skills & Tags: {tags}" if tags else raw_desc
                        cleaned_desc = clean_html(full_desc)
                        exp_level = SeniorityClassifier.classify_job_level(title, cleaned_desc)
                        
                        all_jobs.append({
                            "job_id": job_id,
                            "title": title,
                            "company": job.get("company_name", "").strip(),
                            "location": "Remote" if job.get("remote") else job.get("location", "Global"),
                            "category": "Tech & Engineering",
                            "experience_level": exp_level,
                            "original_description": raw_desc,
                            "cleaned_description": cleaned_desc,
                            "job_type": ", ".join(job.get("job_types", [])) or "Full-time",
                            "source_url": job.get("url", ""),
                            "source_api": "Arbeitnow",
                            "country": "Global / Remote"
                        })
                        added += 1
                print(f"  ├ Arbeitnow [Page {page}/{pages}]: {added} jobs.")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ├ [WARNING] Arbeitnow page {page}: {e}")
            
    print(f"✅ Total jobs fetched from Arbeitnow: {len(all_jobs)}")
    return all_jobs

def load_and_upgrade_existing_jobs(file_path: str) -> list:
    """Loads existing jobs and ensures each has experience_level classified."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        for j in jobs:
            if "experience_level" not in j or not j["experience_level"]:
                j["experience_level"] = SeniorityClassifier.classify_job_level(
                    j.get("title", ""), j.get("cleaned_description", "")
                )
        return jobs
    except Exception:
        return []

def deduplicate_jobs(jobs_list: list) -> list:
    """Deduplicates jobs based on normalized Title + Company."""
    unique_jobs = []
    seen = set()
    
    for job in jobs_list:
        key = f"{job['title'].lower()}|{job['company'].lower()}"
        if key not in seen:
            seen.add(key)
            # Ensure experience_level is present
            if "experience_level" not in job:
                job["experience_level"] = SeniorityClassifier.classify_job_level(
                    job.get("title", ""), job.get("cleaned_description", "")
                )
            unique_jobs.append(job)
            
    return unique_jobs

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 5-SOURCE EXPANDED JOB COLLECTOR & SENIORITY CLASSIFIER")
    print("   [LinkedIn Egypt + Jobicy + RemoteOK + Remotive + Arbeitnow]")
    print("=" * 70)
    
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "jobs_dataset.json")
    
    # 1. Load existing jobs & upgrade with seniority classification
    existing_jobs = load_and_upgrade_existing_jobs(output_file)
    print(f"Loaded {len(existing_jobs)} existing jobs.\n")
    
    # 2. Fetch from all 5 sources
    linkedin_jobs = fetch_linkedin_egypt_jobs(limit_per_keyword=15)
    jobicy_jobs = fetch_jobicy_jobs(count=50)
    remoteok_jobs = fetch_remoteok_jobs()
    remotive_jobs = fetch_remotive_jobs()
    arbeitnow_jobs = fetch_arbeitnow_jobs(pages=6)
    
    # 3. Combine & Deduplicate
    all_combined = existing_jobs + linkedin_jobs + jobicy_jobs + remoteok_jobs + remotive_jobs + arbeitnow_jobs
    final_jobs = deduplicate_jobs(all_combined)
    
    # 4. Generate Level & Geographic Breakdown Stats
    level_counts = {}
    egypt_count = 0
    for j in final_jobs:
        lvl = j.get("experience_level", "Mid-Level")
        level_counts[lvl] = level_counts.get(lvl, 0) + 1
        if "Egypt" in j.get("location", "") or j.get("country") == "Egypt":
            egypt_count += 1
            
    print("\n" + "=" * 70)
    print(f"📊 DATASET COLLECTION & CLASSIFICATION REPORT:")
    print(f"  ├ Total Unique Active Jobs: {len(final_jobs)}")
    print(f"  ├ Jobs Located in Egypt 🇪🇬: {egypt_count}")
    print(f"  ├ Global & Remote Tech Jobs 🌐: {len(final_jobs) - egypt_count}")
    print("  │")
    print("  └ 🎯 Experience Level Breakdown:")
    for lvl, count in sorted(level_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(final_jobs)) * 100
        print(f"      • {lvl:<28} : {count:>4} jobs ({pct:.1f}%)")
    print("=" * 70)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_jobs, f, ensure_ascii=False, indent=4)
        
    print(f"\n[SUCCESS] Dataset saved to: {output_file}\n")
