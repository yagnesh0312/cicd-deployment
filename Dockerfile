FROM python:3.11.0-slim AS base

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "app.py"]
# CMD ["python", "app.py"]
