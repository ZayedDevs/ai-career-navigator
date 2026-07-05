import os
import re
import fitz                    # PyMuPDF — for PDF parsing
from docx import Document      # python-docx — for DOCX parsing

"""
Purpose:
    Extract clean, normalized text from user-uploaded resumes.
    Supports PDF and DOCX formats.
"""


# ============================================================================
# CONFIGURATION
# ============================================================================

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10  # Reject files larger than 10 MB


# ============================================================================
# TEXT CLEANING UTILITIES
# ============================================================================

def clean_resume_text(text: str) -> str:
    """
    Normalize extracted resume text for downstream NLP processing.

    Cleaning steps:
      1. Remove URLs (https://..., http://...)
      2. Remove email addresses
      3. Remove phone numbers (various formats)
      4. Replace multiple newlines with single newlines
      5. Replace multiple spaces with single space
      6. Strip leading/trailing whitespace
      7. Remove non-printable characters
    """
    if not text:
        return ""

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b", " ", text)

    # Remove phone numbers (international, US, simple formats)
    text = re.sub(r"\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}", " ", text)

    # Remove non-printable / control characters (except newline & tab)
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)

    # Collapse multiple newlines (keep paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces and tabs (but preserve newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Strip whitespace from each line
    text = "\n".join(line.strip() for line in text.split("\n"))

    # Remove empty lines at start/end
    text = text.strip()

    return text


# ============================================================================
# PDF PARSER (PyMuPDF / fitz)
# ============================================================================

def extract_pdf_text(file_path: str) -> tuple[str, dict]:
    """
    Extract text from a PDF using PyMuPDF.

    Returns:
        (extracted_text, metadata)
    """
    doc = fitz.open(file_path)
    pages_text = []

    for page_num, page in enumerate(doc):
        # "text" mode preserves logical reading order
        page_text = page.get_text("text")
        pages_text.append(page_text)

    metadata = {
        "file_type": "pdf",
        "pages": len(doc),
        "title": doc.metadata.get("title", "") if doc.metadata else "",
        "author": doc.metadata.get("author", "") if doc.metadata else "",
    }

    doc.close()
    full_text = "\n".join(pages_text)
    return full_text, metadata


# ============================================================================
# DOCX PARSER (python-docx)
# ============================================================================

def extract_docx_text(file_path: str) -> tuple[str, dict]:
    """
    Extract text from a DOCX using python-docx.

    Reads:
      - Body paragraphs
      - Table cells (often contain skills in resume templates)

    Returns:
        (extracted_text, metadata)
    """
    doc = Document(file_path)

    # Paragraphs
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

    # Table cells (resumes often put skills in tables)
    table_text = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    table_text.append(cell_text)

    all_text = paragraphs + table_text
    full_text = "\n".join(all_text)

    metadata = {
        "file_type": "docx",
        "paragraphs": len(paragraphs),
        "tables": len(doc.tables),
    }

    return full_text, metadata


# ============================================================================
# PUBLIC API
# ============================================================================

def parse_resume(file_path: str) -> dict:
    """
    Main entry point — parse a resume file and return clean text.

    Args:
        file_path: Absolute path to the uploaded resume file.

    Returns:
        {
            "success": bool,
            "text":    str (clean text),
            "metadata": dict,
            "error":   str or None,
            "char_count": int,
            "word_count": int
        }
    """
    # ---- 1. Validate file exists ----
    if not os.path.exists(file_path):
        return {
            "success": False,
            "text": "",
            "metadata": {},
            "error": f"File not found: {file_path}",
        }

    # ---- 2. Validate file size ----
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "success": False,
            "text": "",
            "metadata": {},
            "error": f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.",
        }

    # ---- 3. Detect file type ----
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {
            "success": False,
            "text": "",
            "metadata": {},
            "error": f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
        }

    # ---- 4. Extract text using appropriate parser ----
    try:
        if ext == ".pdf":
            raw_text, metadata = extract_pdf_text(file_path)
        elif ext == ".docx":
            raw_text, metadata = extract_docx_text(file_path)
        else:
            # Should not reach here due to validation above
            return {
                "success": False,
                "text": "",
                "metadata": {},
                "error": f"No parser for {ext}",
            }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "metadata": {},
            "error": f"Failed to parse file: {str(e)}",
        }

    # ---- 5. Clean the text ----
    clean_text = clean_resume_text(raw_text)

    # ---- 6. Validate extraction wasn't empty ----
    if len(clean_text.strip()) < 50:
        return {
            "success": False,
            "text": clean_text,
            "metadata": metadata,
            "error": "Extracted text is too short. The file may be empty, "
                     "image-based (scanned), or corrupted.",
        }

    # ---- 7. Return success ----
    return {
        "success": True,
        "text": clean_text,
        "metadata": metadata,
        "error": None,
        "char_count": len(clean_text),
        "word_count": len(clean_text.split()),
    }


# ============================================================================
# STANDALONE TEST (for development)
# ============================================================================

if __name__ == "__main__":
    """
    Test runner: parse all resumes in a test folder and print results.

    Usage:
        python -m app.services.resume_parser <path_to_resume>
    """
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m app.services.resume_parser <path_to_resume>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = parse_resume(file_path)

    print("\n" + "=" * 78)
    print("  RESUME PARSER — TEST RESULT")
    print("=" * 78)

    if result["success"]:
        print(f"✓ Success!")
        print(f"  File:       {file_path}")
        print(f"  Metadata:   {json.dumps(result['metadata'], indent=2)}")
        print(f"  Chars:      {result['char_count']:,}")
        print(f"  Words:      {result['word_count']:,}")
        print(f"\n  First 500 characters of extracted text:")
        print("  " + "-" * 76)
        for line in result["text"][:500].split("\n"):
            print(f"  {line}")
        print("  " + "-" * 76)
    else:
        print(f"✗ Failed!")
        print(f"  Error: {result['error']}")