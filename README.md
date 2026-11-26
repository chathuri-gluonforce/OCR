# PaddleOCR Invoice Extraction API

A FastAPI service that extracts text from invoices and ledger documents with PaddleOCR, then uses an OpenRouter language model to convert the OCR output into structured records.

## Requirements

- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/)
- An OpenRouter API key and a model identifier

The model metadata and folder structure are under `paddle_models/official_models/`. PaddleOCR downloads the model weights (`*.pdiparams`) on first startup when they are not already cached. The cache root defaults to `<project-root>/paddle_models/`, so existing local weights are reused. Git ignores `*.pdiparams`; if model weights were committed previously, `.gitignore` alone does not remove them from Git history.

## Configuration

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=provider/model
```

Replace the example values with your OpenRouter credentials and model identifier. Keep `.env` private; it is excluded by `.gitignore`.

The OCR module sets `PADDLE_PDX_CACHE_HOME` to `<project-root>/paddle_models/` by default. To use a different cache locally, set `PADDLE_PDX_CACHE_HOME` in the shell before starting the service; the OCR module reads it before PaddleOCR is imported.

## Run locally

From the project root:

```bash
uv sync --frozen
uv run uvicorn app.main:app --host 127.0.0.1 --port 8080
```

For a custom local model cache:

```bash
PADDLE_PDX_CACHE_HOME=/absolute/path/to/model-cache uv run uvicorn app.main:app --host 127.0.0.1 --port 8080
```

The service runs OCR on the CPU. Visit `http://127.0.0.1:8080/docs` for the interactive API documentation, or check `http://127.0.0.1:8080/health`.

The first startup on a machine without cached weights requires internet access and may take longer while PaddleOCR downloads the detection and recognition models. Later startups reuse the cached weights.

## Run with Docker

Build and run the image from the project root:

```bash
docker build -t paddle-ocr-service .
docker run --rm --name paddle-ocr-service \
  --env-file .env \
  -p 8080:8080 \
  -v paddle-ocr-model-cache:/app/paddle_models \
  paddle-ocr-service
```

The `.env` file is not copied into the image; `--env-file` passes its settings to the container at runtime. The named volume preserves downloaded model weights between container runs.

## API

### `POST /ocr/extract`

Upload a PDF or image as multipart form data, using the field name `file`.

Supported extensions: `.pdf`, `.png`, `.jpg`, and `.jpeg`. Maximum upload size: 20 MiB.

Example:

```bash
curl -X POST \
  -F "file=@/path/to/invoice.pdf" \
  http://127.0.0.1:8080/ocr/extract
```

Successful responses contain the original filename, a status, and extracted records:

```json
{
  "filename": "invoice.pdf",
  "status": "success",
  "records": [
    {
      "entry_type": "AP",
      "reference": "INV-001",
      "amount_cents": 125000,
      "currency": "USD",
      "invoice_date": "2026-01-15",
      "due_date": null,
      "counterparty": "Example Supplier",
      "is_open": true
    }
  ]
}
```

`entry_type` is `AP`, `AR`, or `GL`. Dates use `YYYY-MM-DD`; fields that cannot be extracted may be `null`.
