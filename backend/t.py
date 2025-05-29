import requests

url = "http://localhost:8000/evaluate-resume/"

files = {
    "resume_pdf": open(r"C:\Users\msaya\Downloads\ressss\resume4.pdf", "rb")
}

data = {
    "job_description": "Software developer"
}

response = requests.post(url, data=data, files=files)
print(response.status_code)
print(response.json())
