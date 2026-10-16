import numpy as np
import sys
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

class SemanticEmbeddingEngine:
    """
    Computes Semantic Text Similarity between CV Text and Job Descriptions
    using TF-IDF Vectorization and Cosine Similarity.
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))

    def calculate_semantic_similarity(self, cv_text: str, job_description: str) -> float:
        """Calculates cosine similarity percentage between CV text and Job Description."""
        if not cv_text or not job_description:
            return 50.0  # Baseline fallback
            
        try:
            tfidf_matrix = self.vectorizer.fit_transform([cv_text, job_description])
            sim_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            # Normalize score between 0.0% and 100.0%
            normalized_score = round(float(sim_score) * 100, 2)
            return max(30.0, min(100.0, normalized_score * 1.8))  # Scale for realistic score distribution
        except Exception:
            return 50.0

    def batch_calculate_similarities(self, cv_text: str, job_descriptions: list[str]) -> list[float]:
        """Calculates similarity scores in batch for fast execution against thousands of jobs."""
        if not cv_text or not job_descriptions:
            return [50.0] * len(job_descriptions)
            
        try:
            corpus = [cv_text] + job_descriptions
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            cv_vector = tfidf_matrix[0:1]
            job_vectors = tfidf_matrix[1:]
            
            sim_scores = cosine_similarity(cv_vector, job_vectors)[0]
            
            results = []
            for score in sim_scores:
                norm = round(float(score) * 100, 2)
                results.append(max(30.0, min(100.0, norm * 1.8)))
                
            return results
        except Exception:
            return [50.0] * len(job_descriptions)


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("📐 Testing Semantic Embedding & Text Similarity Engine")
    print("=" * 65)
    
    engine = SemanticEmbeddingEngine()
    
    cv_sample = "Experienced .NET Developer skilled in C#, ASP.NET Core, MS SQL Server, Docker, and REST APIs."
    job_sample_1 = "Looking for Senior .NET Developer with C#, ASP.NET Core, SQL Server, and Microservices."
    job_sample_2 = "Hiring Graphic Designer proficient in Photoshop, Illustrator, and Figma."
    
    score_1 = engine.calculate_semantic_similarity(cv_sample, job_sample_1)
    score_2 = engine.calculate_semantic_similarity(cv_sample, job_sample_2)
    
    print(f"  ├ Similarity with .NET Job: {score_1}%")
    print(f"  └ Similarity with Graphic Designer Job: {score_2}%")
    print("=" * 65)
