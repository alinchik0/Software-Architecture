import os
import io
from flask import Flask, request, jsonify
from transformers import pipeline
from PIL import Image

app = Flask(__name__)

# Загружаем DETR один раз при старте сервера
detector = pipeline(
    "object-detection",
    model="facebook/detr-resnet-50"
)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Object Detection Flask API работает!"})


@app.route("/detect", methods=["POST"])
def detect_objects():
    """
    Принимает изображение через multipart/form-data → возвращает список объектов.
    """
    if "file" not in request.files:
        return jsonify({"error": "Нет файла 'file' в запросе"}), 400

    file = request.files["file"]

    try:
        # Читаем изображение
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Запускаем модель
        results = detector(image)

        return jsonify({"objects": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
