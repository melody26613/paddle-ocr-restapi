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
import numpy as np

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


def ocr_image(image_path: str, cls: bool = True) -> Dict[str, Any]:
    """
    Returns:
      [
        {
          "transcription": "detected text",
          "points": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        },
        ...
      ]
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(image_path)

    results = ocr_model.predict(image_path)
    if not results:
        return [{"transcription": "", "points": []}]

    formatted = []

    for res in results:
        texts = res["rec_texts"]
        boxes = res["rec_polys"]

        for index, text in enumerate(texts):
            if index >= len(boxes):
                break

            points = (
                boxes[index].tolist()
                if isinstance(boxes[index], np.ndarray)
                else boxes[index]
            )

            formatted.append(
                {
                    "transcription": text,
                    "points": points,
                }
            )

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
            "[ocr_image_dict] exception traceback: " + str(traceback.format_exc())
        )

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
    parser.add_argument("--ocr_version", type=str, default="PP-OCRv5")
    parser.add_argument("--precision", type=str, default="fp16")
    parser.add_argument("--cpu_threads", type=int, default=4)
    parser.add_argument("--device", type=str, default="gpu:0")  # cpu
    parser.add_argument(
        "--text_detection_model_name", type=str, default="PP-OCRv5_mobile_det"
    )
    parser.add_argument(
        "--text_recognition_model_name", type=str, default="PP-OCRv5_mobile_rec"
    )
    parser.add_argument("--use_textline_orientation", action="store_true")
    parser.add_argument("--text_det_limit_side_len", type=int, default=960)
    parser.add_argument("--text_det_limit_type", type=str, default="max")

    args = parser.parse_args()

    logger.info("args=" + str(args))

    if not os.path.exists(TEMP_IMAGE_FOLDER):
        os.makedirs(TEMP_IMAGE_FOLDER)

    ocr_model = PaddleOCR(
        lang=args.lang,
        ocr_version=args.ocr_version,
        precision=args.precision,
        cpu_threads=args.cpu_threads,
        device=args.device,
        text_detection_model_name=args.text_detection_model_name,
        text_recognition_model_name=args.text_recognition_model_name,
        use_textline_orientation=args.use_textline_orientation,
        text_det_limit_side_len=args.text_det_limit_side_len,
        text_det_limit_type=args.text_det_limit_type,
        use_doc_unwarping=False,
    )

    uvicorn.run(app, host=args.host, port=args.port)

