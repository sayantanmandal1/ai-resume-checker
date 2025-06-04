import os
import pickle
import gdown
import re
import json
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text, ARRAY, Float
from dotenv import load_dotenv
from typing import List, Dict, Tuple
from numpy.linalg import norm
import fitz
import openai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Setup database ORM
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
    experience_score = Column(Float, default=0.0)
    skill_match_score = Column(Float, default=0.0)
    status = Column(String)

# Database migration function
def migrate_database():
    """Add new columns if they don't exist"""
    from sqlalchemy import text
    
    try:
        with engine.connect() as connection:
            # Check if columns exist and add them if they don't
            try:
                connection.execute(text("ALTER TABLE resume_reports ADD COLUMN experience_score FLOAT DEFAULT 0.0"))
                logger.info("Added experience_score column")
            except Exception:
                logger.info("experience_score column already exists")
            
            try:
                connection.execute(text("ALTER TABLE resume_reports ADD COLUMN skill_match_score FLOAT DEFAULT 0.0"))
                logger.info("Added skill_match_score column")
            except Exception:
                logger.info("skill_match_score column already exists")
            
            connection.commit()
    except Exception as e:
        logger.error(f"Migration error: {e}")

# Create tables and migrate
Base.metadata.create_all(bind=engine)
migrate_database()

# Comprehensive skill taxonomy for normalization
SKILL_TAXONOMY = {
    # Programming Languages
    "JavaScript": ["js", "javascript", "java script", "ecmascript"],
    "TypeScript": ["ts", "typescript", "type script"],
    "Python": ["python3", "py", "python 3"],
    "Java": ["java8", "java 8", "java11", "java 11", "openjdk"],
    "C#": ["c sharp", "csharp", "c#.net", "c# .net"],
    "C++": ["cpp", "c plus plus", "cplusplus"],
    "PHP": ["php7", "php8", "php 7", "php 8"],
    "Ruby": ["ruby on rails", "ror"],
    "Go": ["golang", "go lang"],
    "Rust": ["rust lang"],
    "Swift": ["swift ui", "swiftui"],
    "Kotlin": ["kotlin/java"],
    
    # Frontend Frameworks
    "React": ["reactjs", "react.js", "react js", "react native"],
    "Vue": ["vuejs", "vue.js", "vue js"],
    "Angular": ["angularjs", "angular.js", "angular js", "angular 2+"],
    "Svelte": ["sveltejs", "svelte.js"],
    "Next.js": ["nextjs", "next js", "next.js"],
    "Nuxt.js": ["nuxtjs", "nuxt js", "nuxt.js"],
    
    # Backend Frameworks
    "Node.js": ["nodejs", "node js", "node", "expressjs", "express.js"],
    "Django": ["django rest", "django rest framework", "drf"],
    "Flask": ["flask python"],
    "FastAPI": ["fast api", "fastapi python"],
    "Spring Boot": ["springboot", "spring", "spring framework"],
    "ASP.NET": ["asp.net", "asp net", "dotnet", ".net", "asp.net mvc", "asp.net core"],
    "Laravel": ["laravel php"],
    "Ruby on Rails": ["rails", "ror", "ruby rails"],
    
    # Databases
    "MySQL": ["my sql", "mysql database"],
    "PostgreSQL": ["postgres", "postgresql", "psql"],
    "MongoDB": ["mongo", "mongo db", "mongodb atlas"],
    "Redis": ["redis cache", "redis db"],
    "SQLite": ["sqlite3", "sqlite database"],
    "Oracle": ["oracle db", "oracle database"],
    "SQL Server": ["ms sql", "microsoft sql server", "mssql", "ms sql server"],
    "Cassandra": ["apache cassandra"],
    "DynamoDB": ["aws dynamodb", "amazon dynamodb"],
    
    # Cloud Platforms
    "AWS": ["amazon web services", "amazon aws", "aws cloud"],
    "Azure": ["microsoft azure", "azure cloud"],
    "GCP": ["google cloud platform", "google cloud", "gcloud"],
    "Heroku": ["heroku cloud"],
    "DigitalOcean": ["digital ocean"],
    
    # DevOps & Tools
    "Docker": ["docker container", "dockerization"],
    "Kubernetes": ["k8s", "kube", "kubernetes orchestration"],
    "Jenkins": ["jenkins ci/cd", "jenkins pipeline"],
    "Git": ["github", "gitlab", "git version control"],
    "CI/CD": ["continuous integration", "continuous deployment", "github actions"],
    "Terraform": ["terraform iac", "infrastructure as code"],
    "Ansible": ["ansible automation"],
    
    # Mobile Development
    "React Native": ["react-native", "rn"],
    "Flutter": ["flutter dart", "dart flutter"],
    "iOS": ["ios development", "iphone app"],
    "Android": ["android development", "android studio"],
    
    # Data & AI/ML
    "TensorFlow": ["tensorflow", "tf"],
    "PyTorch": ["pytorch", "torch"],
    "Pandas": ["pandas python"],
    "NumPy": ["numpy", "numerical python"],
    "Scikit-learn": ["sklearn", "scikit learn"],
    "OpenCV": ["opencv", "computer vision"],
    "FAISS": ["facebook ai similarity search"],
    "LangChain": ["langchain", "lang chain"],
    
    # Web Technologies
    "HTML": ["html5", "html 5", "hypertext markup"],
    "CSS": ["css3", "css 3", "cascading style sheets"],
    "SASS": ["scss", "sass css"],
    "Bootstrap": ["bootstrap css", "bootstrap framework"],
    "Tailwind": ["tailwindcss", "tailwind css"],
    "jQuery": ["jquery", "jquery js"],
    "AJAX": ["ajax requests", "asynchronous javascript"],
    
    # Testing
    "Jest": ["jest testing", "jest js"],
    "Pytest": ["pytest python", "py.test"],
    "Selenium": ["selenium webdriver", "selenium automation"],
    "Cypress": ["cypress testing", "cypress e2e"],
    "JUnit": ["junit testing", "junit java"],
    
    # Other Tools
    "Postman": ["postman api"],
    "Swagger": ["swagger api", "openapi"],
    "GraphQL": ["graphql api", "graph ql"],
    "REST API": ["restful api", "rest apis", "restful services"],
    "Microservices": ["micro services", "microservice architecture"],
    "Agile": ["agile methodology", "scrum", "agile development"],
    "Linux": ["ubuntu", "centos", "linux server"],
    "Nginx": ["nginx server", "nginx proxy"],
    "Apache": ["apache server", "apache http"],
}

