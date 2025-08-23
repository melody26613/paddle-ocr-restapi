from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime

from paddleocr import PaddleOCR

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from restapi.logger import build_logger

import os
import argparse
import shutil
import uuid
import traceback
import uvicorn

TEMP_IMAGE_FOLDER = "temp_image"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = build_logger("paddle_ocr_api", "paddle_ocr_api.log")


def init_ocr(
    lang: str,
    use_gpu: bool,
    det_model_dir: str | None = None,
    rec_model_dir: str | None = None,
) -> PaddleOCR:
    """
    lang options (examples):
      - 'en' (English), 'ch' (Simplified Chinese), 'chinese_cht' (Traditional Chinese),
        'japan' (Japanese), 'korean', 'fr', 'german', 'it', 'es', ...
    """
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang=lang,
        use_gpu=use_gpu,
        det_model_dir=det_model_dir,
        rec_model_dir=rec_model_dir,
        show_log=False,
    )
    return ocr


def ocr_image(
    image_path: str,
    cls: bool = True
) -> Dict[str, Any]:
    """
    Returns:
      {
        "text": "full concatenated text\n...",
        "items": [
            {"bbox": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], "text": "word/line", "score": 0.98},
            ...
        ]
      }
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(image_path)

    # PaddleOCR returns a list per image; we pass one image, so take [0]
    result = ocr_model.ocr(image_path, cls=cls)
    if not result:
        return {"text": "", "items": []}

    lines = result[0]
    items = []
    texts = []
    for line in lines:
        # line format: [bbox, (text, score)]
        bbox: List[List[float]] = line[0]
        text, score = line[1]
        items.append({"bbox": bbox, "text": text, "score": float(score)})
        texts.append(text)

    return format_ocr_items({"text": "\n".join(texts), "items": items})


def format_ocr_items(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform OCR output into desired format:
    [
      {
        "transcription": "detected text",
        "points": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
      },
      ...
    ]
    """
    formatted = []
    for item in result["items"]:
        formatted.append({
            "transcription": item["text"],
            "points": [[int(x), int(y)] for x, y in item["bbox"]]
        })
    return formatted


def gen_png_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return "{}_{}.png".format(timestamp, unique_id)


def save_upload_file(file: UploadFile) -> str:
    temp_filename = gen_png_filename()
    file_path = os.path.join(TEMP_IMAGE_FOLDER, temp_filename)
    logger.info("[save_upload_file] file_path=" + str(file_path))

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def remove_file(file_path: str):
    if len(file_path) > 0 and os.path.exists(file_path):
        os.remove(file_path)


@app.post("/ocr/dict")
async def ocr_image_dict(file: UploadFile = File(...)):
    image_path = ""

    try:
        image_path = save_upload_file(file=file)
        response = ocr_image(image_path=image_path)
        logger.info("[ocr_image_dict] response=" + str(response))

        remove_file(file_path=image_path)

        return JSONResponse(content=response)
    except Exception as e:
        logger.error("[ocr_image_dict] " + str(e))
        logger.error(
            "[ocr_image_dict] exception traceback: " + str(traceback.format_exc()))

        remove_file(file_path=image_path)

        raise HTTPException(
            status_code=500,
            detail="Internal error",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=20000)
    parser.add_argument("--lang", type=str, default="japan")
    parser.add_argument("--use_gpu", type=bool, default=True)
    args = parser.parse_args()

    logger.info("args=" + str(args))

    if not os.path.exists(TEMP_IMAGE_FOLDER):
        os.makedirs(TEMP_IMAGE_FOLDER)

    ocr_model = init_ocr(lang=args.lang, use_gpu=args.use_gpu)

    uvicorn.run(app, host=args.host, port=args.port)
