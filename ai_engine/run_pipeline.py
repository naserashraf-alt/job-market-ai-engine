import os
import sys
import json

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add ai_engine to sys.path
ai_engine_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ai_engine_dir)

from src.extractor import TextExtractor, create_sample_pdf
from src.parser import HybridParser
from src.normalizer import SkillNormalizer
from src.matcher import MatchingEngine
from src.recommender import SkillRecommender


def run_master_career_pipeline(pdf_path: str = None, top_n: int = 5):
    """
    Master Automated Pipeline:
    Takes ANY PDF Resume, extracts, cleans, parses, matches against 2500+ active jobs,
    and generates domain-scoped career recommendations.
    """
    cv_dir = os.path.join(ai_engine_dir, "data", "sample_cvs")
    os.makedirs(cv_dir, exist_ok=True)
    
    # 1. Determine Target PDF Resumes to Process
    pdf_files = []
    if pdf_path:
        if os.path.exists(pdf_path):
            pdf_files = [pdf_path]
        else:
            rel_path = os.path.join(cv_dir, pdf_path)
            if os.path.exists(rel_path):
                pdf_files = [rel_path]
            else:
                print(f"❌ Error: Specified CV file not found at '{pdf_path}'")
                return
    else:
        # Process all PDFs in data/sample_cvs folder
        pdf_files = [os.path.join(cv_dir, f) for f in os.listdir(cv_dir) if f.lower().endswith('.pdf')]
        
    if not pdf_files:
        print("ℹ️ No PDF resumes found. Generating default test resume...")
        sample_path = os.path.join(cv_dir, "sample_resume.pdf")
        create_sample_pdf(sample_path)
        pdf_files = [sample_path]

    print("\n" + "🚀 " * 15)
    print("  CAREER MATCHING & RECOMMENDATION SYSTEM — MASTER PIPELINE")
    print("🚀 " * 15 + "\n")
    
    # Initialize Core Engines
    matcher = MatchingEngine()
    parser = HybridParser()
    recommender = SkillRecommender()
    
    print(f"📊 Active Jobs Dataset Loaded: {len(matcher.raw_jobs)} active tech jobs.")
    print(f"📄 Resumes To Process: {len(pdf_files)} PDF file(s).\n")
    
    for idx_file, current_pdf in enumerate(pdf_files, 1):
        filename = os.path.basename(current_pdf)
        print("=" * 70)
        print(f"📂 [{idx_file}/{len(pdf_files)}] PROCESSING RESUME: {filename}")
        print("=" * 70)
        
        # STAGE 1 & 2: Text Extraction & Cleaning
        try:
            extracted = TextExtractor.process_resume(current_pdf)
            print(f"  [STAGE 1] Text Extracted: {extracted['character_count']} chars, {extracted['line_count']} lines.")
        except Exception as e:
            print(f"  ❌ Text Extraction Error: {e}")
            continue

        # STAGE 3: Structured CV Parsing & Domain Detection
        parsed_cv = parser.parse_cv(extracted["cleaned_text"], filename, extracted["sections"])
        print(f"  [STAGE 2] Candidate Name: {parsed_cv.candidate_name}")
        print(f"  [STAGE 2] Email: {parsed_cv.email or 'N/A'} | Phone: {parsed_cv.phone or 'N/A'}")
        print(f"  [STAGE 2] Primary Job Domain: '{parsed_cv.detected_domain}' (Confidence: {parsed_cv.domain_confidence}%)")
        print(f"  [STAGE 2] Candidate Seniority Level: '{parsed_cv.experience_level}' ({parsed_cv.total_years_experience} yrs exp)")
        print(f"  [STAGE 2] Extracted Skills ({len(parsed_cv.normalized_skills)}): {parsed_cv.normalized_skills}")
        
        # STAGE 4: Job Matching & Ranking Engine
        print(f"\n  [STAGE 3] Matching against {len(matcher.raw_jobs)} active jobs...")
        top_matched_jobs = matcher.match_cv_against_all_jobs(parsed_cv, top_n=top_n)
        
        print("\n" + "🏆 " * 10 + f" TOP {top_n} MATCHED JOBS " + "🏆 " * 10)
        for rank, job in enumerate(top_matched_jobs, 1):
            print(f"\n  #{rank} | Match Score: {job['overall_match_score']}% ──> {job['job_title']}")
            print(f"       Company: {job['company']} | Location: {job['location']}")
            print(f"       Level: {job.get('experience_level', 'Mid-Level')} [{job.get('level_compatibility', 'Compatible')}] | Skills Score: {job['skills_score']}% | Semantic: {job['semantic_score']}%")
            print(f"       ✅ Matched Skills: {job['matched_skills']}")
            if job['missing_skills']:
                print(f"       ❌ Missing Skills: {job['missing_skills']}")
            
            # Gap to 100% Analysis
            gap_info = recommender.generate_job_gap_to_100(job, parsed_cv)
            print(f"       🎯 Gap to 100%: Needs +{gap_info['points_needed']}% points.")
            for act in gap_info['action_items']:
                print(f"          └ {act}")
            print(f"       🔗 Apply URL: {job['source_url'][:65]}...")
            
        # STAGE 5: Domain-Aware Skill Gap Recommendations
        skill_recs = recommender.generate_skill_recommendations(parsed_cv, top_matched_jobs)
        
        print("\n" + "💡 " * 10 + " PRIORITIZED SKILL GAP RECOMMENDATIONS " + "💡 " * 10)
        if skill_recs:
            for rec in skill_recs:
                print(f"  • [{rec['priority']}] {rec['skill_name']} ──> {rec['reason']}")
        else:
            print("  🎉 Excellent! You have covered all key skills for your top matched jobs in your domain.")
            
        # STAGE 6: Complete 12-Week Structured Learning Roadmap
        roadmap = recommender.generate_learning_roadmap(parsed_cv, top_matched_jobs)
        print("\n" + "🗺️ " * 10 + f" {roadmap['roadmap_title'].upper()} " + "🗺️ " * 10)
        for ph in roadmap['phases']:
            print(f"\n  📌 {ph['phase']} ({ph['duration']}):")
            print(f"     • Core Topics: {', '.join(ph['core_topics'])}")
            print(f"     • Skills to Master: {', '.join(ph['skills_to_master'])}")
            print(f"     • 🏆 Milestone Project: {ph['milestone_project']}")
            
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    # If a specific CV path is passed as command line argument
    input_cv = sys.argv[1] if len(sys.argv) > 1 else None
    run_master_career_pipeline(input_cv, top_n=5)
