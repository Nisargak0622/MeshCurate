FROM python:3.12-slim

WORKDIR /app

# Install system dependencies Playwright's Chromium needs
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the actual Chromium browser + its OS-level dependencies
RUN playwright install --with-deps chromium

COPY . .

# Render sets $PORT at runtime; default to 5000 for local testing
ENV PORT=5000
EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:$PORT --timeout 60 app:app
