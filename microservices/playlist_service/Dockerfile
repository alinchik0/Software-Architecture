FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY playlist_service/ ./playlist_service/
COPY shared/ ./shared/
COPY catalog_service/ ./catalog_service/

ENV PYTHONPATH=/app

EXPOSE 50052

CMD ["python", "playlist_service/main.py"]