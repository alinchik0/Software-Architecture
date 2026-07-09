FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY notes_agent/ ./notes_agent/
CMD ["uvicorn", "notes_agent.api:app", "--host", "0.0.0.0", "--port", "8001"]