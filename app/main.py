
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException

from app.services.ocr import extract_text
from app.services.invoice_extractor import extract_invoice_data

app = FastAPI(
    title="PaddleOCR API",
    description="Document text extraction using PaddleOCR",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "PaddleOCR API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ocr/extract")
async def extract_document(file: UploadFile = File(...)):

    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    extension = os.path.splitext(file.filename or "")[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 20 MB.",
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        # Step 1: Extract text and bounding boxes using PaddleOCR
        ocr_result = extract_text(temp_path)


        # Step 2: Convert OCR data into structured records using OpenRouter
        invoice_data = extract_invoice_data(ocr_result)

        return {
            "filename": file.filename,
            "status": "success",
            "records": invoice_data.model_dump(mode="json")["records"],

            
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(error)}",
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        await file.close()
