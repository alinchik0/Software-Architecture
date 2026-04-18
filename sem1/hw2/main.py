from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import pipeline
from PIL import Image
import io

app = FastAPI()

detector = pipeline("object-detection", model="facebook/detr-resnet-50")


@app.get("/")
def home():
	return {"message": "Object Detection FastAPI работает!"}


@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
	if not file:
		raise HTTPException(status_code=400, detail="Файл не загружен")

	try:
		contents = await file.read()
		image = Image.open(io.BytesIO(contents)).convert("RGB")
		results = detector(image)
		return JSONResponse(content={"objects": results})
	except Exception as e:
		return JSONResponse(status_code=500, content={"error": str(e)})