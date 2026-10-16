import json
import os
import sys
import re
from typing import List, Dict

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Import modules from src
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.normalizer import SkillNormalizer
from src.classifier import SeniorityClassifier
from src.extractor import TextExtractor
from src.parser import HybridParser, ParsedCVProfile, ParsedJobProfile
from src.embeddings import SemanticEmbeddingEngine


class MatchingEngine:
    """
    Explainable Ultra-Fast Weighted Matching Engine for CVs vs Job Postings.
    Calculates overall match score %, skill score, experience score, semantic score, and penalties.
    """
    
    def __init__(self, dataset_path: str = None):
        if dataset_path is None:
            dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "jobs_dataset.json")
            
        self.dataset_path = dataset_path
        self.normalizer = SkillNormalizer()
        self.sorted_aliases = sorted(self.normalizer.alias_to_canonical.items(), key=lambda x: len(x[0]), reverse=True)
        self.raw_jobs = self.load_jobs_dataset()

    def load_jobs_dataset(self) -> list:
        """Loads processed active jobs from dataset file."""
        if not os.path.exists(self.dataset_path):
            print(f"[WARNING] Dataset file not found at: {self.dataset_path}")
            return []
            
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def extract_job_skills_fast(self, desc_lower: str) -> List[str]:
        """Fast and accurate skill extraction with regex boundary safety."""
        found = set()
        for alias, canonical in self.sorted_aliases:
            if '#' in alias or '+' in alias or '.' in alias:
                pattern = r'(?:^|\s|,|/)' + re.escape(alias) + r'(?:$|\s|,|/|\.|\b)'
            else:
                pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, desc_lower):
                found.add(canonical)
        return sorted(list(found))

    def match_skills(self, cv_skills: List[str], job_skills: List[str]) -> Dict:
        """Calculates skill compatibility score."""
        cv_set = set(cv_skills)
        job_set = set(job_skills)

        if not job_set:
            return {"score": 70.0, "matched": [], "missing": []}

        matched = cv_set.intersection(job_set)
        missing = job_set - cv_set

        score = (len(matched) / len(job_set)) * 100.0

        return {
            "score": round(score, 2),
            "matched": sorted(list(matched)),
            "missing": sorted(list(missing))
        }

    def match_single_pair(self, parsed_cv: ParsedCVProfile, job_dict: dict) -> Dict:
        """Matches a single CV against a raw Job dictionary."""
        desc = job_dict.get("cleaned_description", "")
        desc_lower = desc.lower()
        title = job_dict.get("title", "Software Role")
        company = job_dict.get("company", "Tech Company")
        location = job_dict.get("location", "Egypt")
        
        # Fast skill extraction
        job_skills = self.extract_job_skills_fast(desc_lower)
        
        # 1. Skill Match Score
        skill_res = self.match_skills(parsed_cv.normalized_skills, job_skills)
        
        # 2. Domain & Title Match Bonus
        title_lower = title.lower()
        domain_match = False
        
        if "data" in title_lower or "ai" in title_lower or "machine learning" in title_lower:
            if "Data" in parsed_cv.detected_domain or "AI" in parsed_cv.detected_domain:
                domain_match = True
        elif "frontend" in title_lower or "react" in title_lower or "web" in title_lower:
            if "Frontend" in parsed_cv.detected_domain or "Full Stack" in parsed_cv.detected_domain:
                domain_match = True
        elif "net" in title_lower or "backend" in title_lower or "c#" in title_lower:
            if "Backend" in parsed_cv.detected_domain or "Full Stack" in parsed_cv.detected_domain:
                domain_match = True
                
        # 3. Fast Overlap & Semantic Score
        overlap_ratio = (len(skill_res["matched"]) / max(1, len(parsed_cv.normalized_skills))) * 100.0
        semantic_score = round(min(98.0, overlap_ratio + (20.0 if domain_match else 0.0)), 1)
        
        # 4. Seniority & Experience Level Compatibility
        job_level = job_dict.get("experience_level") or SeniorityClassifier.classify_job_level(title, desc)
        candidate_level = getattr(parsed_cv, "experience_level", "Mid-Level")
        level_comp = SeniorityClassifier.calculate_level_compatibility(candidate_level, job_level)
        
        exp_score = level_comp["score"]
        edu_score = 95.0
        
        # 5. Weighted Score Calculation
        # Skills (45%) + Level/Experience (25%) + Education (10%) + Semantic (20%)
        weighted_score = (
            (skill_res['score'] * 0.45) +
            (exp_score * 0.25) +
            (edu_score * 0.10) +
            (semantic_score * 0.20)
        )
        
        # Domain Bonus / Penalty & Seniority Penalty
        num_matched = len(skill_res["matched"])
        if not domain_match:
            if num_matched < 2:
                weighted_score -= 35.0
            else:
                weighted_score -= 10.0
        else:
            weighted_score += 15.0
            if num_matched >= 3:
                weighted_score += 5.0
            
        weighted_score += level_comp.get("penalty", 0.0)
            
        final_score = max(30.0, min(98.0, weighted_score))
        
        return {
            "job_id": str(job_dict.get("job_id", "")),
            "job_title": title,
            "company": company,
            "location": location,
            "experience_level": job_level,
            "level_compatibility": level_comp["status"],
            "source_url": job_dict.get("source_url", ""),
            "overall_match_score": round(final_score, 1),
            "skills_score": skill_res['score'],
            "experience_score": exp_score,
            "semantic_score": semantic_score,
            "matched_skills": skill_res['matched'],
            "missing_skills": skill_res['missing']
        }

    def match_cv_against_all_jobs(self, parsed_cv: ParsedCVProfile, top_n: int = 5) -> List[Dict]:
        """Matches candidate CV against ALL active jobs in dataset and returns Top N best matches."""
        if not self.raw_jobs:
            return []
            
        results = []
        for job_dict in self.raw_jobs:
            match_res = self.match_single_pair(parsed_cv, job_dict)
            results.append(match_res)
            
        sorted_results = sorted(results, key=lambda x: x["overall_match_score"], reverse=True)
        return sorted_results[:top_n]


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("🎯 Testing Fast Job Matching & Ranking Engine for CVs (Top 5 Matches)")
    print("=" * 65)
    
    cv_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_cvs")
    pdf_files = [os.path.join(cv_dir, f) for f in os.listdir(cv_dir) if f.lower().endswith('.pdf')]
    
    matcher = MatchingEngine()
    parser = HybridParser()
    
    print(f"\n🚀 Loaded {len(matcher.raw_jobs)} Active Jobs from Dataset.")
    print(f"📄 Processing {len(pdf_files)} Candidate CVs...\n")
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        extracted = TextExtractor.process_resume(pdf_path)
        parsed_cv = parser.parse_cv(extracted["cleaned_text"], filename, extracted["sections"])
        
        print("\n" + "=" * 65)
        print(f"👤 Candidate: {parsed_cv.candidate_name} ({parsed_cv.email or filename})")
        print(f"🎯 Target Domain: '{parsed_cv.detected_domain}' | Skills Count: {len(parsed_cv.normalized_skills)}")
        print("=" * 65)
        
        # Get Top 5 Job Matches
        top_5_jobs = matcher.match_cv_against_all_jobs(parsed_cv, top_n=5)
        
        print(f"\n🏆 TOP 5 MATCHED JOBS for {parsed_cv.candidate_name}:")
        print("-" * 65)
        
        for idx, job in enumerate(top_5_jobs, 1):
            print(f" #{idx} | Match Score: {job['overall_match_score']}% ──> {job['job_title']}")
            print(f"     Company: {job['company']} | Location: {job['location']}")
            print(f"     Skills Match: {job['skills_score']}% | Semantic: {job['semantic_score']}%")
            print(f"     ✅ Matched Skills: {job['matched_skills']}")
            print(f"     ❌ Missing Skills: {job['missing_skills'][:5]}")
            print(f"     🔗 URL: {job['source_url'][:60]}...")
            print("-" * 50)
            
    print("=" * 65)
