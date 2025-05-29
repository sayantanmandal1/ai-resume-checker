from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_resume_evaluation_endpoint():
    with open("resume_embeddings.pkl", "rb") as f:
        assert f.read(10) != b'', "Embedding file seems empty"

    with open("sample_resume.pdf", "rb") as pdf:
        response = client.post(
            "/evaluate-resume/",
            files={"resume_pdf": ("sample_resume.pdf", pdf, "application/pdf")},
            data={"job_description": "Python Developer"},
        )
    assert response.status_code == 200
    assert "score_out_of_100" in response.json()
    assert response.json()["status"] in ["Passed", "Failed"]
