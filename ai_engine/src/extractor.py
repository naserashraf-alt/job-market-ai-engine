import pymupdf  # PyMuPDF
import re
import os
import sys

# Ensure UTF-8 output encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

class TextExtractor:
    """Extracts, cleans, and segments raw text from PDF Resumes."""
    
    SECTION_HEADERS = [
        "SUMMARY", "OBJECTIVE", "PROFESSIONAL SUMMARY", "PROFILE",
        "EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT HISTORY", "PROFESSIONAL EXPERIENCE",
        "EDUCATION", "ACADEMIC BACKGROUND", "QUALIFICATIONS",
        "SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "SKILLS & EXPERTISE",
        "PROJECTS", "PERSONAL PROJECTS", "KEY PROJECTS",
        "CERTIFICATIONS", "CERTIFICATES", "COURSES", "LICENSES",
        "LANGUAGES", "VOLUNTEER"
    ]
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Reads a PDF file and extracts raw text page by page."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        doc = pymupdf.open(pdf_path)
        full_text = []
        for page in doc:
            full_text.append(page.get_text("text"))
        return "\n".join(full_text)

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Cleans and normalizes extracted resume text."""
        if not raw_text:
            return ""
            
        # 1. Normalize line endings
        text = re.sub(r'\r\n|\r|\n', '\n', raw_text)
        
        # 2. Replace weird bullet symbols with standard hyphens
        text = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219\u25C6\u25AA\u25FE\u2026\u2013\u2014]', '-', text)
        
        # 3. Consolidate multiple spaces and tabs into single space
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 4. Remove empty or trailing whitespace lines
        cleaned_lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return '\n'.join(cleaned_lines)

    @classmethod
    def segment_sections(cls, cleaned_text: str) -> dict:
        """Segments resume text into logical sections (Experience, Education, Skills, etc.)."""
        lines = cleaned_text.split('\n')
        sections = {"HEADER": []}
        current_section = "HEADER"
        
        for line in lines:
            normalized_line = line.strip().upper()
            
            matched_header = None
            for header in cls.SECTION_HEADERS:
                if normalized_line == header or normalized_line.startswith(header + ":"):
                    matched_header = header
                    break
                    
            if matched_header:
                current_section = matched_header
                if current_section not in sections:
                    sections[current_section] = []
            else:
                sections[current_section].append(line)
                
        return {sec: "\n".join(content_lines) for sec, content_lines in sections.items() if content_lines}

    @classmethod
    def process_resume(cls, pdf_path: str) -> dict:
        """Extracts, cleans, and segments resume text with full metadata."""
        raw_text = cls.extract_text_from_pdf(pdf_path)
        cleaned_text = cls.clean_text(raw_text)
        segmented = cls.segment_sections(cleaned_text)
        
        return {
            "file_name": os.path.basename(pdf_path),
            "character_count": len(cleaned_text),
            "line_count": len(cleaned_text.split('\n')),
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "segmented_sections": list(segmented.keys()),
            "sections": segmented
        }


def create_sample_pdf(output_path: str):
    """Creates a default sample PDF resume if folder is empty."""
    doc = pymupdf.open()
    page = doc.new_page()
    sample_cv_content = """John Doe
Email: john.doe@example.com | Phone: +1-555-0199
LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

SUMMARY
Experienced Software Engineer with 3+ years in Python, SQL, ASP.NET Core, and Cloud Architecture.

SKILLS
- Languages: Python, SQL, C#, JavaScript, HTML/CSS
- Databases: MS SQL Server, PostgreSQL, Redis
- Cloud & DevOps: AWS, Docker, Git, CI/CD Pipelines
- Frameworks: .NET 8, FastAPI, React.js, Pandas

EXPERIENCE
Software Engineer | ABC Tech | 2023 - Present
- Built scalable RESTful Web APIs using ASP.NET Core and MS SQL Server.
- Implemented automated CI/CD pipelines reducing deployment time by 40%.

EDUCATION
Bachelor of Science in Computer Science | State University (2018 - 2022)
"""
    rect = pymupdf.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, sample_cv_content, fontsize=11)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()


if __name__ == "__main__":
    cv_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_cvs")
    os.makedirs(cv_dir, exist_ok=True)
    
    # Check if user specified a specific file or process all PDFs in sample_cvs directory
    target_pdf = None
    if len(sys.argv) > 1:
        custom_input = sys.argv[1]
        if os.path.exists(custom_input):
            target_pdf = custom_input
        else:
            possible_path = os.path.join(cv_dir, custom_input)
            if os.path.exists(possible_path):
                target_pdf = possible_path

    # List all PDFs in cv_dir
    pdf_files = [os.path.join(cv_dir, f) for f in os.listdir(cv_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files and not target_pdf:
        sample_path = os.path.join(cv_dir, "sample_resume.pdf")
        create_sample_pdf(sample_path)
        pdf_files = [sample_path]
        
    pdfs_to_process = [target_pdf] if target_pdf else pdf_files
    
    print("\n" + "=" * 60)
    print(f"📄 Resume Text Extractor (Found {len(pdfs_to_process)} PDF files)")
    print("=" * 60)
    
    for pdf_path in pdfs_to_process:
        print(f"\n▶ Processing: {os.path.basename(pdf_path)}")
        try:
            res = TextExtractor.process_resume(pdf_path)
            print(f"  ├ Characters: {res['character_count']} | Lines: {res['line_count']}")
            print(f"  ├ Detected Sections: {res['segmented_sections']}")
            print("  └ Section Breakdown Preview:")
            for sec, content in res['sections'].items():
                first_line = content.split('\n')[0][:80]
                print(f"      • [{sec}]: {first_line}...")
        except Exception as e:
            print(f"  ❌ Error reading PDF: {e}")
            
    print("\n" + "=" * 60)
