import pickle
import gdown
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
from fastapi.middleware.cors import CORSMiddleware
from numpy.linalg import norm
import fitz  # PyMuPDF for PDF text extraction

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
        {"role": "system", "content": "You are a career advisor. Based on the resume, suggest the most suitable job type or role."},
        {"role": "user", "content": f"Suggest the most suitable job role for this resume:\n\n{resume}"}
    ]
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def score_resume(resume: str, job_description: str) -> int:
    messages = [
        {"role": "system", "content": "You are a strict hiring manager. Score the resume's suitability for the job description from 0 to 100. Be accurate and critical."},
        {"role": "user", "content": f"Job Description:\n{job_description}\n\nResume:\n{resume}\n\nGive only the numeric score."}
    ]
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.2
    )
    content = response.choices[0].message.content.strip()
    try:
        return min(max(int(content.split()[0]), 0), 100)
    except:
        return 0

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (norm(a) * norm(b))

def search_similar_resumes(job_embedding: np.ndarray, top_k=5):
    scores = [cosine_similarity(job_embedding, emb) for emb in resume_embeddings]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [resume_texts[i] for i in top_indices]

@app.post("/evaluate-resume/")
async def evaluate_resume(
    job_description: str = Form(...),
    resume_pdf: UploadFile = File(...)
):
    try:
        pdf_bytes = await resume_pdf.read()
        resume_text = extract_text_from_pdf(pdf_bytes)

        job_embedding = get_embedding(job_description)

        top_resumes = search_similar_resumes(job_embedding)

        job_role = recommend_job_type(resume_text)

        score = score_resume(resume_text, job_description)

        return {
            "matched_resumes": top_resumes,
            "suggested_job_role": job_role,
            "score_out_of_100": score,
            "status": "Passed" if score >= 60 else "Needs Improvement"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "CV Evaluator API is running. Use POST /evaluate-resume/ to evaluate resumes."}
