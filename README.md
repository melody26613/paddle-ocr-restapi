## PaddleOCR with RestAPI
Use FastAPI to allow sending requests to PaddleOCR service

### Build Docker Image
```bash
docker build -t paddle_ocr_restapi:latest -f Dockerfile .
```

### Run Docker Container from Docker Image
* modify host, port and source language in docker-compose.yaml
```bash
# default --host 0.0.0.0
# default --port 20000
# default --lang japan

docker compose up -d

# check log under log/ folder
```

* request
```bash
curl -X POST "http://localhost:20000/ocr/dict" \
-H "accept: application/json" \
-H "Content-Type: multipart/form-data" \
-F "file=@test.png"
```

* response
```json
[
	{
		"transcription": "text1",
		"points": [
			[],
			[],
			[],
			[]
		]
	}
]
```

## References
* [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
* [PaddleOCR-API](https://github.com/m986883511/PaddleOCR-API)