import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
LLM_MODEL_NAME = "gemini-2.0-flash"

if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not set in environment variables.")

