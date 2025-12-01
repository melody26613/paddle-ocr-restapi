FROM paddlepaddle/paddle:3.2.2-gpu-cuda12.6-cudnn9.5

WORKDIR /home/PaddleOCR

RUN apt-get update
RUN apt-get install libgomp1 -y

RUN pip install --no-cache-dir paddleocr
RUN pip install --no-cache-dir opencv-python-headless
RUN pip install --no-cache-dir fastapi
RUN pip install --no-cache-dir uvicorn
RUN pip install --no-cache-dir python-multipart

COPY ./restapi /home/PaddleOCR/restapi

CMD [ \
    "python", "-m", "restapi.paddle_ocr_restapi", \
    "--host", "0.0.0.0", \
    "--port", "20000", \
    "--lang", "japan", \
    "--device", "gpu:0" \
]
