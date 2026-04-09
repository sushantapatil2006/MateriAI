"""
PDF & TXT text extraction service.

Uses pdfplumber to extract text from PDF files page-by-page.
Handles TXT files via simple UTF-8 read.
"""
import logging
import pdfplumber

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file) -> str:
    """
    Extract all text from a PDF file object.

    Args:
        file: A Django UploadedFile (or any file-like object).

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If the PDF is empty or unreadable.
    """
    try:
        text_pages = []
        with pdfplumber.open(file) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
                else:
                    logger.debug("Page %d returned no text.", i + 1)

        full_text = "\n\n".join(text_pages)

        if not full_text.strip():
            raise ValueError(
                "The PDF file appears to be empty or contains only images/scans. "
                "No extractable text was found."
            )

        logger.info(
            "Extracted text from PDF: %d pages, %d characters.",
            len(text_pages),
            len(full_text),
        )
        return full_text

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as exc:
        raise ValueError(f"Invalid or corrupted PDF file: {exc}") from exc
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Failed to read PDF: {exc}") from exc


def extract_text_from_txt(file) -> str:
    """
    Extract text from a plain-text file object.

    Args:
        file: A Django UploadedFile (or any file-like object).

    Returns:
        File content as a string.

    Raises:
        ValueError: If the file is empty or unreadable.
    """
    try:
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        if not content.strip():
            raise ValueError("The text file is empty.")

        logger.info("Extracted text from TXT: %d characters.", len(content))
        return content

    except UnicodeDecodeError as exc:
        raise ValueError(f"Could not decode the text file: {exc}") from exc
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Failed to read text file: {exc}") from exc
