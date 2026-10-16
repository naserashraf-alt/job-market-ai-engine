import json
import os
import sys
from rapidfuzz import process, fuzz

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

class SkillNormalizer:
    """Normalizes raw skill strings and groups them under explicit Job Role Taxonomies."""
    
    def __init__(self, skill_db_path: str = None):
        if skill_db_path is None:
            skill_db_path = os.path.join(os.path.dirname(__file__), "..", "skills_dictionary.json")
            
        self.skill_db_path = skill_db_path
        self.canonical_skills = {}
        self.job_taxonomies = {}
        self.alias_to_canonical = {}
        self.load_skill_dictionary()

    def load_skill_dictionary(self):
        """Loads canonical skills, aliases, and job role taxonomies from JSON dictionary."""
        if not os.path.exists(self.skill_db_path):
            raise FileNotFoundError(f"Skills dictionary file not found: {self.skill_db_path}")
            
        with open(self.skill_db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.canonical_skills = data.get("canonical_skills", {})
        self.job_taxonomies = data.get("job_role_taxonomies", {})
            
        # Build inverse lookup map for O(1) exact matching
        self.alias_to_canonical = {}
        for canonical, aliases in self.canonical_skills.items():
            self.alias_to_canonical[canonical.lower()] = canonical
            for alias in aliases:
                self.alias_to_canonical[alias.lower()] = canonical

    def normalize_skill(self, input_skill: str, fuzzy_threshold: float = 85.0) -> str:
        """
        Normalizes a single skill string.
        1. Checks exact O(1) match.
        2. Uses rapidfuzz for string similarity if no exact match.
        3. Fallback to cleaned Title-Cased string.
        """
        if not input_skill or not input_skill.strip():
            return ""
            
        cleaned_input = input_skill.strip().lower()
        
        # 1. Exact Match O(1)
        if cleaned_input in self.alias_to_canonical:
            return self.alias_to_canonical[cleaned_input]
            
        # 2. Fuzzy Matching against all aliases
        all_aliases = list(self.alias_to_canonical.keys())
        match_result = process.extractOne(cleaned_input, all_aliases, scorer=fuzz.ratio)
        
        if match_result:
            matched_alias, score, _ = match_result
            if score >= fuzzy_threshold:
                return self.alias_to_canonical[matched_alias]
                
        # 3. Fallback: Clean Title Case format
        return input_skill.strip().title()

    def normalize_skills_list(self, raw_skills: list[str]) -> list[str]:
        """Normalizes a list of raw skills and returns deduplicated canonical names."""
        if not raw_skills:
            return []
            
        normalized_set = set()
        for skill in raw_skills:
            norm = self.normalize_skill(skill)
            if norm:
                normalized_set.add(norm)
                
        return sorted(list(normalized_set))

    def detect_candidate_job_domain(self, candidate_skills: list[str]) -> tuple[str, float]:
        """
        Analyzes a candidate's normalized skills and detects their Primary Job Role Domain
        (e.g., 'Backend .NET Developer', 'Data Engineer', 'Frontend Web Developer').
        Returns (Primary_Domain_Name, Confidence_Percentage).
        """
        normalized_user_skills = set(self.normalize_skills_list(candidate_skills))
        if not normalized_user_skills:
            return "General Tech", 0.0
            
        best_domain = "General Tech"
        max_overlap = 0
        best_match_ratio = 0.0
        
        for domain, domain_skill_list in self.job_taxonomies.items():
            domain_set = set(domain_skill_list)
            overlap = len(normalized_user_skills.intersection(domain_set))
            if overlap > max_overlap:
                max_overlap = overlap
                best_domain = domain
                best_match_ratio = round((overlap / len(domain_set)) * 100, 1)
                
        return best_domain, best_match_ratio

    def filter_recommendations_by_domain(self, missing_skills: list[str], target_domain: str) -> list[str]:
        """
        Ensures recommended missing skills are STRICTLY RELEVANT to the candidate's target job domain.
        Prevents recommending out-of-domain skills (e.g. recommending Airflow to a Frontend Developer).
        """
        if target_domain not in self.job_taxonomies:
            return missing_skills  # Fallback
            
        allowed_domain_skills = set(self.job_taxonomies[target_domain])
        normalized_missing = set(self.normalize_skills_list(missing_skills))
        
        # Filter to only missing skills that belong to the target domain taxonomy
        domain_relevant_missing = normalized_missing.intersection(allowed_domain_skills)
        return sorted(list(domain_relevant_missing))


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("🔤 Testing Domain-Aware Skill Normalizer Engine (Step 1.3)")
    print("=" * 65)
    
    normalizer = SkillNormalizer()
    
    # Candidate 1: Backend .NET Candidate
    candidate_1_skills = ["c#", "aspnet core", ".net 8", "sql server", "dockerization", "git"]
    norm_c1 = normalizer.normalize_skills_list(candidate_1_skills)
    domain_c1, conf_c1 = normalizer.detect_candidate_job_domain(candidate_1_skills)
    
    print("\n📌 Candidate 1 (.NET Backend Specialist):")
    print("  ├ Raw Input:", candidate_1_skills)
    print("  ├ Normalized Skills:", norm_c1)
    print(f"  └ Detected Job Role Taxonomy: '{domain_c1}' (Confidence: {conf_c1}%)")
    
    # Test Domain-Filtered Skill Recommendations
    raw_missing_for_c1 = ["redis", "postgresql", "apache airflow", "flutter development", "cybersecurity"]
    domain_recs_c1 = normalizer.filter_recommendations_by_domain(raw_missing_for_c1, domain_c1)
    print("  └ Domain-Scoped Skill Recommendations (Relevant to .NET Only):", domain_recs_c1)
    
    # Candidate 2: Frontend Web Candidate
    candidate_2_skills = ["reactjs", "javascript", "typescript", "tailwind css", "html5"]
    domain_c2, conf_c2 = normalizer.detect_candidate_job_domain(candidate_2_skills)
    
    print("\n📌 Candidate 2 (Frontend Specialist):")
    print("  ├ Normalized Skills:", normalizer.normalize_skills_list(candidate_2_skills))
    print(f"  └ Detected Job Role Taxonomy: '{domain_c2}' (Confidence: {conf_c2}%)")
    
    raw_missing_for_c2 = ["next.js", "redux", "apache spark", "embedded c", "flutter"]
    domain_recs_c2 = normalizer.filter_recommendations_by_domain(raw_missing_for_c2, domain_c2)
    print("  └ Domain-Scoped Skill Recommendations (Relevant to Frontend Only):", domain_recs_c2)
    
    print("=" * 65)
