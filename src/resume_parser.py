"""
resume_parser.py – Parses uploaded resumes (PDF / TXT) and extracts structured
candidate information: name, skills, experience level, job titles, and education.
"""

import re
import os
from pathlib import Path

# PDF parsing – try pdfminer first; fall back to PyPDF2
try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


# ── Keyword banks ────────────────────────────────────────────────────────────

TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "angular", "vue", "node.js", "django", "flask", "spring", "fastapi",
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
    "aws", "gcp", "azure", "ibm cloud", "machine learning", "deep learning",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "rest api", "graphql", "kafka", "rabbitmq", "microservices",
    "html", "css", "git", "linux", "bash",
]

SOFT_SKILLS = [
    "leadership", "communication", "teamwork", "problem-solving", "critical thinking",
    "adaptability", "time management", "project management", "agile", "scrum",
    "mentoring", "collaboration", "creativity", "analytical", "stakeholder management",
]

EXPERIENCE_KEYWORDS = {
    "entry":  ["intern", "internship", "fresher", "graduate", "trainee", "0-1 year", "1 year"],
    "mid":    ["2 years", "3 years", "4 years", "mid-level", "associate", "2-4 years"],
    "senior": ["senior", "lead", "principal", "staff", "5 years", "6 years", "7 years",
               "8 years", "10 years", "architect", "manager"],
}

ROLE_KEYWORDS = {
    "Software Engineer":    ["software engineer", "software developer", "sde", "swe"],
    "Data Scientist":       ["data scientist", "data science", "ml engineer", "machine learning engineer"],
    "Frontend Developer":   ["frontend", "front-end", "ui developer", "react developer"],
    "Backend Developer":    ["backend", "back-end", "api developer", "server-side"],
    "DevOps Engineer":      ["devops", "site reliability", "sre", "cloud engineer", "infrastructure"],
    "Product Manager":      ["product manager", "pm", "product owner", "po"],
    "Full Stack Developer": ["full stack", "fullstack", "mern", "mean"],
    "Data Analyst":         ["data analyst", "business analyst", "bi analyst"],
    "AI/ML Engineer":       ["ai engineer", "ml engineer", "nlp engineer", "computer vision"],
    "Cybersecurity Analyst":["security analyst", "cybersecurity", "penetration tester", "soc analyst"],
}


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file."""
    if PDFMINER_AVAILABLE:
        try:
            return pdfminer_extract(file_path) or ""
        except Exception:
            pass
    if PYPDF2_AVAILABLE:
        text = []
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
        except Exception:
            pass
    return ""


def extract_text_from_txt(file_path: str) -> str:
    """Read a plain-text file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_resume_text(file_path: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    if ext in (".txt",):
        return extract_text_from_txt(file_path)
    return ""


# ── Parsing helpers ───────────────────────────────────────────────────────────

def _extract_name(text: str) -> str:
    """Heuristic: first two capitalised words at the start of the resume."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return line
    return "Candidate"


def _extract_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def _extract_phone(text: str) -> str:
    match = re.search(r"(\+?\d[\d\s\-().]{7,15}\d)", text)
    return match.group(0).strip() if match else ""


def _extract_skills(text: str) -> dict:
    lower = text.lower()
    technical = [s for s in TECH_SKILLS if s in lower]
    soft      = [s for s in SOFT_SKILLS if s in lower]
    return {"technical": technical, "soft": soft}


def _extract_experience_level(text: str) -> str:
    lower = text.lower()
    for level, keywords in EXPERIENCE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return level
    # Fallback: count years mentioned
    years = re.findall(r"(\d+)\s*(?:\+\s*)?years?", lower)
    if years:
        max_years = max(int(y) for y in years)
        if max_years <= 1:
            return "entry"
        if max_years <= 4:
            return "mid"
        return "senior"
    return "mid"  # default assumption


def _extract_job_role(text: str) -> str:
    lower = text.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return role
    return "Software Engineer"  # sensible default


def _extract_education(text: str) -> list:
    degrees = re.findall(
        r"(b\.?tech|m\.?tech|b\.?e|m\.?e|b\.?sc|m\.?sc|mba|phd|bachelor|master|doctorate)",
        text,
        re.IGNORECASE,
    )
    return list({d.upper() for d in degrees})


# ── Public API ────────────────────────────────────────────────────────────────

def parse_resume(file_path: str) -> dict:
    """
    Parse a resume file and return a structured candidate profile dict.

    Returns:
        {
            name, email, phone,
            skills: {technical, soft},
            experience_level,
            job_role,
            education,
            raw_text,
        }
    """
    raw_text = extract_resume_text(file_path)
    if not raw_text.strip():
        return {
            "name": "Candidate",
            "email": "",
            "phone": "",
            "skills": {"technical": [], "soft": []},
            "experience_level": "mid",
            "job_role": "Software Engineer",
            "education": [],
            "raw_text": "",
        }

    return {
        "name":             _extract_name(raw_text),
        "email":            _extract_email(raw_text),
        "phone":            _extract_phone(raw_text),
        "skills":           _extract_skills(raw_text),
        "experience_level": _extract_experience_level(raw_text),
        "job_role":         _extract_job_role(raw_text),
        "education":        _extract_education(raw_text),
        "raw_text":         raw_text[:5000],  # truncate to avoid token overflows
    }
