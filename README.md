# 🚀 Career Matching & Recommendation System

> **Software Engineering Graduation Project:** An AI-powered System for CV Parsing, Job Matching, Skill Gap Analysis, and Career Recommendations built with **ASP.NET Core (.NET 8.0)**, **Microsoft SQL Server**, and **Python 3.12 AI Engine**.

---

## 🏗️ Updated Architecture & Tech Stack

* **Backend API:** **ASP.NET Core (.NET 8.0)** — High-performance RESTful Web API, Entity Framework Core (EF Core), and JWT Authentication.
* **Database:** **Microsoft SQL Server (MS SQL Server)** — Relational Database for Users, CVs, Jobs, Matches, and Skills.
* **AI Engine:** **Python 3.12** — NLP Resume Parsing, PyMuPDF Extractor, Skill Normalizer (RapidFuzz), Sentence-Transformers Embeddings, and Weighted Matching Engine.
* **Frontend:** **React.js** — Web Application & Admin Dashboard.

---

## 📁 Directory Structure

```
final project/
├── backend/                  # ASP.NET Core (.NET 8.0) Web API Solution
│   ├── Controllers/         # Auth, CVs, Jobs, Matching, Recommendations Endpoints
│   ├── Services/            # Business Logic & AI Subsystem Connector
│   ├── Data/                # Entity Framework Core & MS SQL Server DBContext
│   ├── Models/              # Relational Entities (User, CV, Job, Match, Skill)
│   └── Program.cs
│
├── ai_engine/                # Python 3.12 AI & NLP Subsystem
│   ├── data/
│   │   ├── raw/             # Raw dataset feeds
│   │   ├── processed/       # Cleaned jobs_dataset.json (2,578 active tech jobs)
│   │   └── sample_cvs/      # PDF Test Resumes
│   ├── src/                 # TextExtractor, SkillNormalizer, Embeddings & Matcher
│   ├── scripts/             # Data Collection & Closed Job Cleaning Scripts
│   └── requirements.txt
│
├── frontend/                 # React.js Web Application & Admin Dashboard
└── docs/                     # Specifications, SRS, ERD & Notion Guide Files
```

---

## 📊 Live Dataset Status

* **Total Active Tech Jobs:** `2,578`
* **Egypt Tech Jobs 🇪🇬:** `197` (LinkedIn Egypt across all tech fields)
* **Global Remote Tech Jobs 🌐:** `2,381` (Remotive & Arbeitnow)
