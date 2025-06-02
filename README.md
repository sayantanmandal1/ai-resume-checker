# 🧠 AI Resume Evaluation System

## 📘 Overview

**AI Resume Checker** is a full-stack intelligent system that evaluates candidate resumes against job descriptions and returns a score from 0 to 100, along with a pass/fail verdict. It leverages OpenAI's GPT-4 API for semantic analysis and scoring.

The system is deployed using Docker containers on [Render](https://ai-resume-checker-1-tsrs.onrender.com), and all CI/CD operations—linting, testing, deployment—are automated via GitHub Actions. Live at [Vercel](https://ai-resume-checker-nine.vercel.app/)

---

## 🛠 Tech Stack

### Frontend
- **React** (with `create-react-app`)
- **serve** for static hosting

### Backend
- **FastAPI** – REST API for evaluation
- **OpenAI GPT-4 API**
- **FAISS** (planned for vector similarity)
- **Pydantic** – for data modeling and validation

### DevOps / Infra
- **Docker**
- **Render** (Docker deployment)
- **GitHub Actions** (CI/CD)
- **Google Drive** – Embedding and sample resume files

---

## 🧩 Project Structure

```bash
ai-resume-checker/
├── backend/
│   ├── main.py
│   ├── embed_resumes.py
│   ├── scrape_resumes.py
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_main.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
├── frontend.Dockerfile
├── backend.Dockerfile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci-cd.yml
└── README.md
```

---

## 🧪 Prompt-Based Testing

### Flow
1. Upload a PDF resume and job description.
2. FastAPI extracts the PDF content and generates a prompt.
3. The prompt is passed to **OpenAI GPT-4** with the following system instruction:
   ```
   You are a strict hiring manager. Score the resume's suitability for the job description from 0 to 100.
   ```
4. The numeric score is returned and parsed into:
   ```json
   {
     "score_out_of_100": 72,
     "status": "Passed"
   }
   ```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

### Workflow Summary
- **Linting**:
  - Uses [ruff](https://github.com/astral-sh/ruff) to check Python code quality
- **Testing**:
  - Downloads:
    - [`resume_embeddings.pkl`](https://drive.google.com/file/d/1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP/view)
    - [`sample_resume.pdf`](https://drive.google.com/file/d/1Fd9jE7qaoEIBr6i-P-56DDno2l483Rdp/view)
  - Uses `pytest` with FastAPI’s `TestClient`
  - Checks file download + API behavior
- **Deployment**:
  - Triggers deployment using a `RENDER_DEPLOY_HOOK` on Render
  - Embedding file is freshly downloaded on deploy

---

## 📄 Example Test

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_resume_evaluation_endpoint():
    if not os.path.exists("resume_embeddings.pkl"):
        download_file_from_gdrive("1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP", "resume_embeddings.pkl")

    if not os.path.exists("sample_resume.pdf"):
        download_file_from_gdrive("1Fd9jE7qaoEIBr6i-P-56DDno2l483Rdp", "sample_resume.pdf")

    with open("sample_resume.pdf", "rb") as pdf:
        response = client.post(
            "/evaluate-resume/",
            files={"resume_pdf": ("sample_resume.pdf", pdf, "application/pdf")},
            data={"job_description": "Software Developer"},
        )
    assert response.status_code == 200
    assert "score_out_of_100" in response.json()
```

---

## 🐳 Docker Deployment

### Backend Dockerfile

```Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/ /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/ /app/

RUN npm install && npm run build

RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
```

---

## 🚀 Live Demo

- [AI Resume Checker – Vercel](https://ai-resume-checker-nine.vercel.app/)

---

## 📎 Resources

- 🧠 [Embedding File (pkl)](https://drive.google.com/file/d/1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP/view)
- 📄 [Sample Resume (PDF)](https://drive.google.com/file/d/1Fd9jE7qaoEIBr6i-P-56DDno2l483Rdp/view)
- 🧪 [GitHub Repository](https://github.com/sayantanmandal1/ai-resume-checker)

---

## 📌 Future Improvements

- Upload frontend UI for interactive use
- Add authentication and user dashboards
- Enable vector search fallback using FAISS
- Add score explanation with OpenAI function calling
