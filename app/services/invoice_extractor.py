
import os
import json
import requests

from dotenv import load_dotenv
from app.schemas.invoice import InvoiceExtractionResponse

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def format_ocr_data(ocr_result: dict) -> str:
    """Prepare OCR text with coordinates and confidence scores."""

    formatted_lines = []

    for page in ocr_result.get("pages", []):
        page_number = page.get("page")

        for line in page.get("lines", []):
            text = line.get("text", "")
            confidence = line.get("confidence")
            bounding_box = line.get("bounding_box")

            formatted_lines.append(
                f"Page: {page_number} | "
                f"Text: {text} | "
                f"Bounding box: {bounding_box} | "
                f"Confidence: {confidence}"
            )

    return "\n".join(formatted_lines)


def extract_invoice_data(ocr_result: dict) -> InvoiceExtractionResponse:

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is missing.")

    if not OPENROUTER_MODEL:
        raise ValueError("OPENROUTER_MODEL is missing.")

    ocr_data = format_ocr_data(ocr_result)

    prompt = f"""
You are an expert financial document data extraction assistant.

Extract all invoice and ledger records from the OCR data.

The OCR data contains:
- Text
- Bounding box coordinates [x_min, y_min, x_max, y_max]
- Confidence scores

Use the bounding boxes to understand which values belong
to the same table row and column.

Return ONLY valid JSON.

The response must follow this structure:

{{
    "records": [
        {{
            "entry_type": "AP",
            "reference": "CL-001",
            "amount_cents": -500000,
            "currency": "LKR",
            "invoice_date": "2026-10-08",
            "due_date": null,
            "counterparty": "Amazon Web services",
            "is_open": true
        }}
    ]
}}

Rules:
1. Extract every record.
2. Preserve the original reference values.
3. amount_cents must be an integer.
4. Preserve positive and negative amounts.
5. Dates must use YYYY-MM-DD format.
6. Use null for missing values.
7. Do not invent information.
8. is_open must be a boolean.
9. Do not include column headers as records.
10. Return an empty records list if no records are found.
11. Use bounding boxes to identify table columns and rows.
12. If amount and currency appear together in one OCR result,
    separate them into amount_cents and currency.
13. Use confidence scores to identify potentially uncertain OCR values.
    Do not silently invent corrections.

OCR DATA:
{ocr_data}
"""

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
        },
        timeout=120,
    )

    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    #print("OPENROUTER RESPONSE:")
    #print(content)

    extracted_data = json.loads(content)

    return InvoiceExtractionResponse.model_validate(extracted_data)
