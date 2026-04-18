from transformers import pipeline


def simple_chat():
	print("ПРОСТОЙ ЧАТ-БОТ")

	try:
		generator = pipeline(
			"text-generation",
			model="distilgpt2",
			max_length=100,
			do_sample=True,
			temperature=0.5
		)

	except Exception as e:
		print(f"❌ Ошибка: {e}")
		return

	while True:
		text = input("\nТы: ")
		if text.lower() == 'выход':
			break

		result = generator(text, max_length=150)
		response = result[0]['generated_text']

		if response.startswith(text):
			response = response[len(text):].strip()

		print(f"Бот: {response}")


if __name__ == "__main__":
	simple_chat()
