# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY crewai_app/ ./crewai_app/
COPY .env .

# Install git commit-msg hook for project key enforcement
COPY .githooks/commit-msg .git/hooks/commit-msg
RUN chmod +x .git/hooks/commit-msg

EXPOSE 8000

CMD ["uvicorn", "crewai_app.main:app", "--host", "0.0.0.0", "--port", "8000"] 