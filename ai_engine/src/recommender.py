import os
import sys
from typing import List, Dict
from collections import Counter

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Import modules from src
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.normalizer import SkillNormalizer
from src.parser import ParsedCVProfile


class SkillRecommender:
    """
    Domain-Aware Skill Recommendation & Career Roadmap Engine.
    Analyzes missing skills across matched target jobs, calculates gap-to-100%,
    and generates structured learning roadmaps.
    """
    
    def __init__(self, skill_db_path: str = None):
        self.normalizer = SkillNormalizer(skill_db_path)

    def generate_skill_recommendations(self, parsed_cv: ParsedCVProfile, matched_jobs: List[Dict]) -> List[Dict]:
        """
        Generates domain-scoped, prioritized skill recommendations for a candidate
        based on missing skills in their top matched jobs.
        """
        if not matched_jobs:
            return []
            
        candidate_domain = parsed_cv.detected_domain
        
        # Collect all missing skills from top matched jobs
        all_missing_skills = []
        for job in matched_jobs:
            missing = job.get("missing_skills", [])
            all_missing_skills.extend(missing)
            
        if not all_missing_skills:
            return []
            
        # 1. Scope missing skills strictly to candidate's target job domain
        scoped_missing_skills = self.normalizer.filter_recommendations_by_domain(
            all_missing_skills, 
            candidate_domain
        )
        
        # 2. Count frequency of each domain-relevant missing skill
        total_jobs_analyzed = len(matched_jobs)
        skill_counts = Counter(scoped_missing_skills)
        
        recommendations = []
        for skill, count in skill_counts.most_common(8):
            demand_freq = round((count / total_jobs_analyzed) * 100.0, 1)
            
            if demand_freq >= 50.0:
                priority = "HIGH 🔴"
            elif demand_freq >= 25.0:
                priority = "MEDIUM 🟡"
            else:
                priority = "LOW 🟢"
                
            recommendations.append({
                "skill_name": skill,
                "priority": priority,
                "demand_frequency": demand_freq,
                "reason": f"Required in {count} out of {total_jobs_analyzed} analyzed top jobs for {candidate_domain}."
            })
            
        return recommendations

    @staticmethod
    def generate_job_gap_to_100(job: Dict, parsed_cv: ParsedCVProfile) -> Dict:
        """
        Calculates exact missing components to boost match score to 100% for a specific job.
        """
        missing_skills = job.get("missing_skills", [])
        current_score = job.get("overall_match_score", 0.0)
        level_status = job.get("level_compatibility", "Compatible")
        job_level = job.get("experience_level", "Mid-Level")
        
        action_items = []
        
        if missing_skills:
            action_items.append(f"Add evidence or projects covering missing skills: {', '.join(missing_skills)}.")
        else:
            action_items.append("Skills coverage is already 100% complete for this job.")
            
        if "Gap" in level_status or "Seniority" in level_status:
            action_items.append(f"Highlight production leadership or scale achievements to match the '{job_level}' level.")
        elif "Overqualified" in level_status:
            action_items.append("Tailor resume to emphasize hands-on technical execution for this role.")
            
        action_items.append("Ensure your summary section explicitly cites keywords matching the job title.")
        
        gap_points = round(max(0.0, 100.0 - current_score), 1)
        
        return {
            "current_score": current_score,
            "points_needed": gap_points,
            "missing_skills": missing_skills,
            "level_compatibility": level_status,
            "action_items": action_items
        }

    def generate_learning_roadmap(self, parsed_cv: ParsedCVProfile, matched_jobs: List[Dict]) -> Dict:
        """
        Generates a comprehensive, multi-phase technical learning roadmap tailored to candidate domain and missing skills.
        """
        domain = parsed_cv.detected_domain
        current_skills = set(parsed_cv.normalized_skills)
        
        # Determine Domain-Specific Roadmap Blueprints
        if "Data" in domain or "AI" in domain or "Machine Learning" in domain:
            phases = [
                {
                    "phase": "Phase 1: Advanced AI Modeling & Deep Learning",
                    "duration": "Weeks 1 - 4",
                    "core_topics": ["PyTorch Deep Dive", "Transformer Architectures", "LLMs & Prompt Engineering", "HuggingFace Ecosystem"],
                    "skills_to_master": ["PyTorch", "Transformers", "LangChain", "Vector Databases (Chroma / Pinecone)"],
                    "milestone_project": "Build an End-to-End RAG AI Assistant with Local LLMs and Vector Search."
                },
                {
                    "phase": "Phase 2: Production MLOps & Deployment Pipeline",
                    "duration": "Weeks 5 - 8",
                    "core_topics": ["MLflow Experiment Tracking", "FastAPI Model Serving", "Docker Containerization", "CI/CD for ML (GitHub Actions)"],
                    "skills_to_master": ["MLflow", "Docker", "FastAPI", "AWS SageMaker / GCP Vertex AI"],
                    "milestone_project": "Deploy an automated CI/CD pipeline serving a deep learning model with monitoring."
                },
                {
                    "phase": "Phase 3: Big Data & Scalable AI Engineering",
                    "duration": "Weeks 9 - 12",
                    "core_topics": ["Distributed Computing (Apache Spark)", "Data Warehousing with Snowflake", "Feature Stores", "Real-Time Streaming"],
                    "skills_to_master": ["Apache Spark", "Snowflake", "ETL Pipelines", "Airflow"],
                    "milestone_project": "Design a real-time streaming recommendation engine on cloud infrastructure."
                }
            ]
        elif "Frontend" in domain:
            phases = [
                {
                    "phase": "Phase 1: Advanced Modern JavaScript & TypeScript",
                    "duration": "Weeks 1 - 3",
                    "core_topics": ["TypeScript Generics & Utility Types", "Asynchronous JS & Event Loop", "Performance Optimization"],
                    "skills_to_master": ["TypeScript", "ESNext", "Webpack / Vite"],
                    "milestone_project": "Build a modular, fully typed dashboard with real-time WebSocket feeds."
                },
                {
                    "phase": "Phase 2: Next.js App Router & Global State",
                    "duration": "Weeks 4 - 7",
                    "core_topics": ["Server-Side Rendering (SSR)", "Server Actions", "Redux Toolkit & Zustand", "Tailwind CSS Design Systems"],
                    "skills_to_master": ["Next.js", "Zustand", "Tailwind CSS", "Storybook"],
                    "milestone_project": "Develop a production-ready SaaS landing & client portal with 95+ Web Vitals."
                },
                {
                    "phase": "Phase 3: Micro-Frontends & Testing",
                    "duration": "Weeks 8 - 10",
                    "core_topics": ["Jest & React Testing Library", "Cypress E2E Testing", "CI/CD deployment to Vercel/AWS"],
                    "skills_to_master": ["Cypress", "Jest", "CI/CD", "Web Vitals"],
                    "milestone_project": "Complete test suite covering unit, integration, and E2E flows with 90% coverage."
                }
            ]
        else: # Backend / Full Stack / General
            phases = [
                {
                    "phase": "Phase 1: Enterprise Architecture & Cloud Services",
                    "duration": "Weeks 1 - 4",
                    "core_topics": ["Clean Architecture & CQRS", "Entity Framework Core / ORM Deep Dive", "Microservices & Message Brokers"],
                    "skills_to_master": ["ASP.NET Core / FastAPI", "RabbitMQ / Kafka", "Redis Caching"],
                    "milestone_project": "Build an Event-Driven Microservices Backend with Distributed Tracing."
                },
                {
                    "phase": "Phase 2: Cloud Infrastructure & DevOps",
                    "duration": "Weeks 5 - 8",
                    "core_topics": ["Docker & Kubernetes Orchestration", "AWS / Azure Cloud Deployment", "Terraform Infrastructure as Code"],
                    "skills_to_master": ["Docker", "Kubernetes", "AWS/Azure", "CI/CD"],
                    "milestone_project": "Deploy containerized microservices to a managed Kubernetes cluster with automated CI/CD."
                },
                {
                    "phase": "Phase 3: High-Throughput System Design",
                    "duration": "Weeks 9 - 12",
                    "core_topics": ["Database Sharding & Indexing", "gRPC Communication", "Security & OAuth2/OIDC"],
                    "skills_to_master": ["PostgreSQL/MS SQL", "gRPC", "OAuth2", "System Design"],
                    "milestone_project": "Benchmark and optimize high-throughput API handling 10,000+ requests/sec."
                }
            ]
            
        return {
            "target_domain": domain,
            "roadmap_title": f"12-Week Master Career Roadmap for {domain}",
            "phases": phases
        }
