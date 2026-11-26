
from pathlib import Path

from paddleocr import PaddleOCR


MODEL_ROOT = (
    Path(__file__).resolve().parents[2]
    / "paddle_models"
    / "official_models"
)

ocr = PaddleOCR(
    lang="en",
    device="cpu",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_detection_model_dir=str(MODEL_ROOT / "PP-OCRv6_medium_det"),
    text_recognition_model_dir=str(MODEL_ROOT / "PP-OCRv6_medium_rec"),
)

def extract_text(file_path: str):
    results = ocr.predict(input=file_path)

    pages = []
    all_text = []

    for page_number, result in enumerate(results, start=1):
        data = result.json

        if isinstance(data, str):
            import json
            data = json.loads(data)

        page_data = data.get("res", data)
        #print("Available fields:", page_data.keys())
        #print("Sample texts:", page_data.get("rec_texts", [])[:5])
        #print("Sample scores:", page_data.get("rec_scores", [])[:5])
        # print("Sample boxes:", page_data.get("rec_boxes", [])[:5])

        
        texts = page_data.get("rec_texts", [])
        scores = page_data.get("rec_scores", [])
        boxes = page_data.get("rec_boxes", [])

        lines = []

        for index, text in enumerate(texts):
            confidence = (
                float(scores[index])
                if index < len(scores)
                else None
            )

            bounding_box = (
                boxes[index].tolist()
                if hasattr(boxes[index], "tolist")
                else list(boxes[index])
            ) if index < len(boxes) else None

            lines.append({
                "text": text,
                "confidence": confidence,
                "bounding_box": bounding_box,
            })

        all_text.extend(texts)

        pages.append({
            "page": page_number,
            "lines": lines,
        })


    return {
        "total_pages": len(pages),
        "full_text": "\n".join(all_text),
        "pages": pages,
    }
