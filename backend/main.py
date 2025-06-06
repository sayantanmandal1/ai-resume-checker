import os
import pickle
import gdown
import re
import json
import numpy as np
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text, ARRAY, Float, DateTime, Boolean
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional
from numpy.linalg import norm
import fitz
import openai
import logging
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from google.cloud import firestore
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Interview platform URL
INTERVIEW_PLATFORM_URL = os.getenv("INTERVIEW_PLATFORM_URL", "https://ai-interviewer-henna.vercel.app/")

# Configurable threshold
SUITABILITY_THRESHOLD = float(os.getenv("SUITABILITY_THRESHOLD", "75.0"))

# Firebase Admin SDK setup
try:
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if firebase_cred_path and os.path.exists(firebase_cred_path):
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized using service account file.")
    elif all([
        os.getenv("FIREBASE_PROJECT_ID"),
        os.getenv("FIREBASE_PRIVATE_KEY"),
        os.getenv("FIREBASE_CLIENT_EMAIL")
    ]):
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),  # optional
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),  # optional
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL", "")
        }
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized using inline environment config.")
    else:
        logger.warning("Firebase credentials not found. Email integration will be disabled.")
        firebase_admin = None

except Exception as e:
    logger.error(f"Firebase initialization error: {e}")
    firebase_admin = None

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class ResumeReport(Base):
    __tablename__ = "resume_reports"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    candidate_email = Column(String)
    candidate_name = Column(String)
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
    email_sent = Column(Boolean, default=False)
    interview_username = Column(String)
    interview_password = Column(String)
    firebase_uid = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def migrate_database():
    """Add new columns if they don't exist"""
    from sqlalchemy import text

    try:
        with engine.connect() as connection:
            # Existing migrations
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

            # New columns for interview integration
            new_columns = [
                ("candidate_email", "VARCHAR(255)"),
                ("candidate_name", "VARCHAR(255)"),
                ("email_sent", "BOOLEAN DEFAULT FALSE"),
                ("interview_username", "VARCHAR(255)"),
                ("interview_password", "VARCHAR(255)"),
                ("firebase_uid", "VARCHAR(255)"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]

            for column_name, column_type in new_columns:
                try:
                    connection.execute(text(f"ALTER TABLE resume_reports ADD COLUMN {column_name} {column_type}"))
                    logger.info(f"Added {column_name} column")
                except Exception:
                    logger.info(f"{column_name} column already exists")

            connection.commit()
    except Exception as e:
        logger.error(f"Migration error: {e}")

Base.metadata.create_all(bind=engine)
migrate_database()

# Skill taxonomy (keeping the existing one)
SKILL_TAXONOMY = {
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
    "React": ["reactjs", "react.js", "react js", "react native"],
    "Vue": ["vuejs", "vue.js", "vue js"],
    "Angular": ["angularjs", "angular.js", "angular js", "angular 2+"],
    "Svelte": ["sveltejs", "svelte.js"],
    "Next.js": ["nextjs", "next js", "next.js"],
    "Nuxt.js": ["nuxtjs", "nuxt js", "nuxt.js"],
    "Node.js": ["nodejs", "node js", "node", "expressjs", "express.js"],
    "Django": ["django rest", "django rest framework", "drf"],
    "Flask": ["flask python"],
    "FastAPI": ["fast api", "fastapi python"],
    "Spring Boot": ["springboot", "spring", "spring framework"],
    "ASP.NET": ["asp.net", "asp net", "dotnet", ".net", "asp.net mvc", "asp.net core"],
    "Laravel": ["laravel php"],
    "Ruby on Rails": ["rails", "ror", "ruby rails"],
    "MySQL": ["my sql", "mysql database"],
    "PostgreSQL": ["postgres", "postgresql", "psql"],
    "MongoDB": ["mongo", "mongo db", "mongodb atlas"],
    "Redis": ["redis cache", "redis db"],
    "SQLite": ["sqlite3", "sqlite database"],
    "Oracle": ["oracle db", "oracle database"],
    "SQL Server": ["ms sql", "microsoft sql server", "mssql", "ms sql server"],
    "Cassandra": ["apache cassandra"],
    "DynamoDB": ["aws dynamodb", "amazon dynamodb"],
    "AWS": ["amazon web services", "amazon aws", "aws cloud"],
    "Azure": ["microsoft azure", "azure cloud"],
    "GCP": ["google cloud platform", "google cloud", "gcloud"],
    "Heroku": ["heroku cloud"],
    "DigitalOcean": ["digital ocean"],
    "Docker": ["docker container", "dockerization"],
    "Kubernetes": ["k8s", "kube", "kubernetes orchestration"],
    "Jenkins": ["jenkins ci/cd", "jenkins pipeline"],
    "Git": ["github", "gitlab", "git version control"],
    "CI/CD": ["continuous integration", "continuous deployment", "github actions"],
    "Terraform": ["terraform iac", "infrastructure as code"],
    "Ansible": ["ansible automation"],
    "React Native": ["react-native", "rn"],
    "Flutter": ["flutter dart", "dart flutter"],
    "iOS": ["ios development", "iphone app"],
    "Android": ["android development", "android studio"],
    "TensorFlow": ["tensorflow", "tf"],
    "PyTorch": ["pytorch", "torch"],
    "Pandas": ["pandas python"],
    "NumPy": ["numpy", "numerical python"],
    "Scikit-learn": ["sklearn", "scikit learn"],
    "OpenCV": ["opencv", "computer vision"],
    "FAISS": ["facebook ai similarity search"],
    "LangChain": ["langchain", "lang chain"],
    "HTML": ["html5", "html 5", "hypertext markup"],
    "CSS": ["css3", "css 3", "cascading style sheets"],
    "SASS": ["scss", "sass css"],
    "Bootstrap": ["bootstrap css", "bootstrap framework"],
    "Tailwind": ["tailwindcss", "tailwind css"],
    "jQuery": ["jquery", "jquery js"],
    "AJAX": ["ajax requests", "asynchronous javascript"],
    "Jest": ["jest testing", "jest js"],
    "Pytest": ["pytest python", "py.test"],
    "Selenium": ["selenium webdriver", "selenium automation"],
    "Cypress": ["cypress testing", "cypress e2e"],
    "JUnit": ["junit testing", "junit java"],
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

def extract_email_from_resume(text: str) -> Optional[str]:
    """Extract email address from resume text"""
    email_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    ]
    
    for pattern in email_patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return the first valid email found
            for email in matches:
                if len(email.split('@')) == 2 and '.' in email.split('@')[1]:
                    return email.lower().strip()
    
    return None

def extract_name_from_resume(text: str) -> Optional[str]:
    """Extract candidate name from resume text using GPT"""
    prompt = f"""
    Extract the candidate's full name from this resume text. Return ONLY the name, nothing else.
    If multiple names are present, return the main candidate's name (usually at the top).
    
    Resume text (first 500 characters):
    {text[:500]}
    
    Name:
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=50
        )
        
        name = response.choices[0].message.content.strip()
        # Clean up the name (remove titles, extra text)
        name = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof)\.?\s*', '', name, flags=re.IGNORECASE)
        name = name.split('\n')[0].strip()
        
        return name if name and len(name.split()) <= 4 else None
    except Exception as e:
        logger.error(f"Error extracting name: {e}")
        return None

def generate_credentials() -> Tuple[str, str]:
    """Generate random username and password for interview platform"""
    # Generate username: candidate_ + random string
    username = "candidate_" + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    
    # Generate secure password
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    return username, password

load_dotenv()  # Load from .env

firebase_credentials = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": "dummy-key-id",  # Not used but required
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
}

credentials = service_account.Credentials.from_service_account_info(firebase_credentials)


def is_username_taken(username: str) -> bool:
    try:
        return db.collection("usernames").document(username).get().exists
    except Exception as e:
        logger.error(f"Error checking if username is taken: {e}")
        return True
# Now initialize Firestore with credentials
db = firestore.Client(credentials=credentials, project=os.getenv("FIREBASE_PROJECT_ID"))

def save_username_mapping(username: str, uid: str, email: str) -> bool:
    try:
        doc_ref = db.collection("usernames").document(username)
        doc_ref.set({
            "uid": uid,
            "email": email,
            "createdAt": firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        logger.error(f"Failed to save username mapping: {e}")
        return False

def get_username_by_uid(uid: str) -> Optional[str]:
    try:
        query = db.collection("usernames").where("uid", "==", uid).limit(1).stream()
        for doc in query:
            return doc.id
        return None
    except Exception as e:
        logger.error(f"Error fetching username for UID {uid}: {e}")
        return None


def create_firebase_user(email: str, password: str, name: str, username: str) -> Optional[Tuple[str, str]]:
    """Create Firebase user or reuse existing one. Save username mapping in Firestore. Return (UID, username)."""
    if not firebase_admin:
        logger.warning("Firebase not initialized")
        return None

    if is_username_taken(username):
        logger.warning(f"Username {username} is already taken.")
        return None

    try:
        # Create a new Firebase user
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=name,
            email_verified=False
        )
        logger.info(f"Created Firebase user: {user_record.uid}")

        save_username_mapping(username, user_record.uid, email)
        return user_record.uid, username

    except firebase_auth.EmailAlreadyExistsError:
        logger.warning(f"User with email {email} already exists.")

        try:
            existing_user = firebase_auth.get_user_by_email(email)
            uid = existing_user.uid

            username_from_db = get_username_by_uid(uid)
            if not username_from_db:
                logger.info(f"No existing username mapping found, saving new mapping.")
                save_username_mapping(username, uid, email)
                username_from_db = username

            # Don't reset password by default – optional
            logger.info(f"Using existing user without resetting password for {email}")
            return uid, username_from_db

        except Exception as e:
            logger.error(f"Failed to fetch/update existing user: {e}")
            return None

    except Exception as e:
        logger.error(f"Error creating Firebase user: {e}")
        return None


    

def send_interview_email(candidate_email: str, candidate_name: str, username: str, password: str, skills: list) -> bool:
    """Send interview invitation email to candidate"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured")
        return False

    try:
        # Normalize skills input
        if isinstance(skills, str):
            # If skills is a string, split by commas
            skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        elif isinstance(skills, list):
            # If skills is a list of single-character strings, likely a mistaken split of a string
            if all(isinstance(s, str) and len(s) == 1 for s in skills):
                # Join back and split properly
                skills_str = "".join(skills)
                skills = [skill.strip() for skill in skills_str.split(',') if skill.strip()]
            else:
                # Clean each skill string (trim spaces)
                skills = [skill.strip() for skill in skills if isinstance(skill, str) and skill.strip()]

        skills_text = ", ".join(skills[:10])  # Limit to first 10 skills

        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = candidate_email
        msg['Subject'] = "Interview Invitation - Technical Round"

        body = f"""
Dear {candidate_name or 'Candidate'},

Congratulations! Based on your CV, you have been shortlisted for a round of technical interview.

We were impressed by your skills in: {skills_text}

Please use the following link and credentials to login and start answering the questions:

🔗 Interview Platform: {INTERVIEW_PLATFORM_URL}

📝 Login Credentials:
   Username: {username}
   Password: {password}

⏰ The interview session will be tailored to your skillset and typically takes 30-45 minutes.

📋 Instructions:
1. Click on the interview platform link
2. Login using the provided credentials
3. The system will automatically start asking questions based on your skills
4. Answer honestly and to the best of your ability
5. Complete all questions in the session

Good luck with your interview!

Best regards,
Hiring Team

---
This is an automated message. Please do not reply to this email.
"""
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, candidate_email, msg.as_string())
        server.quit()

        logger.info(f"Interview email sent successfully to {candidate_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending email to {candidate_email}: {e}")
        return False


