from langchain_chroma import Chroma
from app.config import CHROMA_DB_DIR
from app.embeddings.embedder import get_embedding_function
from typing import List, Dict, Any
from langchain_core.documents import Document

class VectorStore:
    def __init__(self):
        self.embedding_function = get_embedding_function()
        self.persist_directory = CHROMA_DB_DIR
        
        # Initialize Chroma
        # We use LangChain's Chroma wrapper for easy integration with retrievers
        self.vector_db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
            collection_name="lecture_pdfs"
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], metadata: Dict[str, Any]):
        """
        Adds chunks to the vector store.
        
        Args:
            chunks: List of dictionaries with 'text', 'id', 'page_numbers'.
            metadata: Global metadata for the PDF (e.g., pdf_id, title).
        """
        documents = []
        for chunk in chunks:
            # Combine chunk-specific metadata with global metadata
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_id": chunk["id"],
                "page_numbers": str(chunk["page_numbers"]),
                "contains_code": str(chunk.get("contains_code", False)),
                "contains_math": str(chunk.get("contains_math", False)),
            })
            
            doc = Document(
                page_content=chunk["text"],
                metadata=chunk_metadata
            )
            documents.append(doc)
            
        if documents:
            self.vector_db.add_documents(documents)
            # self.vector_db.persist() # Chroma 0.4+ persists automatically or via settings

    def as_retriever(self, search_kwargs: Dict[str, Any] = None):
        """
        Returns a retriever object.
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        return self.vector_db.as_retriever(search_kwargs=search_kwargs)
    
    def similarity_search(self, query: str, k: int = 5, filter: Dict[str, Any] = None):
        """
        Performs a similarity search.
        """
        return self.vector_db.similarity_search(query, k=k, filter=filter)
    
    def delete_by_pdf_id(self, pdf_id: str):
        """
        Delete all chunks associated with a specific PDF.
        """
        try:
            # Get all documents with this pdf_id
            results = self.vector_db.get(where={"pdf_id": pdf_id})
            if results and results.get('ids'):
                self.vector_db.delete(ids=results['ids'])
        except Exception as e:
            print(f"Error deleting PDF {pdf_id}: {e}")
            raise
    
    def clear_all(self):
        """
        Clear all documents from the vector store.
        """
        try:
            # Delete the collection and recreate it
            self.vector_db.delete_collection()
            self.vector_db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function,
                collection_name="lecture_pdfs"
            )
        except Exception as e:
            print(f"Error clearing vector store: {e}")
            raise

# Global instance
vector_store = VectorStore()

