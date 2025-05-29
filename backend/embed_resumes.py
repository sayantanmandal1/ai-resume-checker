import os
from dotenv import load_dotenv
import pandas as pd
import openai
import numpy as np
import pickle
from openai import OpenAI
# Load environment variables from .env file in current directory
load_dotenv()

# Access OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load CSV from backend folder (current directory)
csv_path = os.path.join(os.getcwd(), "Resume.csv")
df = pd.read_csv(csv_path)

def preprocess_text(text):
    return " ".join(str(text).split())

df['clean_resume'] = df['Resume_str'].apply(preprocess_text)


client = OpenAI()

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding


print("Generating embeddings, this may take a while...")
embeddings = []
for text in df['clean_resume']:
    emb = get_embedding(text)
    embeddings.append(np.array(emb, dtype=np.float32))

embeddings = np.vstack(embeddings)

metadata = df[['ID', 'Category', 'clean_resume']].to_dict(orient='records')

with open("resume_embeddings.pkl", "wb") as f:
    pickle.dump({"embeddings": embeddings, "metadata": metadata}, f)

print("Embeddings and metadata saved.")