def normalize_skill(skill: str) -> str:
    """Normalize skills using comprehensive taxonomy"""
    if not skill or not skill.strip():
        return ""
    
    skill_clean = skill.strip().lower()
    
    # Direct match check
    for canonical, variants in SKILL_TAXONOMY.items():
        if skill_clean == canonical.lower():
            return canonical
        for variant in variants:
            if skill_clean == variant.lower():
                return canonical
    
    # Return original with proper capitalization
    return skill.strip().title()

def extract_skills_with_gpt(text: str, context: str = "resume") -> List[str]:
    """Extract skills from resume or job description text using GPT-3.5-turbo."""
    prompt = f"""
Extract ALL technical skills, tools, frameworks, programming languages, databases, and technologies from this {context}.

Include:
- Programming languages (Python, Java, JavaScript, etc.)
- Frameworks and libraries (React, Django, Spring Boot, etc.)
- Databases (MySQL, MongoDB, PostgreSQL, etc.)
- Cloud platforms (AWS, Azure, GCP, etc.)
- DevOps tools (Docker, Kubernetes, Jenkins, etc.)
- Development tools (Git, Postman, etc.)
- Methodologies (Agile, Scrum, etc.)

Return ONLY a JSON array of skills, nothing else.

Example: ["Python", "React", "AWS", "Docker", "MySQL"]

Text to analyze:
```{text[:3000]}```
""".strip()

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()

        # Try parsing strict JSON
        if content.startswith('[') and content.endswith(']'):
            skills = json.loads(content)
            return [skill.strip() for skill in skills if skill and isinstance(skill, str)]
        else:
            # Fallback: line-by-line parsing
            lines = content.split('\n')
            skills = []
            for line in lines:
                line = line.strip().strip('"-\' ')
                if line and not any(prefix in line.lower() for prefix in ["example", "note", "skills"]):
                    skills.append(line)
            return skills[:30]

    except Exception as e:
        logger.error(f"Error extracting skills with GPT: {e}")
        return []

