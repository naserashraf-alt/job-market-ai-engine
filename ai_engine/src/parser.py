import re
import os
import sys
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Import modules from src
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.normalizer import SkillNormalizer
from src.classifier import SeniorityClassifier
from src.extractor import TextExtractor, create_sample_pdf


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration_raw: Optional[str] = None
    description: Optional[str] = None

class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None

class ParsedCVProfile(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    links: Dict[str, str] = Field(default_factory=dict)
    detected_domain: str = "General Tech"
    domain_confidence: float = 0.0
    experience_level: str = "Junior / Entry-Level"
    normalized_skills: List[str] = Field(default_factory=list)
    total_years_experience: float = 0.0
    summary: Optional[str] = None
    experiences: List[ExperienceItem] = Field(default_factory=list)
    educations: List[EducationItem] = Field(default_factory=list)

class ParsedJobProfile(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    detected_domain: str = "General Tech"
    experience_level: str = "Mid-Level"
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_years_experience: float = 0.0
    cleaned_description: str


class HybridParser:
    """Hybrid Resume & Job Description Parser combining Regex, NLP Rules & Skill Normalization."""
    
    def __init__(self, skill_db_path: str = None):
        self.normalizer = SkillNormalizer(skill_db_path)

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_regex, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        phone_regex = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_regex, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_links(text: str) -> Dict[str, str]:
        links = {}
        linkedin_match = re.search(r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        github_match = re.search(r'(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        
        if linkedin_match:
            links['linkedin'] = linkedin_match.group(0)
        if github_match:
            links['github'] = github_match.group(0)
            
        return links

    @staticmethod
    def extract_years_of_experience(text: str) -> float:
        """Extracts candidate's total years of experience using regex patterns."""
        exp_regex = r'(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\b'
        matches = re.findall(exp_regex, text, re.IGNORECASE)
        if matches:
            float_years = [float(m) for m in matches if float(m) <= 40]
            if float_years:
                return max(float_years)
        return 1.0

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extracts and normalizes canonical skills from unstructured text safely."""
        found_skills = set()
        text_lower = text.lower()
        
        sorted_aliases = sorted(self.normalizer.alias_to_canonical.items(), key=lambda x: len(x[0]), reverse=True)
        
        for alias, canonical in sorted_aliases:
            if '#' in alias or '+' in alias or '.' in alias:
                pattern = r'(?:^|\s|,|/)' + re.escape(alias) + r'(?:$|\s|,|/|\.|\b)'
            else:
                pattern = r'\b' + re.escape(alias) + r'\b'
                
            if re.search(pattern, text_lower):
                found_skills.add(canonical)
                
        return sorted(list(found_skills))

    def parse_cv(self, cleaned_cv_text: str, file_name: str = "cv.pdf", segmented_sections: dict = None) -> ParsedCVProfile:
        """Parses cleaned CV text into a structured ParsedCVProfile object."""
        email = self.extract_email(cleaned_cv_text)
        phone = self.extract_phone(cleaned_cv_text)
        links = self.extract_links(cleaned_cv_text)
        
        extracted_skills = self.extract_skills_from_text(cleaned_cv_text)
        domain, confidence = self.normalizer.detect_candidate_job_domain(extracted_skills)
        years_exp = self.extract_years_of_experience(cleaned_cv_text)
        
        lines = [line.strip() for line in cleaned_cv_text.split('\n') if line.strip()]
        candidate_name = lines[0] if lines and len(lines[0]) < 50 and not '@' in lines[0] else "Candidate"
        
        summary = segmented_sections.get("SUMMARY", None) if segmented_sections else None
        exp_level = SeniorityClassifier.classify_candidate_level(years_exp, summary or "", cleaned_cv_text[:300])
        
        return ParsedCVProfile(
            candidate_name=candidate_name,
            email=email,
            phone=phone,
            links=links,
            detected_domain=domain,
            domain_confidence=confidence,
            experience_level=exp_level,
            normalized_skills=extracted_skills,
            total_years_experience=years_exp,
            summary=summary
        )

    def parse_job(self, job_dict: dict) -> ParsedJobProfile:
        """Parses raw job dictionary into structured ParsedJobProfile object."""
        title = job_dict.get("title", "Software Role")
        desc = job_dict.get("cleaned_description", "")
        extracted_skills = self.extract_skills_from_text(desc)
        domain, _ = self.normalizer.detect_candidate_job_domain(extracted_skills)
        years_exp = self.extract_years_of_experience(desc)
        exp_level = job_dict.get("experience_level") or SeniorityClassifier.classify_job_level(title, desc)
        
        num_skills = len(extracted_skills)
        split_idx = int(num_skills * 0.75) if num_skills > 3 else num_skills
        
        required_skills = extracted_skills[:split_idx]
        preferred_skills = extracted_skills[split_idx:]
        
        return ParsedJobProfile(
            job_id=str(job_dict.get("job_id", "")),
            title=title,
            company=job_dict.get("company", "Tech Company"),
            location=job_dict.get("location", "Egypt"),
            detected_domain=domain,
            experience_level=exp_level,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            required_years_experience=years_exp,
            cleaned_description=desc
        )


def create_second_sample_pdf(output_path: str):
    """Creates a second sample PDF resume (Frontend Developer Specialist) for testing."""
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    
    cv_content = """Sara Ahmed
Email: sara.ahmed@example.com | Phone: +20-100-123-4567
LinkedIn: linkedin.com/in/saraahmed | GitHub: github.com/saraahmed

SUMMARY
Passionate Frontend Web Developer with 2+ years of experience crafting responsive web interfaces.

SKILLS
- Core: JavaScript, TypeScript, HTML5, CSS3, Tailwind CSS
- Frameworks: React.js, Next.js, Redux Toolkit
- UI Libraries: Bootstrap, Material UI, Figma
- Tools: Git, GitHub, VS Code, Postman, Webpack

EXPERIENCE
Frontend Developer | Digital Cairo Agency | 2024 - Present
- Developed high-performance Single Page Applications (SPAs) using React.js and Next.js.
- Integrated RESTful APIs with Axios and Redux Toolkit for global state management.
- Improved Web Vitals score by 35% through image optimization and lazy loading.

UI Developer Intern | TechEgypt | 2023 - 2024
- Designed and built responsive landing pages using Tailwind CSS and React.

EDUCATION
Bachelor of Engineering in Information Technology | Cairo University (2019 - 2023)
"""
    rect = pymupdf.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, cv_content, fontsize=11)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("🧠 Testing Hybrid Resume & Job Parser Engine (Step 2)")
    print("=" * 65)
    
    cv_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_cvs")
    os.makedirs(cv_dir, exist_ok=True)
    
    # 1. Ensure test CVs exist
    sample_cv1 = os.path.join(cv_dir, "sample_resume.pdf")
    sample_cv2 = os.path.join(cv_dir, "sample_resume_frontend.pdf")
    
    create_sample_pdf(sample_cv1)
    create_second_sample_pdf(sample_cv2)
    
    parser = HybridParser()
    
    # Process all CV PDFs in sample_cvs folder
    pdf_files = [os.path.join(cv_dir, f) for f in os.listdir(cv_dir) if f.lower().endswith('.pdf')]
    
    print(f"\n📄 Found {len(pdf_files)} Resumes in 'data/sample_cvs/' folder:")
    print("-" * 65)
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        extracted = TextExtractor.process_resume(pdf_path)
        parsed = parser.parse_cv(extracted["cleaned_text"], filename, extracted["sections"])
        
        print(f"\n▶ Resume File: {filename}")
        print(f"  ├ Name: {parsed.candidate_name}")
        print(f"  ├ Email: {parsed.email}")
        print(f"  ├ Phone: {parsed.phone}")
        print(f"  ├ Links: {parsed.links}")
        print(f"  ├ Detected Domain Taxonomy: '{parsed.detected_domain}' (Confidence: {parsed.domain_confidence}%)")
        print(f"  ├ Total Experience: {parsed.total_years_experience} years")
        print(f"  └ Extracted Skills ({len(parsed.normalized_skills)}): {parsed.normalized_skills}")
        print("-" * 50)
        
    print("=" * 65)
