import os
import pickle
import gdown
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
    score_out_of_100 = Column(Integer)
    status = Column(String)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding
url = "https://drive.google.com/uc?id=1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP"
output = "resume_embeddings.pkl"
gdown.download(url, output, quiet=False)

with open(output, "rb") as f:
    data = pickle.load(f)
resume_embeddings = data["embeddings"]
resume_texts = [item["clean_resume"] for item in data["metadata"]]

# Helpers
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

def score_resume(resume: str, job_description: str) -> int:
    messages = [
        {"role": "system", "content": (
            "You are a strict hiring manager. Score the resume only based on how well it matches the job description. "
            "Give a score from 0 to 100. No explanations.")},
        {"role": "user", "content": f"Job Description:\n{job_description}\n\nResume:\n{resume}"}
    ]
    response = openai.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.0)
    try:
        content = response.choices[0].message.content.strip()
        return min(max(int(''.join(filter(str.isdigit, content.split()[0]))), 0), 100)
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

# Endpoint
@app.post("/evaluate-resumes/")
async def evaluate_resumes(
    job_description: str = Form(...),
    resume_pdfs: List[UploadFile] = File(...)
):
    session = SessionLocal()
    reports = []
    for resume_pdf in resume_pdfs:
        try:
            pdf_bytes = await resume_pdf.read()
            resume_text = extract_text_from_pdf(pdf_bytes)
            job_embedding = get_embedding(job_description)
            top_resumes = search_similar_resumes(job_embedding)
            job_role = recommend_job_type(resume_text)
            resume_analysis = analyze_resume_strengths(resume_text, job_description)
            score = score_resume(resume_text, job_description)
            status = "Passed" if score >= 60 else "Needs Improvement"

            report = ResumeReport(
                filename=resume_pdf.filename,
                suggested_job_role=job_role,
                resume_summary=resume_analysis["resume_summary"],
                skills_present=resume_analysis["skills_present"],
                skills_missing=resume_analysis["skills_missing"],
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
                "skills_present": resume_analysis["skills_present"],
                "skills_missing": resume_analysis["skills_missing"],
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
