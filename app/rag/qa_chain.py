import os
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import]
from langchain_core.output_parsers import StrOutputParser  # type: ignore[import]
from langchain_core.runnables import RunnablePassthrough  # type: ignore[import]
from app.config import LLM_MODEL_NAME, GOOGLE_API_KEY
from app.embeddings.vector_store import vector_store
from app.rag.prompts import QA_PROMPT

def format_docs(docs):
    """
    Format retrieved documents for the prompt.
    Includes metadata for citations.
    """
    formatted_docs = []
    for doc in docs:
        content = doc.page_content
        page_nums = doc.metadata.get("page_numbers", "Unknown")
        chunk_id = doc.metadata.get("chunk_id", "Unknown")
        contains_code = str(doc.metadata.get("contains_code", "False")).lower() == "true"
        contains_math = str(doc.metadata.get("contains_math", "False")).lower() == "true"

        stripped = content.strip()
        if contains_code and not stripped.startswith("```"):
            content = f"```pseudo\n{stripped}\n```"
        elif contains_math and "$$" not in stripped:
            content = f"$$\n{stripped}\n$$"
        else:
            content = stripped

        tag_list = []
        if contains_code:
            tag_list.append("code")
        if contains_math:
            tag_list.append("math")
        tag_str = f" | Tags: {', '.join(tag_list)}" if tag_list else ""

        formatted_docs.append(f"Content:\n{content}\n\nSource: [Page {page_nums}] (Chunk {chunk_id}){tag_str}")

    return "\n\n---\n\n".join(formatted_docs)

class QAChain:
    def __init__(self):
        from app.config import GOOGLE_API_KEY as api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")

        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL_NAME,
            google_api_key=api_key,
            temperature=0.0,
            convert_system_message_to_human=True
        )
        
        self.retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    def _determine_k_value(self, question: str) -> int:
        """
        Dynamically determine how many chunks to retrieve based on question type.
        
        Args:
            question: The user's question
            
        Returns:
            Number of chunks to retrieve (k value)
        """
        question_lower = question.lower()
        
        # Comprehensive queries need more chunks
        comprehensive_keywords = [
            "all topics", "all the topics", "list topics", "list all",
            "what topics", "what are the topics", "table of contents",
            "overview", "summary of", "everything about",
            "all algorithms", "all sorting", "all methods",
            "entire", "complete list", "full list"
        ]
        
        if any(keyword in question_lower for keyword in comprehensive_keywords):
            return 20  # Retrieve many chunks for comprehensive questions
        
        # Comparison questions need more context
        comparison_keywords = [
            "compare", "difference between", "vs", "versus",
            "contrast", "similarities", "which is better"
        ]
        
        if any(keyword in question_lower for keyword in comparison_keywords):
            return 10  # More chunks for comparisons
        
        # Complex questions need more context
        complex_keywords = [
            "explain in detail", "walk me through", "step by step",
            "how does", "why does", "analyze"
        ]
        
        if any(keyword in question_lower for keyword in complex_keywords):
            return 8  # More chunks for detailed explanations
        
        # Default for simple questions
        return 5

    def get_answer(self, question: str, pdf_ids: List[str] = None) -> Dict[str, Any]:
        """
        Generates an answer for the given question.
        
        Args:
            question: User's question.
            pdf_ids: Optional list of PDF IDs to filter by. If None or empty, searches all PDFs.
            
        Returns:
            Dict containing 'answer', 'citations' (extracted from answer or separate), and 'source_documents'.
        """
        # Dynamically determine k based on question type
        k_value = self._determine_k_value(question)
        
        # Configure retriever with filter if pdf_ids is provided
        search_kwargs = {"k": k_value}
        if pdf_ids:
            # Filter by multiple PDF IDs using $in operator
            search_kwargs["filter"] = {"pdf_id": {"$in": pdf_ids}}
            
        retriever = vector_store.vector_db.as_retriever(search_kwargs=search_kwargs)
        
        # Build the chain
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | QA_PROMPT
            | self.llm
            | StrOutputParser()
        )
        
        # Retrieve docs separately to return them
        source_docs = retriever.invoke(question)
        formatted_context = format_docs(source_docs)
        
        # Invoke chain
        answer = rag_chain.invoke(question)
        
        return {
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                } for doc in source_docs
            ]
        }

qa_chain = QAChain()