def extract_experience_years(text: str, skill: str) -> int:
    """Extract years of experience for a specific skill"""
    patterns = [
        rf"(\d+)[\+\-\s]*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+)?(?:in\s+|with\s+|using\s+)?{re.escape(skill)}",
        rf"{re.escape(skill)}[\s\w]*?(\d+)[\+\-\s]*(?:years?|yrs?)",
        rf"(\d+)[\+\-\s]*(?:years?|yrs?)[\s\w]*?{re.escape(skill)}",
        rf"{re.escape(skill)}[\s\-:]*(\d+)[\+\-\s]*(?:years?|yrs?)"
    ]
    
    text_lower = text.lower()
    skill.lower()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            try:
                years = int(match.group(1))
                if 0 <= years <= 50:  # Reasonable range
                    return years
            except (ValueError, IndexError):
                continue
    
    return 0

def calculate_experience_score(resume_text: str, jd_text: str, skills: List[str]) -> Tuple[float, Dict[str, Dict]]:
    """Calculate experience score based on skill-experience matching"""
    
    # Extract required experience from job description
    jd_requirements = {}
    for skill in skills:
        years = extract_experience_years(jd_text, skill)
        if years > 0:
            jd_requirements[skill] = years
    
    # Extract candidate experience
    candidate_experience = {}
    for skill in skills:
        years = extract_experience_years(resume_text, skill)
        candidate_experience[skill] = years
    
    if not jd_requirements:
        return 85.0, {"jd_requirements": jd_requirements, "candidate_experience": candidate_experience}
    
    total_score = 0
    skill_count = 0
    
    for skill, required_years in jd_requirements.items():
        candidate_years = candidate_experience.get(skill, 0)
        skill_count += 1
        
        if candidate_years == 0:
            # No experience mentioned
            score = 20
        elif candidate_years >= required_years * 0.8 and candidate_years <= required_years * 1.5:
            # Near perfect match (80%-150% of required)
            score = 100
        elif candidate_years >= required_years * 0.6 and candidate_years < required_years * 0.8:
            # Slightly under-qualified (60%-80% of required)
            score = 75
        elif candidate_years >= required_years * 1.5 and candidate_years <= required_years * 2:
            # Slightly over-qualified (150%-200% of required)
            score = 85
        elif candidate_years < required_years * 0.6:
            # Under-qualified (less than 60% of required)
            score = 40
        else:
            # Highly over-qualified (more than 200% of required)
            score = 60
        
        total_score += score
    
    # Add bonus for skills without specific year requirements
    other_skills = [s for s in skills if s not in jd_requirements and candidate_experience.get(s, 0) > 0]
    bonus = min(len(other_skills) * 5, 20)  # Max 20 points bonus
    
    final_score = (total_score / skill_count) + bonus if skill_count > 0 else 70
    final_score = min(max(final_score, 0), 100)
    
    return final_score, {"jd_requirements": jd_requirements, "candidate_experience": candidate_experience}

