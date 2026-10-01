FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium and all its OS-level dependencies are already installed in this
# base image, matching playwright==1.47.0 in requirements.txt exactly - no
# separate "playwright install" step needed.

COPY . .

# Render sets $PORT at runtime; default to 5000 for local testing
ENV PORT=5000
EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:$PORT --timeout 60 app:app
