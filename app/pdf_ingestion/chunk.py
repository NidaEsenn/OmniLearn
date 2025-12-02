from typing import List, Dict, Any


def create_chunks_with_metadata(
    pages: List[Dict[str, Any]],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> List[Dict[str, Any]]:
    """
    Creates structured chunks while preserving block boundaries so that
    pseudo-code and math blocks are not split across chunks.
    """

    chunks_with_meta: List[Dict[str, Any]] = []
    current_blocks: List[Dict[str, Any]] = []
    current_chars = 0
    current_contains_code = False
    current_contains_math = False
    chunk_index = 0

    def flush_chunk():
        nonlocal chunk_index, current_blocks, current_chars, current_contains_code, current_contains_math
        if not current_blocks:
            return

        chunk_text_value = "\n\n".join(block["text"] for block in current_blocks).strip()
        if not chunk_text_value:
            return

        chunk_pages = sorted({block["page_number"] for block in current_blocks if block.get("page_number")})
        chunks_with_meta.append(
            {
                "id": f"chunk_{chunk_index}",
                "text": chunk_text_value,
                "page_numbers": chunk_pages,
                "contains_code": current_contains_code,
                "contains_math": current_contains_math,
            }
        )
        chunk_index += 1

        if overlap > 0:
            overlap_chars = 0
            overlap_blocks: List[Dict[str, Any]] = []
            for block in reversed(current_blocks):
                overlap_blocks.insert(0, block)
                overlap_chars += len(block["text"])
                if overlap_chars >= overlap:
                    break
        else:
            overlap_blocks = []

        current_blocks = overlap_blocks.copy()
        current_chars = sum(len(block["text"]) for block in current_blocks)
        current_contains_code = any(block.get("contains_code") for block in current_blocks)
        current_contains_math = any(block.get("contains_math") for block in current_blocks)

    for page in pages:
        blocks = page.get("blocks")
        if not blocks:
            blocks = [
                {
                    "text": page.get("text", ""),
                    "contains_code": False,
                    "contains_math": False,
                    "page_number": page.get("page_number"),
                }
            ]

        for block in blocks:
            block_text = block.get("text", "")
            if not block_text.strip():
                continue

            block_len = len(block_text)

            if current_blocks and current_chars + block_len > chunk_size:
                flush_chunk()

            if not current_blocks and block_len > chunk_size:
                current_blocks.append(block)
                current_chars += block_len
                current_contains_code = block.get("contains_code", False)
                current_contains_math = block.get("contains_math", False)
                flush_chunk()
                continue

            current_blocks.append(block)
            current_chars += block_len
            if block.get("contains_code"):
                current_contains_code = True
            if block.get("contains_math"):
                current_contains_math = True

    flush_chunk()
    return chunks_with_meta

