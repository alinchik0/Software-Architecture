import os
import cv2
from PIL import Image
import matplotlib.pyplot as plt


def check_dependencies():
	try:
		from transformers import pipeline
		import torch
		return True
	except ImportError as e:
		print(f"❌ Ошибка импорта: {e}")
		return False


def simple_video_analysis():
	print("🎥 АНАЛИЗ ВИДЕО")
	print("=" * 50)

	if not check_dependencies():
		print("💡 Установи зависимости: pip install torch transformers")
		return

	print("⚠️  Скачиваю упрощенную модель... (~500МБ)")

	try:
		from transformers import pipeline

		classifier = pipeline(
			"image-classification",
			model="google/vit-base-patch16-224"
		)

		print("✅ Модель загружена!")
		print("💡 Эта версия анализирует отдельные кадры из видео")

	except Exception as e:
		print(f"❌ Ошибка загрузки модели: {e}")
		return


	video_path = input("Введи путь к видеофайлу: ").strip()

	if not os.path.exists(video_path):
		print("❌ Файл не найден!")
		return

	cap = cv2.VideoCapture(video_path)
	ret, frame = cap.read()

	if ret:
		frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		image = Image.fromarray(frame_rgb)

		print("🔍 Анализирую кадр из видео...")
		results = classifier(image)

		print("\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
		for i, result in enumerate(results[:3], 1):
			print(f"{i}. {result['label']}: {result['score']:.2f}")

	cap.release()


if __name__ == "__main__":
	simple_video_analysis()