def calculate_skill_match_score(resume_skills: List[str], jd_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """Calculate skill matching score using vector similarity and exact matching"""
    
    if not jd_skills:
        return 70.0, resume_skills, []
    
    # Normalize all skills
    resume_normalized = [normalize_skill(skill) for skill in resume_skills]
    jd_normalized = [normalize_skill(skill) for skill in jd_skills]
    
    # Remove empty skills
    resume_normalized = [s for s in resume_normalized if s]
    jd_normalized = [s for s in jd_normalized if s]
    
    # Find exact matches
    matching_skills = []
    missing_skills = []
    
    for jd_skill in jd_normalized:
        found = False
        for resume_skill in resume_normalized:
            if jd_skill.lower() == resume_skill.lower():
                matching_skills.append(jd_skill)
                found = True
                break
        
        if not found:
            # Check for partial/fuzzy matches
            jd_words = set(jd_skill.lower().split())
            for resume_skill in resume_normalized:
                resume_words = set(resume_skill.lower().split())
                # If 50% or more words match, consider it a match
                if len(jd_words.intersection(resume_words)) / len(jd_words) >= 0.5:
                    matching_skills.append(jd_skill)
                    found = True
                    break
        
        if not found:
            missing_skills.append(jd_skill)
    
    # Calculate score
    if len(jd_normalized) == 0:
        skill_match_percentage = 85.0
    else:
        skill_match_percentage = (len(matching_skills) / len(jd_normalized)) * 100
    
    # Bonus for additional relevant skills
    additional_skills = len([s for s in resume_normalized if s not in jd_normalized])
    bonus = min(additional_skills * 2, 15)  # Max 15 points bonus
    
    final_score = min(skill_match_percentage + bonus, 100)
    
    return final_score, matching_skills, missing_skills

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF with better error handling"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return ""

def get_embedding(text: str) -> np.ndarray:
    """Get text embedding using OpenAI"""
    try:
        text = text.replace("\n", " ")[:8000]  # Limit text size
        response = openai.embeddings.create(
            input=[text], 
            model="text-embedding-3-large"
        )
        return np.array(response.data[0].embedding)
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return np.array([])

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    if len(a) == 0 or len(b) == 0:
        return 0.0
    try:
        return np.dot(a, b) / (norm(a) * norm(b))
    except Exception:
        return 0.0

def search_similar_resumes(job_embedding: np.ndarray, top_k=5):
    """Search for similar resumes using embeddings"""
    try:
        scores = [cosine_similarity(job_embedding, emb) for emb in resume_embeddings]
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [resume_texts[i] for i in top_indices]
    except Exception:
        return []

def recommend_job_type(resume: str) -> str:
    """Recommend job type based on resume content"""
    prompt = f"""
    Based on this resume, suggest the most suitable job title in 2-3 words only.
    Focus on the primary skills and experience level.
    
    Resume: {resume[:2000]}
    
    Respond with just the job title, nothing else.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        return response.choices[0].message.content.strip().split("\n")[0]
    except Exception as e:
        logger.error(f"Error recommending job type: {e}")
        return "Software Developer"

def generate_resume_summary(resume_text: str, job_description: str) -> str:
    """Generate a professional summary of the resume"""
    prompt = f"""
    Create a 2-3 sentence professional summary of this candidate based on their resume.
    Focus on their key skills, experience level, and relevant background for the given job.
    
    Job Description:
    {job_description[:1000]}
    
    Resume:
    {resume_text[:2000]}
    
    Summary:
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Professional with relevant technical experience."

def calculate_final_score(skill_score: float, experience_score: float, resume_text: str, jd_text: str) -> int:
    """Calculate final comprehensive score"""
    
    # Weight the scores
    skill_weight = 0.4
    experience_weight = 0.4
    relevance_weight = 0.2
    
    # Calculate relevance score using text similarity
    try:
        resume_embedding = get_embedding(resume_text)
        jd_embedding = get_embedding(jd_text)
        relevance_score = cosine_similarity(resume_embedding, jd_embedding) * 100
    except Exception:
        relevance_score = 60.0
    
    # Weighted final score
    final_score = (
        skill_score * skill_weight +
        experience_score * experience_weight +
        relevance_score * relevance_weight
    )
    
    return min(max(int(round(final_score)), 0), 100)

# Initialize FastAPI app
app = FastAPI(title="Advanced Resume Evaluator", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for embeddings
resume_embeddings = []
resume_texts = []

# Load embeddings on startup
@app.on_event("startup")
async def load_embeddings():
    global resume_embeddings, resume_texts
    try:
        url = "https://drive.google.com/uc?id=1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP"
        output = "resume_embeddings.pkl"
        
        if not os.path.exists(output):
            logger.info("Downloading resume embeddings...")
            gdown.download(url, output, quiet=False)
        
        with open(output, "rb") as f:
            data = pickle.load(f)
            resume_embeddings = data["embeddings"]
            resume_texts = [item["clean_resume"] for item in data["metadata"]]
            
        logger.info(f"Loaded {len(resume_embeddings)} resume embeddings")
    except Exception as e:
        logger.error(f"Error loading embeddings: {e}")
        resume_embeddings = []
        resume_texts = []

@app.post("/evaluate-resumes/")
async def evaluate_resumes(
    job_description: str = Form(...), 
    resume_pdfs: List[UploadFile] = File(...)
):
    """Evaluate resumes against job description with comprehensive scoring"""
    
    session = SessionLocal()
    reports = []
    
    try:
        # Extract skills from job description
        jd_skills = extract_skills_with_gpt(job_description, "job description")
        logger.info(f"Extracted {len(jd_skills)} skills from job description: {jd_skills}")
        
        # Get job embedding for similarity search
        job_embedding = get_embedding(job_description)
        
        for resume_pdf in resume_pdfs:
            try:
                logger.info(f"Processing resume: {resume_pdf.filename}")
                
                # Extract text from PDF
                pdf_bytes = await resume_pdf.read()
                resume_text = extract_text_from_pdf(pdf_bytes)
                
                if not resume_text.strip():
                    reports.append({
                        "filename": resume_pdf.filename,
                        "error": "Could not extract text from PDF"
                    })
                    continue
                
                # Extract skills from resume
                resume_skills = extract_skills_with_gpt(resume_text, "resume")
                logger.info(f"Extracted {len(resume_skills)} skills from resume: {resume_skills}")
                
                # Normalize skills
                normalized_resume_skills = [normalize_skill(skill) for skill in resume_skills]
                normalized_jd_skills = [normalize_skill(skill) for skill in jd_skills]
                
                # Calculate skill match score
                skill_score, matching_skills, missing_skills = calculate_skill_match_score(
                    normalized_resume_skills, normalized_jd_skills
                )
                
                # Calculate experience score
                experience_score, exp_details = calculate_experience_score(
                    resume_text, job_description, normalized_jd_skills
                )
                
                # Calculate final comprehensive score
                final_score = calculate_final_score(
                    skill_score, experience_score, resume_text, job_description
                )
                
                # Determine status
                if final_score >= 75:
                    status = "Excellent Match"
                elif final_score >= 60:
                    status = "Good Match"
                elif final_score >= 40:
                    status = "Needs Improvement"
                else:
                    status = "Poor Match"
                
                # Generate summary and job recommendation
                resume_summary = generate_resume_summary(resume_text, job_description)
                suggested_job_role = recommend_job_type(resume_text)
                
                # Find similar resumes
                similar_resumes = search_similar_resumes(job_embedding, top_k=3)
                
                # Create report with error handling for database save
                try:
                    report = ResumeReport(
                        filename=resume_pdf.filename,
                        suggested_job_role=suggested_job_role,
                        resume_summary=resume_summary,
                        skills_present=resume_skills,
                        skills_missing=missing_skills,
                        normalized_skills=normalized_resume_skills,
                        matching_skills=matching_skills,
                        missing_skills=missing_skills,
                        score_out_of_100=final_score,
                        experience_score=experience_score,
                        skill_match_score=skill_score,
                        status=status
                    )
                    
                    session.add(report)
                    session.commit()
                    logger.info(f"Successfully saved report for {resume_pdf.filename}")
                    
                except Exception as db_error:
                    logger.error(f"Database save error for {resume_pdf.filename}: {db_error}")
                    session.rollback()
                    # Continue processing even if DB save fails
                
                # Prepare response (regardless of DB save status)
                reports.append({
                    "filename": resume_pdf.filename,
                    "suggested_job_role": suggested_job_role,
                    "resume_summary": resume_summary,
                    "skills_present": resume_skills,
                    "skills_missing": missing_skills,
                    "normalized_skills": normalized_resume_skills,
                    "matching_skills": matching_skills,
                    "missing_skills": missing_skills,
                    "score_out_of_100": final_score,
                    "skill_match_score": round(skill_score, 1),
                    "experience_score": round(experience_score, 1),
                    "experience_details": exp_details,
                    "status": status,
                    "matched_resumes_preview": similar_resumes[:2]  # Limit for response size
                })
                
                logger.info(f"Successfully processed {resume_pdf.filename} - Score: {final_score}")
                
            except Exception as e:
                logger.error(f"Error processing {resume_pdf.filename}: {e}")
                reports.append({
                    "filename": resume_pdf.filename,
                    "error": f"Processing error: {str(e)}"
                })
    
    except Exception as e:
        logger.error(f"Error in evaluation process: {e}")
        return {"error": f"Evaluation failed: {str(e)}"}
    
    finally:
        session.close()
    
    return {
        "message": f"Analysis complete for {len(reports)} resumes",
        "job_skills_extracted": jd_skills,
        "reports": reports
    }

@app.get("/")
def root():
    return {
        "message": "Advanced CV Evaluator API v2.0 is running",
        "endpoints": {
            "evaluate": "POST /evaluate-resumes/",
            "health": "GET /"
        },
        "features": [
            "Advanced skill extraction using GPT-4",
            "Comprehensive skill normalization",
            "Experience-based scoring",
            "Vector similarity matching",
            "Detailed skill gap analysis"
        ]
    }

# Manual database migration endpoint (optional)
@app.post("/migrate-database/")
def manual_migrate():
    """Manually trigger database migration"""
    try:
        migrate_database()
        return {"message": "Database migration completed successfully"}
    except Exception as e:
        return {"error": f"Migration failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)