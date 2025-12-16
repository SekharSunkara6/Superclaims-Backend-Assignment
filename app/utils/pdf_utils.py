from io import BytesIO
from pypdf import PdfReader


async def pdf_to_text(content: bytes) -> str:
    """
    Convert a PDF (bytes) to plain text using pypdf.
    """
    try:
        buffer = BytesIO(content)
        reader = PdfReader(buffer)
        texts: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            texts.append(page_text)

        full_text = "\n".join(texts).strip()
        return full_text or "EMPTY_PDF_TEXT"
    except Exception as e:
        # In case of any parsing error, return a marker string.
        return f"PDF_PARSE_ERROR: {e}"