# Keep all existing functions (normalize_skill, extract_skills_with_gpt, etc.)
def normalize_skill(skill: str) -> str:
    """Normalize skills using comprehensive taxonomy"""
    if not skill or not skill.strip():
        return ""

    skill_clean = skill.strip().lower()

    for canonical, variants in SKILL_TAXONOMY.items():
        if skill_clean == canonical.lower():
            return canonical
        for variant in variants:
            if skill_clean == variant.lower():
                return canonical

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

        if content.startswith('[') and content.endswith(']'):
            skills = json.loads(content)
            return [skill.strip() for skill in skills if skill and isinstance(skill, str)]
        else:
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
                if 0 <= years <= 50:  
                    return years
            except (ValueError, IndexError):
                continue

    return 0

def calculate_experience_score(resume_text: str, jd_text: str, skills: List[str]) -> Tuple[float, Dict[str, Dict]]:
    """Calculate experience score based on skill-experience matching"""
    jd_requirements = {}
    for skill in skills:
        years = extract_experience_years(jd_text, skill)
        if years > 0:
            jd_requirements[skill] = years

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
            score = 20
        elif candidate_years >= required_years * 0.8 and candidate_years <= required_years * 1.5:
            score = 100
        elif candidate_years >= required_years * 0.6 and candidate_years < required_years * 0.8:
            score = 75
        elif candidate_years >= required_years * 1.5 and candidate_years <= required_years * 2:
            score = 85
        elif candidate_years < required_years * 0.6:
            score = 40
        else:
            score = 60

        total_score += score

    other_skills = [s for s in skills if s not in jd_requirements and candidate_experience.get(s, 0) > 0]
    bonus = min(len(other_skills) * 5, 20)

    final_score = (total_score / skill_count) + bonus if skill_count > 0 else 70
    final_score = min(max(final_score, 0), 100)

    return final_score, {"jd_requirements": jd_requirements, "candidate_experience": candidate_experience}

