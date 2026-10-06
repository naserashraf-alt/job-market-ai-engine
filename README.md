# 🧠 Job Market AI Engine & Resume Parser

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-PDF%20Extraction-red?style=for-the-badge)](https://pymupdf.readthedocs.io/)
[![NLP](https://img.shields.io/badge/NLP-Skill%20Extraction-blueviolet?style=for-the-badge)](https://en.wikipedia.org/wiki/Natural_language_processing)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

An intelligent AI engine and automated data pipeline designed for **job market analysis**, **resume parsing (PDF)**, **skill extraction**, and **candidate-job matching**. Built as part of a University Graduation Project.

---

## 🎯 Features

- 📄 **Resume PDF Parser (`src/extractor.py`):** High-speed raw text and structured data extraction from PDF resumes using `PyMuPDF` with Unicode normalization and bullet-point cleanup.
- 🔍 **Automated Job Scraper (`scripts/collect_jobs.py`):** Automated collection and ingestion of current job market listings into structured JSON datasets.
- 🏷️ **Skills Taxonomy & Dictionary (`skills_dictionary.json`):** Comprehensive predefined taxonomy of programming languages, frameworks, cloud tools, databases, and DevOps keywords for precise entity recognition.
- 📊 **Processed Datasets (`data/processed/`):** Cleaned, tokenized, and normalized job postings ready for similarity matching and skill gap analysis.

---

## 📂 Project Structure

```
job-market-ai-engine/
└── ai_engine/
    ├── data/
    │   ├── processed/
    │   │   └── jobs_dataset.json      # Cleaned and processed job listings dataset
    │   └── sample_cvs/
    │       └── sample_resume.pdf     # Sample PDF resumes for testing
    ├── scripts/
    │   └── collect_jobs.py           # Web scrapers and job data collectors
    ├── src/
    │   └── extractor.py              # PDF resume parser & text normalization engine
    ├── requirements.txt              # Project dependencies
    ├── skills_dictionary.json        # Skills vocabulary taxonomy
    └── README.md
```

---

## 🚀 Getting Started

### 1. Clone & Setup Environment
```bash
git clone https://github.com/naserashraf-alt/job-market-ai-engine.git
cd job-market-ai-engine/ai_engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Resume Extractor
```bash
python src/extractor.py
```

### 3. Collect Job Market Data
```bash
python scripts/collect_jobs.py
```

---

## 👤 Author

**Naser Ashraf**
- 🌐 [Portfolio Website](https://naserashraf-alt.github.io/portfolio/)
- 💼 [LinkedIn Profile](https://www.linkedin.com/in/naser-ashraf-742106358)
- 📧 [Email](mailto:naserashraf248@gmail.com)
