import os
import importlib
import sys


def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')


def print_menu():
	print("🤖 ML ПРИЛОЖЕНИЯ - НОУТБУК 2")
	print("=" * 50)
	print("1. 🖼  Определение объектов на фото")
	print("2. 🎥 Анализ видео")
	print("3. 💬 Локальный чат-бот")
	print("0. ❌ Выход")
	print("=" * 50)
	print("💡 Задачи: Изображения + Видео + Чат-бот")


def run_task(task_number):
	tasks = {
		'1': ('object_detection', 'detect_objects'),
		'2': ('video_analysis', 'analyze_video'),
		'3': ('local_chat', 'chat')
	}

	if task_number in tasks:
		module_name, function_name = tasks[task_number]

		try:
			module = importlib.import_module(module_name)
			function = getattr(module, function_name)

			clear_screen()
			print(f"🚀 Запускаю задачу {task_number}...")
			print("⚠️  Первый запуск может занять время!")
			print("-" * 50)

			function()

		except ImportError as e:
			print(f"❌ Ошибка: Файл {module_name}.py не найден")
		except Exception as e:
			print(f"❌ Ошибка: {e}")

	input("\nНажми Enter чтобы продолжить...")


def main():
	while True:
		clear_screen()
		print_menu()

		choice = input("Выбери задачу (0-3): ").strip()

		if choice == '0':
			print("👋 До свидания!")
			break
		elif choice in ['1', '2', '3']:
			run_task(choice)
		else:
			print("❌ Неверный выбор!")
			input("Нажми Enter чтобы продолжить...")


if __name__ == "__main__":
	main()
