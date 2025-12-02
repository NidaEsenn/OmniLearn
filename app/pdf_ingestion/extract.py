import fitz  # PyMuPDF
from typing import List, Dict, Any
import re
from .ocr import extract_images_with_ocr

CODE_FONT_HINTS = ("mono", "code", "courier", "consolas", "menlo", "andale", "inconsolata")
MATH_SYMBOLS = set("±×÷∞√∑∏∫≈≠≤≥→←⇒⇔∂∇ΩΘλμσπθφψωβγδηκρτυζα≡⊆⊂⊇⊃⊕⊗∪∩∀∃∧∨¬⊢⊨⇐⇑⇓⇔≅∝∴∵")
MATH_PATTERNS = (
    r"\bT\s*\(n\)\s*=",
    r"\bO\([^)]+\)",
    r"\bsum_{",
    r"\\frac",
    r"\balgorithm\b",
)


def _collect_block_text(block: Dict[str, Any]) -> str:
    lines = []
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        span_text = "".join(span.get("text", "") for span in spans)
        lines.append(span_text)
    return "\n".join(lines).rstrip()


def _collect_block_fonts(block: Dict[str, Any]) -> List[str]:
    fonts = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            font_name = span.get("font", "")
            if font_name:
                fonts.append(font_name.lower())
    return fonts


def _looks_like_code(block_text: str, block_fonts: List[str]) -> bool:
    if not block_text.strip():
        return False

    # Font-based detection
    if any(any(hint in font for hint in CODE_FONT_HINTS) for font in block_fonts):
        return True

    # Pattern-based detection for algorithm traces/examples
    # Look for array notation, comparisons, swap operations
    code_patterns = [
        r"a=\[.*?\]",  # array notation like a=[4,2,3,1]
        r"\w+\s*=\s*\[.*?\]",  # variable = [...]
        r"\d+\s*[<>]=?\s*\d+\s+so\s+we",  # "4>2 so we swap"
        r"swap|compare",  # swap/compare operations
        r"(for|while|if|else|return|procedure|function|algorithm)\s+",  # keywords
        r"^\s+(for|while|if|return)",  # indented keywords
    ]
    
    text_lower = block_text.lower()
    pattern_matches = sum(1 for pattern in code_patterns if re.search(pattern, text_lower))
    if pattern_matches >= 2:
        return True

    # Indentation-based detection
    lines = block_text.splitlines()
    if not lines:
        return False
    indented = [line for line in lines if line.startswith(("    ", "\t"))]
    if len(indented) / len(lines) >= 0.4:
        return True

    # Keyword density
    keywords = ("procedure", "function", "for", "while", "if", "return", "repeat", "until", "end", "input", "output", "loop", "array")
    keyword_hits = sum(1 for kw in keywords if kw in text_lower)
    return keyword_hits >= 3


def _looks_like_math(block_text: str) -> bool:
    if not block_text.strip():
        return False
    if any(char in MATH_SYMBOLS for char in block_text):
        return True
    
    # Enhanced math detection patterns
    math_indicators = [
        r"O\([^)]+\)",  # Big-O notation
        r"Θ\([^)]+\)",  # Theta notation
        r"Ω\([^)]+\)",  # Omega notation
        r"T\s*\(\s*n\s*\)",  # Time complexity function
        r"\bn\s*\^\s*\d+",  # n^2, n^3, etc.
        r"log\s*n",  # logarithmic
        r"complexity|theorem|lemma|proof",  # mathematical context
    ]
    
    for pattern in math_indicators:
        if re.search(pattern, block_text, flags=re.IGNORECASE):
            return True
    
    return any(re.search(pattern, block_text, flags=re.IGNORECASE) for pattern in MATH_PATTERNS)


def _format_block_text(block_text: str, is_code: bool, is_math: bool) -> str:
    cleaned = block_text.strip("\n")
    if not cleaned:
        return ""
    if is_code:
        return f"```pseudo\n{cleaned}\n```"
    if is_math:
        return f"$$\n{cleaned}\n$$"
    return cleaned


def extract_text_from_pdf(pdf_bytes: bytes, use_ocr: bool = True) -> Dict[str, Any]:
    """
    Extracts text (with best-effort preservation of pseudo-code and math blocks)
    and metadata from a PDF file. Optionally uses OCR to extract text from images.
    
    Args:
        pdf_bytes: PDF file content as bytes
        use_ocr: If True, also extract text from images using OCR (default: True)
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    full_text_parts: List[str] = []
    pages_content: List[Dict[str, Any]] = []
    
    # Extract OCR text from all images if enabled
    ocr_results_by_page = {}
    if use_ocr:
        try:
            ocr_results = extract_images_with_ocr(pdf_bytes)
            for ocr_item in ocr_results:
                page_num = ocr_item['page_number']
                if page_num not in ocr_results_by_page:
                    ocr_results_by_page[page_num] = []
                ocr_results_by_page[page_num].append(ocr_item)
        except Exception as e:
            print(f"Warning: OCR extraction failed: {e}")
            # Continue without OCR

    for page_num, page in enumerate(doc):
        page_blocks = page.get_text("dict")["blocks"]
        block_entries: List[Dict[str, Any]] = []

        # Process regular text blocks
        for block in page_blocks:
            if block.get("type") != 0:  # skip non-text blocks
                continue

            raw_text = _collect_block_text(block)
            if not raw_text.strip():
                continue

            fonts = _collect_block_fonts(block)
            is_code = _looks_like_code(raw_text, fonts)
            is_math = not is_code and _looks_like_math(raw_text)

            formatted = _format_block_text(raw_text, is_code, is_math)
            if formatted:
                block_entries.append(
                    {
                        "text": formatted,
                        "contains_code": is_code,
                        "contains_math": is_math,
                        "page_number": page_num + 1,
                    }
                )
        
        # Add OCR results for this page
        page_num_1indexed = page_num + 1
        if page_num_1indexed in ocr_results_by_page:
            for ocr_item in ocr_results_by_page[page_num_1indexed]:
                ocr_text = ocr_item['text']
                is_code = ocr_item['is_code']
                
                formatted = _format_block_text(ocr_text, is_code, False)
                if formatted:
                    block_entries.append(
                        {
                            "text": formatted,
                            "contains_code": is_code,
                            "contains_math": False,
                            "page_number": page_num_1indexed,
                            "source": "ocr",
                        }
                    )

        page_header = f"--- Page {page_num + 1} ---"
        page_text = page_header + "\n" + "\n\n".join([entry["text"] for entry in block_entries])

        pages_content.append(
            {
                "page_number": page_num + 1,
                "text": page_text,
                "blocks": block_entries,
            }
        )
        full_text_parts.append(page_text)

    metadata = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "page_count": doc.page_count,
    }

    return {
        "text": "\n\n".join(full_text_parts),
        "metadata": metadata,
        "pages": pages_content,
    }

