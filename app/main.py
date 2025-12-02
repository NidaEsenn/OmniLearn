import shutil
import uuid
import os
from typing import List, Optional, Dict
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pdf_ingestion.extract import extract_text_from_pdf
from app.pdf_ingestion.chunk import create_chunks_with_metadata
from app.embeddings.vector_store import vector_store
from app.rag.qa_chain import qa_chain
from app.study_plans.planner import study_planner
from app.practice.question_generator import question_generator

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Lecture Assistant AI", description="RAG Q&A + Study Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for uploaded PDFs metadata
# In production, use a database
uploaded_pdfs: Dict[str, dict] = {}

# Limits
MAX_PDFS = 4
MAX_TOTAL_PAGES = 400

@app.get("/")
async def root():
    return {"message": "Lecture Assistant API is running. Use the Streamlit frontend to interact."}

class ChatRequest(BaseModel):
    question: str
    pdf_ids: Optional[List[str]] = None  # Changed to support multiple PDFs

class ChatResponse(BaseModel):
    answer: str
    source_documents: List[dict]

class PDFInfo(BaseModel):
    pdf_id: str
    filename: str
    title: str
    page_count: int
    chunk_count: int

class StudyPlanRequest(BaseModel):
    pdf_id: str
    total_days: int
    daily_minutes: int
    level: str = "Intermediate"
    goal: str = "understand the material"
    weak_topics: str = ""
    deadline_context: str = "upcoming exam"

class PracticeQuestionRequest(BaseModel):
    question_type: str  # "multiple-choice" or "open-ended"
    num_questions: int = 10
    pdf_ids: Optional[List[str]] = None
    shuffle: bool = True
    focused_topics: Optional[List[str]] = None

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # Check PDF count limit
    if len(uploaded_pdfs) >= MAX_PDFS:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {MAX_PDFS} PDFs allowed. Please delete a file before uploading a new one."
        )
    
    try:
        # Read file content
        contents = await file.read()
        
        # Extract text
        extraction_result = extract_text_from_pdf(contents)
        page_count = extraction_result["metadata"]["page_count"]
        
        # Check total pages limit
        current_total_pages = sum(pdf["page_count"] for pdf in uploaded_pdfs.values())
        if current_total_pages + page_count > MAX_TOTAL_PAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Total page limit ({MAX_TOTAL_PAGES}) would be exceeded. "
                       f"Current: {current_total_pages} pages, Uploading: {page_count} pages."
            )
        
        # Generate a unique ID for this PDF
        pdf_id = str(uuid.uuid4())
        
        # Create chunks
        chunks = create_chunks_with_metadata(extraction_result["pages"])
        
        # Store in vector DB
        metadata = {
            "pdf_id": pdf_id,
            "filename": file.filename,
            "title": extraction_result["metadata"].get("title", file.filename)
        }
        
        vector_store.add_chunks(chunks, metadata)
        
        # Store PDF metadata in memory
        uploaded_pdfs[pdf_id] = {
            "pdf_id": pdf_id,
            "filename": file.filename,
            "title": extraction_result["metadata"].get("title", file.filename),
            "page_count": page_count,
            "chunk_count": len(chunks)
        }
        
        return {
            "message": "PDF processed successfully",
            "pdf_id": pdf_id,
            "filename": file.filename,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "total_pdfs": len(uploaded_pdfs),
            "total_pages": sum(pdf["page_count"] for pdf in uploaded_pdfs.values())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # If no pdf_ids specified, search across all uploaded PDFs
        pdf_ids = request.pdf_ids if request.pdf_ids else list(uploaded_pdfs.keys())
        
        if not pdf_ids:
            raise HTTPException(status_code=400, detail="No PDFs uploaded yet. Please upload a PDF first.")
        
        result = qa_chain.get_answer(request.question, pdf_ids)
        return ChatResponse(
            answer=result["answer"],
            source_documents=result["source_documents"]
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/pdfs", response_model=List[PDFInfo])
async def list_pdfs():
    """List all uploaded PDFs."""
    return list(uploaded_pdfs.values())

@app.delete("/pdfs/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """Delete a specific PDF and its chunks from the vector store."""
    if pdf_id not in uploaded_pdfs:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    try:
        # Delete from vector store
        vector_store.delete_by_pdf_id(pdf_id)
        
        # Remove from memory
        pdf_info = uploaded_pdfs.pop(pdf_id)
        
        return {
            "message": f"PDF '{pdf_info['filename']}' deleted successfully",
            "pdf_id": pdf_id,
            "remaining_pdfs": len(uploaded_pdfs)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting PDF: {str(e)}")

@app.delete("/pdfs")
async def delete_all_pdfs():
    """Delete all PDFs and clear the vector store."""
    try:
        # Clear vector store
        vector_store.clear_all()
        
        # Clear memory
        count = len(uploaded_pdfs)
        uploaded_pdfs.clear()
        
        return {
            "message": f"All {count} PDFs deleted successfully",
            "remaining_pdfs": 0
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error clearing PDFs: {str(e)}")

@app.post("/study-plan")
async def generate_study_plan(request: StudyPlanRequest):
    try:
        plan = study_planner.generate_plan(
            pdf_id=request.pdf_id,
            total_days=request.total_days,
            daily_minutes=request.daily_minutes,
            level=request.level,
            goal=request.goal,
            weak_topics=request.weak_topics,
            deadline_context=request.deadline_context
        )
        return {"plan": plan}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating study plan: {str(e)}")

@app.post("/practice/generate")
async def generate_practice_questions(request: PracticeQuestionRequest):
    """Generate practice questions based on uploaded PDFs."""
    try:
        # Validate question type
        if request.question_type not in ["multiple-choice", "open-ended"]:
            raise HTTPException(
                status_code=400,
                detail="question_type must be 'multiple-choice' or 'open-ended'"
            )
        
        # Validate number of questions
        if request.num_questions < 1 or request.num_questions > 20:
            raise HTTPException(
                status_code=400,
                detail="num_questions must be between 1 and 20"
            )
        
        # If no PDF IDs specified, use all uploaded PDFs
        pdf_ids = request.pdf_ids if request.pdf_ids else list(uploaded_pdfs.keys())
        
        if not pdf_ids:
            raise HTTPException(
                status_code=400,
                detail="No PDFs uploaded. Please upload at least one PDF first."
            )
        
        # Generate questions
        result = question_generator.generate_questions(
            question_type=request.question_type,
            num_questions=request.num_questions,
            pdf_ids=pdf_ids,
            shuffle=request.shuffle,
            focused_topics=request.focused_topics
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate questions: {result.get('error', 'Unknown error')}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
