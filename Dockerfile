FROM python:3.11-slim

# System deps for matplotlib, pptx etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# /data is the persistent volume HF mounts — SQLite DB + uploaded files live here
RUN mkdir -p /data/uploads

EXPOSE 7860

CMD ["python", "app.py"]
