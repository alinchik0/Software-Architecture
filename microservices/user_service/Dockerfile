FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY user_service/ ./user_service/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 50051

CMD ["python", "user_service/main.py"]