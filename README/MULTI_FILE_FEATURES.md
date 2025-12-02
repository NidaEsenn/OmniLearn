# Multi-File Support Features

## Overview
The Lecture Assistant now supports uploading and querying multiple PDF files simultaneously, with intelligent OCR-based pseudocode extraction.

## Key Features

### 1. Multi-PDF Upload
- **Limit**: Up to 4 PDFs
- **Page Limit**: 400 pages total across all PDFs
- **Format**: PDF files only
- **Processing**: Each PDF is:
  - Text extracted using PyMuPDF
  - Images extracted and OCR'd using Tesseract
  - Chunked with overlap for better context
  - Embedded using BGE-small-en-v1.5
  - Stored in ChromaDB with metadata

### 2. OCR Integration
- **Purpose**: Extract pseudocode and algorithms from embedded images
- **Technology**: Tesseract OCR + pdf2image
- **Detection**: Automatically identifies code patterns:
  - Keywords: `for`, `while`, `if`, `procedure`, `function`, `algorithm`
  - Operators: `←`, `:=`, `==`, `!=`
  - Array notation and indices
- **Formatting**: Detected code is wrapped in ` ```pseudo ` fences for LLM

### 3. Cross-PDF Querying
- **Default Behavior**: Searches across ALL uploaded PDFs
- **Selective Search**: Choose specific PDFs to query
- **Source Attribution**: Each answer shows:
  - Which PDF the information came from
  - Page numbers
  - Chunk IDs

### 4. File Management
- **List PDFs**: View all uploaded files with metadata
- **Delete Individual**: Remove specific PDFs
- **Delete All**: Clear entire database
- **Persistent Storage**: ChromaDB persists across restarts

## API Endpoints

### Upload PDF
```http
POST /upload
Content-Type: multipart/form-data

Response:
{
  "pdf_id": "uuid",
  "filename": "lecture.pdf",
  "page_count": 85,
  "chunk_count": 120,
  "total_pdfs": 2,
  "total_pages": 150
}
```

### List PDFs
```http
GET /pdfs

Response:
[
  {
    "pdf_id": "uuid",
    "filename": "lecture.pdf",
    "title": "Algorithms",
    "page_count": 85,
    "chunk_count": 120
  }
]
```

### Delete PDF
```http
DELETE /pdfs/{pdf_id}

Response:
{
  "message": "PDF deleted successfully",
  "pdf_id": "uuid",
  "remaining_pdfs": 1
}
```

### Chat (Multi-PDF)
```http
POST /chat
Content-Type: application/json

{
  "question": "Explain bubble sort",
  "pdf_ids": ["uuid1", "uuid2"]  // Optional, omit to search all
}

Response:
{
  "answer": "Bubble sort is...",
  "source_documents": [
    {
      "content": "...",
      "metadata": {
        "pdf_id": "uuid1",
        "filename": "lecture.pdf",
        "page_numbers": "6",
        "chunk_id": "chunk_12",
        "contains_code": "True"
      }
    }
  ]
}
```

## Limits and Validation

### Hard Limits
- **MAX_PDFS**: 4 files
- **MAX_TOTAL_PAGES**: 400 pages
- Enforced at upload time
- Returns HTTP 400 if limits exceeded

### Soft Limits
- **Chunk Size**: ~1000 characters
- **Chunk Overlap**: 200 characters
- **Retrieval K**: 5 chunks per query
- **Embedding Dimension**: 384 (BGE-small)

## Technical Details

### Vector Store Filtering
- Uses ChromaDB's `$in` operator for multi-PDF filtering
- Metadata schema:
  ```python
  {
    "pdf_id": str,
    "filename": str,
    "title": str,
    "chunk_id": str,
    "page_numbers": str,
    "contains_code": bool,
    "contains_math": bool
  }
  ```

### OCR Pipeline
1. Extract images from PDF using PyMuPDF
2. Convert each image to PIL Image
3. Run Tesseract OCR with `--psm 6` (uniform text block)
4. Clean OCR artifacts (common mistakes like `|` → `I`)
5. Detect code patterns using regex
6. Tag chunks with `contains_code` metadata
7. Wrap in ` ```pseudo ` fences during retrieval

### Session Management
- Backend stores PDF metadata in-memory (`uploaded_pdfs` dict)
- Frontend fetches list on load and after each operation
- Chat history persists in Streamlit session state
- Vector store persists to disk (ChromaDB)

## Usage Examples

### Example 1: Upload Multiple Lectures
```python
# Upload lecture 1
files = {"file": open("lecture1.pdf", "rb")}
response = requests.post("http://localhost:8001/upload", files=files)
pdf1_id = response.json()["pdf_id"]

# Upload lecture 2
files = {"file": open("lecture2.pdf", "rb")}
response = requests.post("http://localhost:8001/upload", files=files)
pdf2_id = response.json()["pdf_id"]
```

### Example 2: Query Specific PDFs
```python
# Ask about content in lecture 1 only
payload = {
    "question": "What is the time complexity of merge sort?",
    "pdf_ids": [pdf1_id]
}
response = requests.post("http://localhost:8001/chat", json=payload)
```

### Example 3: Query All PDFs
```python
# Search across all uploaded PDFs
payload = {
    "question": "Compare bubble sort and merge sort",
    "pdf_ids": None  # or omit this field
}
response = requests.post("http://localhost:8001/chat", json=payload)
```

## Troubleshooting

### OCR Not Working
- Ensure Tesseract is installed: `tesseract --version`
- Ensure Poppler is installed: `pdfinfo --version`
- Check Python packages: `pip list | grep -E "pytesseract|pdf2image"`

### Upload Fails with "Limit Exceeded"
- Check current usage: `GET /pdfs`
- Delete unused PDFs: `DELETE /pdfs/{pdf_id}`
- Or clear all: `DELETE /pdfs`

### Chat Returns "No PDFs uploaded"
- Verify PDFs are uploaded: `GET /pdfs`
- Check backend logs for ingestion errors
- Ensure ChromaDB directory exists and is writable

### Poor Code Extraction
- Check if pseudocode is in an image (use `debug_extraction.py`)
- Verify OCR is enabled in `extract_text_from_pdf(use_ocr=True)`
- Adjust code detection patterns in `app/pdf_ingestion/ocr.py`

## Performance Considerations

### Upload Time
- ~2-5 seconds per 100 pages (depends on OCR complexity)
- OCR adds ~1-2 seconds per image
- Embedding generation is the main bottleneck

### Query Time
- ~2-4 seconds end-to-end
- Retrieval: <500ms
- LLM generation: 1-3 seconds
- Scales well with multiple PDFs (same retrieval time)

### Storage
- ChromaDB: ~5-10 MB per 100 pages
- In-memory metadata: negligible (<1 MB for 4 PDFs)
- No file storage (PDFs not saved, only processed)

## Future Enhancements

Potential improvements:
- [ ] Persistent PDF metadata (database instead of in-memory)
- [ ] PDF preview/viewer in UI
- [ ] Advanced filtering (by topic, date, etc.)
- [ ] Batch upload (multiple files at once)
- [ ] Export chat history
- [ ] Improved OCR accuracy (preprocessing, multiple passes)
- [ ] Support for other document formats (DOCX, PPTX)

