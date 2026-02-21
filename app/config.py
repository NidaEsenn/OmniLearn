import os
from dotenv import load_dotenv

load_dotenv()

# Try Streamlit secrets first, then env var
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    try:
        import streamlit as st
        GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", None)
        if GOOGLE_API_KEY:
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    except Exception:
        pass

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
LLM_MODEL_NAME = "gemini-2.0-flash"

if not GOOGLE_API_KEY:
    print("Warning: GOOGLE_API_KEY not set.")

