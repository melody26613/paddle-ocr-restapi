FROM paddlecloud/paddleocr:2.6-gpu-cuda10.2-cudnn7-latest

COPY ./restapi /home/PaddleOCR/restapi

CMD [ \
    "python", "-m", "restapi.paddle_ocr_restapi", \
    "--host", "0.0.0.0", \
    "--port", "20000", \
    "--lang", "ch" \
]