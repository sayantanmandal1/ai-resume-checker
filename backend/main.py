import pickle
import gdown
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from dotenv import load_dotenv
import os
import openai
from fastapi.middleware.cors import CORSMiddleware
from numpy.linalg import norm
import fitz  # PyMuPDF for PDF text extraction
from typing import List

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

url = "https://drive.google.com/uc?id=1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP"
output = "resume_embeddings.pkl"
gdown.download(url, output, quiet=False)

with open(output, "rb") as f:
    data = pickle.load(f)

resume_embeddings = data["embeddings"]  # numpy array of shape (N, embedding_dim)
resume_texts = [item['clean_resume'] for item in data["metadata"]]  # list of resumes extracted correctly

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_embedding(text: str) -> np.ndarray:
    text = text.replace("\n", " ")
    response = openai.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return np.array(response.data[0].embedding)

def recommend_job_type(resume: str) -> str:
    messages = [
        {"role": "system", "content": "You are a career advisor. Only respond with the most suitable job title in 2 to 3 sentences only and no additional information."},
        {"role": "user", "content": f"Suggest the most suitable job title for this resume:\n\n{resume}"}
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip().split("\n")[0]



def score_resume(resume: str, job_description: str) -> int:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict and domain-sensitive hiring manager. You must score the resume based ONLY on how well it matches the job description. "
                "If the skills, experience, or domain do not match, give a low score (under 40). "
                "If the resume is for a different field entirely (e.g., backend dev for an HR job), give a score under 20. "
                "Do NOT explain. Only respond with a number from 0 to 100."
            )
        },
        {
            "role": "user",
            "content": f"Job Description:\n{job_description}\n\nResume:\n{resume}"
        }
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.0
    )
    content = response.choices[0].message.content.strip()

    try:
        score = int(''.join(filter(str.isdigit, content.split()[0])))
        return min(max(score, 0), 100)
    except:
        return 0


def analyze_resume_strengths(resume: str, job_description: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a career advisor and resume evaluator. Your task is to:\n"
                "- Write a concise summary (max 3 sentences) analyzing the resume's strengths and weaknesses.\n"
                "- List key skills present in the resume.\n"
                "- List important skills missing in the resume, based on the job description.\n"
                "Be structured, clear, and to the point. Respond in this format:\n"
                "Summary:\n<summary>\nSkills Present:\n- skill1\n- skill2\nSkills Missing:\n- skill1\n- skill2"
            )
        },
        {
            "role": "user",
            "content": f"Job Description:\n{job_description}\n\nResume:\n{resume}"
        }
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    content = response.choices[0].message.content.strip()

    analysis = {
        "resume_summary": "",
        "skills_present": [],
        "skills_missing": []
    }

    lines = content.splitlines()
    current_section = None

    for line in lines:
        if line.lower().startswith("summary"):
            current_section = "resume_summary"
            analysis[current_section] = ""
        elif line.lower().startswith("skills present"):
            current_section = "skills_present"
        elif line.lower().startswith("skills missing"):
            current_section = "skills_missing"
        elif current_section == "resume_summary":
            analysis[current_section] += " " + line.strip()
        elif current_section in ["skills_present", "skills_missing"]:
            if line.strip().startswith("-"):
                analysis[current_section].append(line.strip("- ").strip())

    return analysis



def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (norm(a) * norm(b))

def search_similar_resumes(job_embedding: np.ndarray, top_k=5):
    scores = [cosine_similarity(job_embedding, emb) for emb in resume_embeddings]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [resume_texts[i] for i in top_indices]

@app.post("/evaluate-resumes/")
async def evaluate_resumes(
    job_description: str = Form(...),
    resume_pdfs: List[UploadFile] = File(...)
):
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

            reports.append({
                "filename": resume_pdf.filename,
                "matched_resumes": top_resumes,
                "suggested_job_role": job_role,
                "resume_summary": resume_analysis["resume_summary"],
                "skills_present": resume_analysis["skills_present"],
                "skills_missing": resume_analysis["skills_missing"],
                "score_out_of_100": score,
                "status": "Passed" if score >= 60 else "Needs Improvement"
            })

        except Exception as e:
            reports.append({
                "filename": resume_pdf.filename,
                "error": str(e)
            })

    return {"reports": reports}

@app.get("/")
def root():
    return {"message": "CV Evaluator API is running. Use POST /evaluate-resumes/ to evaluate multiple resumes."}