def calculate_skill_match_score(resume_skills: List[str], jd_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    """Calculate skill matching score using vector similarity and exact matching"""
    if not jd_skills:
        return 70.0, resume_skills, []

    resume_normalized = [normalize_skill(skill) for skill in resume_skills]
    jd_normalized = [normalize_skill(skill) for skill in jd_skills]

    resume_normalized = [s for s in resume_normalized if s]
    jd_normalized = [s for s in jd_normalized if s]

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
            jd_words = set(jd_skill.lower().split())
            for resume_skill in resume_normalized:
                resume_words = set(resume_skill.lower().split())

                if len(jd_words.intersection(resume_words)) / len(jd_words) >= 0.5:
                    matching_skills.append(jd_skill)
                    found = True
                    break

        if not found:
            missing_skills.append(jd_skill)

    if len(jd_normalized) == 0:
        skill_match_percentage = 85.0
    else:
        skill_match_percentage = (len(matching_skills) / len(jd_normalized)) * 100

    additional_skills = len([s for s in resume_normalized if s not in jd_normalized])
    bonus = min(additional_skills * 2, 15)

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
        text = text.replace("\n", " ")[:8000]
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
    skill_weight = 0.4
    experience_weight = 0.4
    relevance_weight = 0.2

    try:
        resume_embedding = get_embedding(resume_text)
        jd_embedding = get_embedding(jd_text)
        relevance_score = cosine_similarity(resume_embedding, jd_embedding) * 100
    except Exception:
        relevance_score = 60.0

    final_score = (
        skill_score * skill_weight +
        experience_score * experience_weight +
        relevance_score * relevance_weight
    )

    return min(max(int(round(final_score)), 0), 100)

app = FastAPI(title="Advanced Resume Evaluator with Interview Integration", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_embeddings = []
resume_texts = []

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
    """Evaluate resumes against job description with comprehensive scoring and interview integration"""
    session = SessionLocal()
    reports = []
    interview_invitations_sent = 0

    try:
        jd_skills = extract_skills_with_gpt(job_description, "job description")
        logger.info(f"Extracted {len(jd_skills)} skills from job description: {jd_skills}")

        job_embedding = get_embedding(job_description)

        for resume_pdf in resume_pdfs:
            try:
                logger.info(f"Processing resume: {resume_pdf.filename}")

                pdf_bytes = await resume_pdf.read()
                resume_text = extract_text_from_pdf(pdf_bytes)

                if not resume_text.strip():
                    reports.append({
                        "filename": resume_pdf.filename,
                        "error": "Could not extract text from PDF"
                    })
                    continue

                # Extract candidate information
                candidate_email = extract_email_from_resume(resume_text)
                candidate_name = extract_name_from_resume(resume_text)

                resume_skills = extract_skills_with_gpt(resume_text, "resume")
                logger.info(f"Extracted {len(resume_skills)} skills from resume: {resume_skills}")

                normalized_resume_skills = [normalize_skill(skill) for skill in resume_skills]
                normalized_jd_skills = [normalize_skill(skill) for skill in jd_skills]

                skill_score, matching_skills, missing_skills = calculate_skill_match_score(
                    normalized_resume_skills, normalized_jd_skills
                )

                experience_score, exp_details = calculate_experience_score(
                    resume_text, job_description, normalized_jd_skills
                )

                final_score = calculate_final_score(
                    skill_score, experience_score, resume_text, job_description
                )

                if final_score >= 75:
                    status = "Excellent Match"
                elif final_score >= 60:
                    status = "Good Match"
                elif final_score >= 40:
                    status = "Needs Improvement"
                else:
                    status = "Poor Match"

                resume_summary = generate_resume_summary(resume_text, job_description)
                suggested_job_role = recommend_job_type(resume_text)

                # Only prepare credentials for eligible candidates, but don't send email yet
                interview_username = None
                interview_password = None
                firebase_uid = None

                if final_score >= SUITABILITY_THRESHOLD and candidate_email:
                    try:
                        # Generate credentials but don't send email
                        interview_username, interview_password = generate_credentials()
                        
                        # Create Firebase user but don't send email
                        firebase_uid = create_firebase_user(
                            candidate_email, 
                            interview_password, 
                            candidate_name or "Candidate",
                            interview_username
                        )
                        
                        if firebase_uid:
                            logger.info(f"Firebase user created for {candidate_email} - ready for interview invitation")
                        else:
                            logger.warning(f"Failed to create Firebase user for {candidate_email}")
                            
                    except Exception as e:
                        logger.error(f"Error creating Firebase user for {candidate_email}: {e}")

                similar_resumes = search_similar_resumes(job_embedding, top_k=3)

                # Create database record
                report_id = None
                try:
                    report = ResumeReport(
                        filename=resume_pdf.filename,
                        candidate_email=candidate_email,
                        candidate_name=candidate_name,
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
                        status=status,
                        email_sent=False,  # Email not sent automatically
                        interview_username=interview_username,
                        interview_password=interview_password,
                        firebase_uid=firebase_uid
                    )

                    session.add(report)
                    session.commit()
                    session.refresh(report)  # This ensures we get the generated ID
                    report_id = report.id  # Capture the database ID
                    logger.info(f"Successfully saved report for {resume_pdf.filename} with ID: {report_id}")

                except Exception as db_error:
                    logger.error(f"Database save error for {resume_pdf.filename}: {db_error}")
                    session.rollback()

                # Add to response with database ID
                reports.append({
                    "id": report_id,  # IMPORTANT: Include the database ID
                    "filename": resume_pdf.filename,
                    "candidate_email": candidate_email,
                    "candidate_name": candidate_name,
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
                    "interview_eligible": final_score >= SUITABILITY_THRESHOLD,
                    "email_sent": False,  # No automatic email sending
                    "interview_credentials": {
                        "username": interview_username,
                        "password": interview_password
                    } if interview_username else None,
                    "matched_resumes_preview": similar_resumes[:2]
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
        "suitability_threshold": SUITABILITY_THRESHOLD,
        "interview_invitations_sent": 0,  # No automatic emails sent
        "reports": reports
    }


@app.post("/resend-interview-invitation/{candidate_id}")
def resend_interview_invitation(candidate_id: int):
    """Send interview invitation to a candidate (only when button is clicked)"""
    session = SessionLocal()
    try:
        candidate = session.query(ResumeReport).filter(ResumeReport.id == candidate_id).first()
        if not candidate:
            return {"error": "Candidate not found"}
        
        if not candidate.candidate_email:
            return {"error": "No email address found for candidate"}
        
        if candidate.score_out_of_100 < SUITABILITY_THRESHOLD:
            return {"error": f"Candidate score ({candidate.score_out_of_100}) below threshold ({SUITABILITY_THRESHOLD})"}
        
        # Generate new credentials if not exist
        if not candidate.interview_username or not candidate.interview_password:
            username, password = generate_credentials()
            candidate.interview_username = username
            candidate.interview_password = password
            
            # Create Firebase user if not exists
            if not candidate.firebase_uid:
                firebase_uid = create_firebase_user(
                    candidate.candidate_email,
                    password,
                    candidate.candidate_name or "Candidate",
                    username
                )
                candidate.firebase_uid = firebase_uid
        
        # Send email only when this endpoint is called (button click)
        email_sent = send_interview_email(
            candidate.candidate_email,
            candidate.candidate_name,
            candidate.interview_username,
            candidate.interview_password,
            candidate.matching_skills or []
        )
        
        candidate.email_sent = email_sent
        session.commit()
        
        if email_sent:
            logger.info(f"Interview invitation sent to {candidate.candidate_email} via button click")
        
        return {
            "message": "Interview invitation sent successfully" if email_sent else "Failed to send invitation",
            "email_sent": email_sent,
            "candidate_email": candidate.candidate_email
        }
        
    except Exception as e:
        logger.error(f"Error sending invitation: {e}")
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()


@app.get("/interview-candidates/")
def get_interview_candidates():
    """Get candidates who received interview invitations"""
    session = SessionLocal()
    try:
        candidates = session.query(ResumeReport).filter(
            ResumeReport.score_out_of_100 >= SUITABILITY_THRESHOLD,
            ResumeReport.candidate_email.isnot(None)
        ).order_by(ResumeReport.created_at.desc()).all()
        
        return {
            "total_interview_candidates": len(candidates),
            "threshold": SUITABILITY_THRESHOLD,
            "candidates": [
                {
                    "id": candidate.id,
                    "candidate_name": candidate.candidate_name,
                    "candidate_email": candidate.candidate_email,
                    "score": candidate.score_out_of_100,
                    "status": candidate.status,
                    "suggested_job_role": candidate.suggested_job_role,
                    "email_sent": candidate.email_sent,
                    "interview_username": candidate.interview_username,
                    "matching_skills": candidate.matching_skills,
                    "created_at": candidate.created_at.isoformat() if candidate.created_at else None
                }
                for candidate in candidates
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching interview candidates: {e}")
        return {"error": str(e)}
    finally:
        session.close()

@app.put("/update-threshold/")
def update_threshold(new_threshold: float):
    """Update the suitability threshold"""
    global SUITABILITY_THRESHOLD
    if 0 <= new_threshold <= 100:
        SUITABILITY_THRESHOLD = new_threshold
        return {"message": f"Threshold updated to {new_threshold}%", "new_threshold": SUITABILITY_THRESHOLD}
    else:
        return {"error": "Threshold must be between 0 and 100"}

@app.get("/")
def root():
    return {
        "message": "Advanced CV Evaluator API v3.0 with Interview Integration",
        "endpoints": {
            "evaluate": "POST /evaluate-resumes/",
            "candidates": "GET /candidates/",
            "candidate_details": "GET /candidates/{id}",
            "interview_candidates": "GET /interview-candidates/",
            "resend_invitation": "POST /resend-interview-invitation/{id}",
            "update_threshold": "PUT /update-threshold/",
            "health": "GET /"
        },
        "features": [
            "Advanced skill extraction using GPT-4",
            "Comprehensive skill normalization",
            "Experience-based scoring",
            "Vector similarity matching",
            "Detailed skill gap analysis",
            "Automatic email extraction from resumes",
            "Interview invitation system",
            "Firebase user creation",
            "Configurable suitability threshold"
        ],
        "current_threshold": SUITABILITY_THRESHOLD
    }

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