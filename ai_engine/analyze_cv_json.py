import os
import sys
import json
import argparse

# Ensure UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ai_engine_dir = os.path.dirname(os.path.abspath(__file__))
if ai_engine_dir not in sys.path:
    sys.path.append(ai_engine_dir)

from src.extractor import TextExtractor
from src.parser import HybridParser
from src.matcher import MatchingEngine
from src.recommender import SkillRecommender

def analyze_cv(pdf_path: str, top_n: int = 5):
    if not os.path.exists(pdf_path):
        return {"error": f"File not found: {pdf_path}"}
        
    filename = os.path.basename(pdf_path)
    
    # 1. Text Extraction
    try:
        extracted = TextExtractor.process_resume(pdf_path)
    except Exception as e:
        return {"error": f"Failed to extract text: {str(e)}"}
        
    # 2. Parsing
    parser = HybridParser()
    parsed_cv = parser.parse_cv(extracted["cleaned_text"], filename, extracted["sections"])
    
    # 3. Job Matching
    matcher = MatchingEngine()
    top_matched_jobs = matcher.match_cv_against_all_jobs(parsed_cv, top_n=top_n)
    
    # 4. Recommendations
    recommender = SkillRecommender()
    skill_recs = recommender.generate_skill_recommendations(parsed_cv, top_matched_jobs)
    
    output = {
        "filename": filename,
        "candidate_name": parsed_cv.candidate_name,
        "email": parsed_cv.email,
        "phone": parsed_cv.phone,
        "detected_domain": parsed_cv.detected_domain,
        "domain_confidence": parsed_cv.domain_confidence,
        "experience_level": getattr(parsed_cv, "experience_level", "Mid-Level"),
        "normalized_skills": parsed_cv.normalized_skills,
        "summary": parsed_cv.summary,
        "total_years_experience": parsed_cv.total_years_experience,
        "top_matched_jobs": [
            {
                "job_id": job.get("job_id", ""),
                "job_title": job.get("job_title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "experience_level": job.get("experience_level", "Mid-Level"),
                "level_compatibility": job.get("level_compatibility", "Compatible"),
                "overall_match_score": job.get("overall_match_score", 0.0),
                "skills_score": job.get("skills_score", 0.0),
                "semantic_score": job.get("semantic_score", 0.0),
                "matched_skills": job.get("matched_skills", []),
                "missing_skills": job.get("missing_skills", []),
                "source_url": job.get("source_url", "")
            } for job in top_matched_jobs
        ],
        "recommendations": skill_recs
    }
    
    return output

if __name__ == "__main__":
    parser_arg = argparse.ArgumentParser(description="Analyze CV and output JSON")
    parser_arg.add_argument("--pdf", type=str, required=True, help="Path to PDF resume")
    parser_arg.add_argument("--top_n", type=int, default=5, help="Number of matched jobs")
    args = parser_arg.parse_args()
    
    result = analyze_cv(args.pdf, args.top_n)
    print(json.dumps(result, ensure_ascii=False, indent=2))
