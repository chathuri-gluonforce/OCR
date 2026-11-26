import json
import os
import threading
from functools import lru_cache
from pathlib import Path

APP_ROOT = Path(os.getenv("APP_ROOT", Path(__file__).resolve().parents[2]))

# Must be set before paddleocr is imported.
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(APP_ROOT / "paddle_models"))

_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_ocr():
    from paddleocr import PaddleOCR  # imported lazily, after the env is set

    return PaddleOCR(
        device="cpu",
        enable_mkldnn=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        text_detection_model_name="PP-OCRv6_medium_det",
        text_recognition_model_name="PP-OCRv6_medium_rec",
    )


def _to_list(value):
    return value.tolist() if hasattr(value, "tolist") else list(value)


def extract_text(file_path: str) -> dict:
    with _lock:
        results = list(get_ocr().predict(input=file_path))

    pages, all_text = [], []
    for page_number, result in enumerate(results, start=1):
        data = result.json
        if isinstance(data, str):
            data = json.loads(data)
        page = data.get("res", data)

        texts = page.get("rec_texts", [])
        scores = page.get("rec_scores", [])
        boxes = page.get("rec_boxes", [])

        lines = [
            {
                "text": text,
                "confidence": float(scores[i]) if i < len(scores) else None,
                "bounding_box": _to_list(boxes[i]) if i < len(boxes) else None,
            }
            for i, text in enumerate(texts)
        ]
        all_text.extend(texts)
        pages.append({"page": page_number, "lines": lines})

    return {
        "total_pages": len(pages),
        "full_text": "\n".join(all_text),
        "pages": pages,
    }