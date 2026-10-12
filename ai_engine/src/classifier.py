import re
from typing import Dict, List, Optional

class SeniorityClassifier:
    """
    Classifies Job Postings and Candidates into standardized experience levels:
    1. 'Internship / Student'
    2. 'Junior / Entry-Level'
    3. 'Mid-Level'
    4. 'Senior'
    5. 'Lead / Principal / Architect'
    """

    LEVELS = [
        "Internship / Student",
        "Junior / Entry-Level",
        "Mid-Level",
        "Senior",
        "Lead / Principal / Architect"
    ]

    # Regex keyword patterns for jobs
    INTERN_KEYWORDS = re.compile(
        r'\b(intern|internship|trainee|training|student|graduate program|co-op|werkstudent|تدريب)\b',
        re.IGNORECASE
    )
    
    LEAD_KEYWORDS = re.compile(
        r'\b(lead|principal|staff|architect|architecture|head of|vp|director|engineering manager|tech lead|chief)\b',
        re.IGNORECASE
    )
    
    SENIOR_KEYWORDS = re.compile(
        r'\b(senior|sr\.?|sr\b|experienced|advanced|expert|specialist|5\+?\s*years?|6\+?\s*years?|7\+?\s*years?|8\+?\s*years?)\b',
        re.IGNORECASE
    )
    
    JUNIOR_KEYWORDS = re.compile(
        r'\b(junior|jr\.?|jr\b|entry\s*level|entry-level|fresh\s*grad|fresh\s*graduate|associate|starter|0-1\s*years?|0-2\s*years?|1-2\s*years?)\b',
        re.IGNORECASE
    )

    MID_KEYWORDS = re.compile(
        r'\b(mid|mid-level|mid\s*level|intermediate|semi\s*senior|semi-senior|2-4\s*years?|3-5\s*years?|2-5\s*years?)\b',
        re.IGNORECASE
    )

    @classmethod
    def classify_job_level(cls, title: str, description: str = "", level_hint: str = "") -> str:
        """Classifies a job listing into an experience level."""
        combined_title = title.lower()
        combined_text = f"{title} {description[:400]}".lower()

        # 1. Direct hints from API if provided
        hint_lower = (level_hint or "").lower()
        if "intern" in hint_lower or "student" in hint_lower:
            return "Internship / Student"
        if "junior" in hint_lower or "entry" in hint_lower:
            return "Junior / Entry-Level"
        if "lead" in hint_lower or "principal" in hint_lower or "architect" in hint_lower or "manager" in hint_lower:
            return "Lead / Principal / Architect"
        if "senior" in hint_lower:
            return "Senior"
        if "mid" in hint_lower:
            return "Mid-Level"

        # 2. Check Title first (Title has highest weight)
        if cls.INTERN_KEYWORDS.search(combined_title):
            return "Internship / Student"
        if cls.LEAD_KEYWORDS.search(combined_title):
            return "Lead / Principal / Architect"
        if cls.SENIOR_KEYWORDS.search(combined_title):
            return "Senior"
        if cls.JUNIOR_KEYWORDS.search(combined_title):
            return "Junior / Entry-Level"
        if cls.MID_KEYWORDS.search(combined_title):
            return "Mid-Level"

        # 3. Check Description excerpt
        if cls.INTERN_KEYWORDS.search(combined_text):
            return "Internship / Student"
        if cls.LEAD_KEYWORDS.search(combined_text):
            return "Lead / Principal / Architect"
        if cls.SENIOR_KEYWORDS.search(combined_text):
            return "Senior"
        if cls.JUNIOR_KEYWORDS.search(combined_text):
            return "Junior / Entry-Level"

        # Default fallback is Mid-Level
        return "Mid-Level"

    @classmethod
    def classify_candidate_level(cls, total_years_experience: float, summary: str = "", current_title: str = "") -> str:
        """Classifies a candidate's experience level based on parsed years and profile summary."""
        text = f"{current_title} {summary}".lower()

        if cls.LEAD_KEYWORDS.search(text) and total_years_experience >= 5.0:
            return "Lead / Principal / Architect"

        if total_years_experience >= 6.0:
            return "Senior"
        elif total_years_experience >= 2.0:
            return "Mid-Level"
        elif total_years_experience >= 0.5:
            return "Junior / Entry-Level"
        else:
            if cls.INTERN_KEYWORDS.search(text) or "student" in text or total_years_experience == 0:
                return "Internship / Student"
            return "Junior / Entry-Level"

    @classmethod
    def calculate_level_compatibility(cls, candidate_level: str, job_level: str) -> Dict[str, any]:
        """
        Calculates compatibility score (0-100) between Candidate Level and Job Level.
        Returns score and human-readable explanation.
        """
        level_hierarchy = {
            "Internship / Student": 1,
            "Junior / Entry-Level": 2,
            "Mid-Level": 3,
            "Senior": 4,
            "Lead / Principal / Architect": 5
        }

        c_rank = level_hierarchy.get(candidate_level, 2)
        j_rank = level_hierarchy.get(job_level, 3)

        diff = c_rank - j_rank

        if diff == 0:
            # Perfect level match
            return {"score": 100.0, "status": "Perfect Match", "penalty": 0.0}
        elif diff == 1:
            # Candidate is 1 step above (e.g., Mid applying to Junior) -> slight overqualified
            return {"score": 90.0, "status": "Overqualified (Safe)", "penalty": 0.0}
        elif diff == -1:
            # Candidate is 1 step below (e.g., Junior applying to Mid) -> stretch opportunity
            return {"score": 80.0, "status": "Growth Opportunity", "penalty": 0.0}
        elif diff > 1:
            # Candidate is significantly overqualified (e.g. Senior applying to Intern)
            return {"score": 60.0, "status": "Highly Overqualified", "penalty": -5.0}
        else:
            # Candidate is significantly underqualified (e.g. Junior applying to Lead)
            return {"score": 40.0, "status": "Seniority Gap", "penalty": -15.0}
