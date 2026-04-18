import os
from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import PyPDFLoader
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

# 1. Инициализация Langfuse (версия 3.x)
langfuse_client = Langfuse(
    public_key="pk-lf-test-123-456",
    secret_key="sk-lf-test-456-789",
    host="http://localhost:3000"
)
langfuse_handler = CallbackHandler()

# 2. Создаем модель
llm = OllamaLLM(model="llama3.1:8b", temperature=0.1)


# 3. Функция для анализа
def analyze_pdf(file_path: str, question: str):
    print(f"📄 Загружаю документ: {file_path}")
    print(f"❓ Вопрос: {question}")
    print("=" * 50)

    # Загружаем PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # Объединяем текст (первые ~6000 символов)
    full_text = "\n\n".join([doc.page_content for doc in documents])
    context = full_text[:6000]

    # Промпт для анализа
    prompt = f"""
Ты — технический аналитик. Проанализируй предоставленный документ и ответь на вопрос.
Используй ТОЛЬКО информацию из документа. Если информации нет — так и скажи.

ДОКУМЕНТ (начало):
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{question}

ТВОЙ АНАЛИЗ (структурируй по пунктам, выдели риски и требования отдельно):
"""

    print("🤖 Анализирую с помощью LLM...")

    # Запускаем с мониторингом через langfuse_handler
    result = llm.invoke(prompt, config={"callbacks": [langfuse_handler]})

    print("\n" + "=" * 50)
    print("✅ АНАЛИЗ ЗАВЕРШЁН!")
    print("=" * 50)
    print("\n📋 РЕЗУЛЬТАТ:\n")
    print(result)

    # Сохраняем в файл
    with open("анализ_результат.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\n💾 Результат сохранён в 'анализ_результат.txt'")


# 4. Запуск
if __name__ == "__main__":
    PDF_FILE = "K-550.pdf"
    QUESTION = "Выдели основные риски и ключевые требования из этого документа."

    if not os.path.exists(PDF_FILE):
        print(f"Файл '{PDF_FILE}' не найден в папке с программой!")
    else:
        analyze_pdf(PDF_FILE, QUESTION)
        