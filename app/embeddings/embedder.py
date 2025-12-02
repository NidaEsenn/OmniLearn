from langchain_huggingface import HuggingFaceEmbeddings
from app.config import EMBEDDING_MODEL_NAME

def get_embedding_function():
    """
    Returns the embedding function using BGE-small-en-v1.5.
    """
    encode_kwargs = {'normalize_embeddings': True} # Recommended for BGE
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        encode_kwargs=encode_kwargs
    )

