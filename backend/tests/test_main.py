from fastapi.testclient import TestClient
from backend.main import app
import requests
import os

client = TestClient(app)

def download_file_from_gdrive(file_id: str, dest_path: str):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = requests.get(url)
    if response.status_code == 200:
        with open(dest_path, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(f"Failed to download file {file_id}")

def test_resume_evaluation_endpoint():
    if not os.path.exists("resume_embeddings.pkl"):
        download_file_from_gdrive("1oM5yvJy3ugBHZ_RZOhZxlV3cESZwRZKP", "resume_embeddings.pkl")

    if not os.path.exists("sample_resume.pdf"):
        download_file_from_gdrive("1Fd9jE7qaoEIBr6i-P-56DDno2l483Rdp", "sample_resume.pdf")

    with open("resume_embeddings.pkl", "rb") as f:
        assert f.read(10) != b'', "Embedding file seems empty"

    with open("sample_resume.pdf", "rb") as pdf:
        response = client.post(
            "/evaluate-resumes/",
            files=[("resume_pdfs", ("sample_resume.pdf", pdf, "application/pdf"))],
            data={"job_description": "Software Developer"},
        )

    data = response.json()
    assert response.status_code == 200
    assert "score_out_of_100" in data["reports"][0]
    assert data["reports"][0]["status"] in ["Passed", "Failed"]

