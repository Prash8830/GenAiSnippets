import os
import requests
import numpy as np
from langchain.embeddings.base import Embeddings

# Set your Hugging Face API token

os.environ["HUGGINGFACEHUB_API_TOKEN"] = HF_TOKEN
API_URL = "https://api-inference.huggingface.co/models/intfloat/multilingual-e5-large-instruct"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

class HFInferenceEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        response = requests.post(API_URL, headers=HEADERS, json={"inputs": text, "options": {"wait_for_model": True}})
        response.raise_for_status()  # Raise an exception for HTTP errors
        return np.array(response.json(), dtype="float32").tolist()

# Instantiate the embedding class
embeddings = HFInferenceEmbeddings()

# Test the embedding with a sample text
test_text = "I det här kapitlet kommer vi att studera polynom av olika gradtal och vilka räkneregler som gäller när vi multiplicerar polynom. Vi lär oss de två kvadreringsreglerna och konjugatregeln, som vi har användning för när vi vill faktorisera ett polynom."
embedding = embeddings.embed_query(test_text)
print("Embedding length:", len(embedding))
