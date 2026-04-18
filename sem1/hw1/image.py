import os
import requests
from PIL import Image, ImageDraw, ImageFont
from transformers import pipeline
import matplotlib.pyplot as plt
import numpy as np


def download_sample_image():
	print("📥 Скачиваю тестовое изображение...")

	url = "https://images.unsplash.com/photo-1546961347-8d03ac563da5?w=500"

	try:
		response = requests.get(url, timeout=10)
		with open("sample_image.jpg", "wb") as f:
			f.write(response.content)
		return "sample_image.jpg"
	except:
		print("❌ Не удалось скачать тестовое изображение")
		return None


def show_image_with_boxes(image_path, results):
	image = Image.open(image_path)
	draw = ImageDraw.Draw(image)


	colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']

	print("\n📋 НАЙДЕННЫЕ ОБЪЕКТЫ:")
	print("=" * 40)


	for i, result in enumerate(results):
		if i >= 6:
			break

		box = result['box']
		label = result['label']
		score = result['score']


		color = colors[i % len(colors)]
		draw.rectangle(
			[box['xmin'], box['ymin'], box['xmax'], box['ymax']],
			outline=color,
			width=3
		)


		text = f"{label} ({score:.2f})"
		draw.text(
			(box['xmin'] + 5, box['ymin'] + 5),
			text,
			fill=color
		)


		print(f"🎯 {i + 1}. {label}:")
		print(f"    Уверенность: {score:.2f} ({score * 100:.1f}%)")
		print(f"    Координаты: x:{box['xmin']:.0f}-{box['xmax']:.0f}, y:{box['ymin']:.0f}-{box['ymax']:.0f}")


	output_path = "detection_result.jpg"
	image.save(output_path)


	plt.figure(figsize=(12, 8))
	plt.imshow(np.array(image))
	plt.axis('off')
	plt.title("Результат определения объектов")
	plt.tight_layout()
	plt.show()

	return output_path


def detect_objects():
	print("🖼  ОПРЕДЕЛЕНИЕ ОБЪЕКТОВ НА ФОТО")

	detector = pipeline(
		"object-detection",
		model="facebook/detr-resnet-50"
	)

	print("✅ Модель загружена!")
	print("\n💡 СОВЕТЫ:")
	print("- Используй фото с четкими объектами")
	print("- Люди, машины, животные определяются лучше всего")
	print("- Избегай размытых или темных фото")

	while True:
		print("\n" + "=" * 50)
		print("Выбери вариант:")
		print("1. Использовать тестовое изображение (автоскачивание)")
		print("2. Указать путь к своему изображению")
		print("3. Выход")

		choice = input("Твой выбор (1/2/3): ").strip()

		if choice == '3':
			break

		image_path = None

		if choice == '1':
			image_path = download_sample_image()
			if not image_path:
				continue

		elif choice == '2':
			custom_path = input("Введи полный путь к изображению: ").strip()
			if os.path.exists(custom_path):
				image_path = custom_path
			else:
				print("❌ Файл не найден! Проверь путь.")
				continue
		else:
			print("❌ Неверный выбор!")
			continue

		try:
			print("🔍 Анализирую изображение...")

			results = detector(image_path)

			output_path = show_image_with_boxes(image_path, results)

			print(f"\n✅ Результат сохранен в: {output_path}")
			print("💡 Файл 'detection_result.jpg' в папке с программой")

		except Exception as e:
			print(f"❌ Ошибка при анализе: {e}")
			print("💡 Попробуй другое изображение")


def main():
	detect_objects()


if __name__ == "__main__":
	main()
