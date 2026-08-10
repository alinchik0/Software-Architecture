FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY catalog_service/ ./catalog_service/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 50053

CMD ["python", "catalog_service/main.py"]