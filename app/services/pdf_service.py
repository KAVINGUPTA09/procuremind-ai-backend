from pathlib import Path
from uuid import uuid4

import fitz
#used to load pdf,open pdf,load pages,access specific pages,extract text from pdf pages
from fastapi import UploadFile


UPLOAD_DIR = Path("app/uploads")

ALLOWED_CONTENT_TYPES = {
    "application/pdf"
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_pdf(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            "Invalid file type. Only PDF files are allowed."
        )


def generate_safe_filename(
    original_filename: str
) -> str:
    original_path = Path(original_filename)

    file_extension = original_path.suffix.lower()

    unique_name = uuid4().hex

    return f"{unique_name}{file_extension}"


async def save_uploaded_file(
    file: UploadFile
) -> Path:
    validate_pdf(file)

    file_content = await file.read()

    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError(
            "File size exceeds the maximum limit of 10 MB."
        )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_filename = generate_safe_filename(
        file.filename or "uploaded_file.pdf"
    )

    file_path = UPLOAD_DIR / safe_filename

    file_path.write_bytes(
        file_content
    )

    await file.seek(0)

    return file_path


def extract_text_from_pdf(
    file_path: Path
) -> str:
    extracted_pages = []

    with fitz.open(file_path) as pdf_document:

        for page_number in range(
            pdf_document.page_count
        ):
            page = pdf_document.load_page(
                page_number
            )

            page_text = page.get_text(
                "text"
            )

            extracted_pages.append(
                page_text.strip()
            )

    extracted_text = "\n\n".join(
        page
        for page in extracted_pages
        if page
    )

    if not extracted_text.strip():
        raise ValueError(
            "No readable text was found in the PDF."
        )

    return extracted_text





# =========================================================================
# pdf_service.py Summary
# =========================================================================

# 1. Validates that the uploaded file is a PDF.

# 2. Restricts the maximum file size to 10 MB.

# 3. Generates a unique filename using UUID
#    to prevent file-name conflicts.

# 4. Saves the uploaded PDF inside app/uploads.

# 5. Resets the uploaded file pointer after reading.

# 6. Opens the saved PDF using PyMuPDF.

# 7. Extracts text from every PDF page.

# 8. Combines all page text into one string.

# 9. Raises an error if the PDF contains no readable text.

# =========================================================================