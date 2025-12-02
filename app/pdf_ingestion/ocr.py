"""
OCR functionality for extracting text from images embedded in PDFs.
"""
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from typing import List, Dict, Any
import re


def _is_likely_code_image(ocr_text: str) -> bool:
    """
    Heuristic to determine if OCR'd text looks like pseudocode/algorithm.
    """
    if not ocr_text.strip():
        return False
    
    # Code indicators
    code_patterns = [
        r'\bfor\b',
        r'\bwhile\b',
        r'\bif\b',
        r'\belse\b',
        r'\breturn\b',
        r'\bprocedure\b',
        r'\bfunction\b',
        r'\balgorithm\b',
        r'\bdo\b',
        r'\bend\b',
        r'\binput\b',
        r'\boutput\b',
        r'←|:=|==|!=',  # assignment/comparison operators
        r'\[\s*\d+\s*\.\.\s*\d+\s*\]',  # array indices
    ]
    
    text_lower = ocr_text.lower()
    matches = sum(1 for pattern in code_patterns if re.search(pattern, text_lower))
    
    # If we have 3+ code indicators, it's likely pseudocode
    return matches >= 3


def _clean_ocr_text(text: str) -> str:
    """
    Clean up OCR artifacts and normalize whitespace.
    """
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Fix common OCR errors
    text = text.replace('|', 'I')  # Common OCR mistake
    text = text.replace('0', 'O')  # In variable names
    return text.strip()


def extract_images_with_ocr(pdf_bytes: bytes, page_num: int = None) -> List[Dict[str, Any]]:
    """
    Extract images from PDF and run OCR on them.
    
    Args:
        pdf_bytes: PDF file content as bytes
        page_num: Optional specific page number (0-indexed). If None, process all pages.
    
    Returns:
        List of dicts with keys: 'text', 'page_number', 'is_code', 'bbox'
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    ocr_results = []
    
    pages_to_process = [page_num] if page_num is not None else range(len(doc))
    
    for pg_idx in pages_to_process:
        if pg_idx >= len(doc):
            continue
            
        page = doc[pg_idx]
        image_list = page.get_images(full=True)
        
        for img_index, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Convert to PIL Image
                pil_image = Image.open(io.BytesIO(image_bytes))
                
                # Run OCR
                ocr_text = pytesseract.image_to_string(pil_image, config='--psm 6')
                
                if not ocr_text.strip():
                    continue
                
                cleaned_text = _clean_ocr_text(ocr_text)
                is_code = _is_likely_code_image(cleaned_text)
                
                # Get image position on page
                img_rects = page.get_image_rects(xref)
                bbox = img_rects[0] if img_rects else None
                
                ocr_results.append({
                    'text': cleaned_text,
                    'page_number': pg_idx + 1,
                    'is_code': is_code,
                    'bbox': bbox,
                    'image_index': img_index,
                })
                
            except Exception as e:
                # Skip images that can't be processed
                print(f"Warning: Could not OCR image {img_index} on page {pg_idx + 1}: {e}")
                continue
    
    doc.close()
    return ocr_results


def extract_images_from_page(pdf_bytes: bytes, page_num: int) -> List[Dict[str, Any]]:
    """
    Convenience function to extract images from a specific page.
    
    Args:
        pdf_bytes: PDF file content
        page_num: Page number (1-indexed)
    
    Returns:
        List of OCR results for that page
    """
    return extract_images_with_ocr(pdf_bytes, page_num - 1)

