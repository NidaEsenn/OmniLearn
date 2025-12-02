# Lecture Assistant: AI-Powered Study Companion

## Overview
A low-cost AI system that turns static lecture PDFs into interactive learning tools with:
1. RAG-based **Q&A chat over lecture PDFs**
2. Personalized **study plan generation**
3. **Multi-file support** with OCR for pseudocode extraction

## Features
- **Multi-PDF Support**: Upload up to 4 PDFs (400 pages total) and query across all of them
- **PDF Ingestion**: Extracts text and creates embeddings using BGE-small-en
- **OCR Integration**: Extracts pseudocode and algorithms from embedded images using Tesseract
- **RAG Q&A**: Uses Gemini 2.0 Flash to answer questions with natural, teacher-like explanations
- **Dynamic Retrieval**: Automatically adjusts retrieval based on question type (comprehensive, comparison, simple)
- **File Management**: Add, delete, and manage multiple lecture PDFs
- **Study Planner**: Generates personalized study schedules with weak topic prioritization
- **Practice Questions**: Generate multiple-choice or open-ended questions for self-assessment
- **Evaluation**: Automated and manual scoring with predefined rubric

## Setup

### Prerequisites
- Python 3.9+
- Gemini API Key (Get one from Google AI Studio)
- Tesseract OCR (for pseudocode extraction from images)
- Poppler (for PDF to image conversion)

### System Dependencies

**macOS:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment:
   ```bash
   # Create .env file
   cp .env.example .env
   # Open .env and paste your GOOGLE_API_KEY
   ```

### Running the Application

**Terminal 1 - Start the backend server:**
```bash
uvicorn app.main:app --reload --port 8001 --reload-dir app
```

**Terminal 2 - Start the Streamlit frontend:**
```bash
streamlit run frontend/app.py
```

The Streamlit UI will open automatically in your browser (usually at `http://localhost:8501`).

### Using the Application

1. **Upload PDFs**: 
   - Use the sidebar to upload up to 4 PDFs (max 400 pages total)
   - Each PDF is processed with OCR to extract pseudocode from images
   - View uploaded files and their metadata in the sidebar

2. **Chat with Your Lectures**:
   - Select specific PDFs to query, or search across all uploaded files
   - Ask questions about algorithms, concepts, formulas, etc.
   - View source citations showing which PDF and page the answer came from

3. **Generate Study Plans**:
   - Select a PDF to create a study plan for
   - Specify days, daily minutes, and your level
   - Add weak topics for prioritization
   - Get a structured day-by-day schedule with concrete tasks

4. **Practice with Generated Questions**:
   - Choose multiple-choice or open-ended questions
   - Generate 5-20 questions from your PDFs
   - Get immediate feedback on multiple-choice
   - Compare your answers with sample answers for open-ended
   - Shuffle to create new question sets

5. **Manage Files**:
   - Delete individual PDFs when no longer needed
   - Clear all PDFs to start fresh

### Evaluation

The system includes a comprehensive evaluation framework with a pre-defined rubric.

**Quick Start:**
```bash
# 1. Generate answers
python app/evaluation/run_eval.py

# 2. Auto-score (recommended) or manual scoring
python app/evaluation/auto_score.py eval_results_YYYYMMDD_HHMMSS.csv

# 3. Analyze results
python app/evaluation/run_eval.py --analyze eval_results_YYYYMMDD_HHMMSS_auto_scored.csv
```

**Evaluation Framework:**
- **Rubric:** 4 dimensions (Relevance, Correctness, Citations, Detail) - 0-2 points each
- **Dataset:** 15 questions across 5 categories
- **Goal:** ≥85% of answers score ≥6/8 points
- **Process:** Pre-defined criteria → Generate → Score → Analyze

**Scoring Options:**
- **Automated**: Uses Gemini as LLM judge (~30 seconds for 15 questions)
- **Manual**: Score each answer by hand using the rubric

**Files:**
- `app/evaluation/rubric.md` - Scoring criteria
- `app/evaluation/eval_dataset.json` - Test questions
- `app/evaluation/run_eval.py` - Generate answers & analyze
- `app/evaluation/auto_score.py` - Automated scoring
- `app/evaluation/EVALUATION_GUIDE.md` - Complete guide
- `app/evaluation/AUTO_SCORING_GUIDE.md` - Auto-scoring guide

For detailed instructions, see `app/evaluation/README.md`

## Project Structure
- `app/`: Backend code (FastAPI, RAG logic, Study Planner).
- `frontend/`: Static HTML/JS frontend.
- `app/evaluation/`: Rubric and evaluation scripts.
