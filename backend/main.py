import os
import pickle
import gdown
import re
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text, ARRAY
from dotenv import load_dotenv
from typing import List
from numpy.linalg import norm
import fitz
import openai

# Load environment
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Set up DB
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class ResumeReport(Base):
    __tablename__ = "resume_reports"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    suggested_job_role = Column(String)
    resume_summary = Column(Text)
    skills_present = Column(ARRAY(String))
    skills_missing = Column(ARRAY(String))
    normalized_skills = Column(ARRAY(String))
    matching_skills = Column(ARRAY(String))
    missing_skills = Column(ARRAY(String))
    score_out_of_100 = Column(Integer)
    status = Column(String)

Base.metadata.create_all(bind=engine)

# Skill taxonomy
SKILL_TAXONOMY = {
    "Node.js": ["Node JS", "Nodejs", "Node"],
    "React": ["ReactJS", "React.js"],
    "Python": ["python3", "py"],
    "MongoDB": ["mongo", "Mongo DB"],
    "Spring Boot": ["SpringBoot", "Spring"],
}

def normalize_skill(skill: str) -> str:
    skill_lower = skill.lower()
    for norm, variants in SKILL_TAXONOMY.items():
        if skill_lower == norm.lower() or skill_lower in [v.lower() for v in variants]:
            return norm
    return skill.strip()

def extract_skill_experience(resume_text: str, skills: List[str]) -> dict:
    experience = {}
    for skill in skills:
        pattern = rf"(?i)(\d+)\+?\s*(?:years|yrs).{{0,15}}{re.escape(skill)}"
        match = re.search(pattern, resume_text)
        if match:
            experience[skill] = int(match.group(1))
        else:
            experience[skill] = 0
    return experience

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join([page.get_text() for page in doc])

def get_embedding(text: str) -> np.ndarray:
    text = text.replace("\n", " ")
    response = openai.embeddings.create(input=[text], model="text-embedding-3-large")
    return np.array(response.data[0].embedding)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (norm(a) * norm(b))

def search_similar_resumes(job_embedding: np.ndarray, top_k=5):
    scores = [cosine_similarity(job_embedding, emb) for emb in resume_embeddings]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [resume_texts[i] for i in top_indices]

def recommend_job_type(resume: str) -> str:
    messages = [
        {"role": "system", "content": "You are a career advisor. Only respond with the most suitable job title in 2 to 3 sentences only and no additional information."},
        {"role": "user", "content": f"Suggest the most suitable job title for this resume:\n\n{resume}"}
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages, temperature=0.7
    )
    return response.choices[0].message.content.strip().split("\n")[0]

def score_resume_with_experience(resume_text: str, job_description: str, normalized_skills: List[str]) -> int:
    skills_experience = extract_skill_experience(resume_text, normalized_skills)
    prompt = (
        "Score the resume from 0 to 100 based on:\n"
        "1. Skill match (both missing & matching skills).\n"
        "2. Experience match — prefer exact/near matches to the years mentioned in the JD.\n"
        "3. Penalize for overqualification or underqualification.\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Resume:\n{resume_text}\n\n"
        f"Candidate Skills & Experience:\n{skills_experience}"
    )
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    try:
        content = response.choices[0].message.content
        match = re.search(r"\b(\d{1,3})\b", content)
        return min(max(int(match.group(1)), 0), 100) if match else 0
    except Exception:
        return 0

def analyze_resume_strengths(resume: str, job_description: str) -> dict:
    messages = [
        {"role": "system", "content": (
            "You are a resume evaluator.\nFormat:\nSummary:\n<summary>\nSkills Present:\n- skill1\n- skill2\nSkills Missing:\n- skill1\n- skill2")},
        {"role": "user", "content": f"Job Description:\n{job_description}\n\nResume:\n{resume}"}
    ]
    response = openai.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.7)
    content = response.choices[0].message.content.strip()
    analysis = {"resume_summary": "", "skills_present": [], "skills_missing": []}
    lines = content.splitlines()
    current = None
    for line in lines:
        if line.lower().startswith("summary"):
            current = "resume_summary"
        elif line.lower().startswith("skills present"):
            current = "skills_present"
        elif line.lower().startswith("skills missing"):
            current = "skills_missing"
        elif current == "resume_summary":
            analysis[current] += " " + line.strip()
        elif current in ["skills_present", "skills_missing"] and line.strip().startswith("-"):
            analysis[current].append(line.strip("- ").strip())
    return analysis

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embeddings
url = "https://drive.google.com/uc?id=1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP"
output = "resume_embeddings.pkl"
gdown.download(url, output, quiet=False)
with open(output, "rb") as f:
    data = pickle.load(f)
resume_embeddings = data["embeddings"]
resume_texts = [item["clean_resume"] for item in data["metadata"]]

@app.post("/evaluate-resumes/")
async def evaluate_resumes(job_description: str = Form(...), resume_pdfs: List[UploadFile] = File(...)):
    session = SessionLocal()
    reports = []
    for resume_pdf in resume_pdfs:
        try:
            pdf_bytes = await resume_pdf.read()
            resume_text = extract_text_from_pdf(pdf_bytes)
            resume_analysis = analyze_resume_strengths(resume_text, job_description)
            skills_present = resume_analysis["skills_present"]
            skills_missing = resume_analysis["skills_missing"]
            normalized_skills = list(set([normalize_skill(skill) for skill in skills_present]))
            score = score_resume_with_experience(resume_text, job_description, normalized_skills)
            status = "Passed" if score >= 60 else "Needs Improvement"
            job_embedding = get_embedding(job_description)
            top_resumes = search_similar_resumes(job_embedding)
            job_role = recommend_job_type(resume_text)

            report = ResumeReport(
                filename=resume_pdf.filename,
                suggested_job_role=job_role,
                resume_summary=resume_analysis["resume_summary"],
                skills_present=skills_present,
                skills_missing=skills_missing,
                normalized_skills=normalized_skills,
                matching_skills=skills_present,
                missing_skills=skills_missing,
                score_out_of_100=score,
                status=status
            )
            session.add(report)
            session.commit()

            reports.append({
                "filename": resume_pdf.filename,
                "matched_resumes": top_resumes,
                "suggested_job_role": job_role,
                "resume_summary": resume_analysis["resume_summary"],
                "skills_present": skills_present,
                "skills_missing": skills_missing,
                "normalized_skills": normalized_skills,
                "score_out_of_100": score,
                "status": status
            })
        except Exception as e:
            reports.append({"filename": resume_pdf.filename, "error": str(e)})
    session.close()
    return {"reports": reports}

@app.get("/")
def root():
    return {"message": "CV Evaluator API is running. Use POST /evaluate-resumes/ to evaluate resumes."}
