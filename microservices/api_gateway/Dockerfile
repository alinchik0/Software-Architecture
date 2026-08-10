FROM python:3.11-slim

WORKDIR /app

# Копируем requirements.txt из корня (контекст сборки будет корнем)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем необходимые папки для работы импортов
COPY api_gateway/ ./api_gateway/
COPY shared/ ./shared/
# Копируем proto-файлы, так как api_gateway их импортирует
COPY user_service/protos/ ./user_service/protos/
COPY playlist_service/protos/ ./playlist_service/protos/
COPY catalog_service/ ./catalog_service/

# Указываем Python искать модули от корня /app (аналог sys.path.insert)
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]