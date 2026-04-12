FROM python:3.10-slim

WORKDIR /app

# Prevent Python from writing pyc files & enable logs immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies (for sklearn, scipy, OCR, etc.)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (Docker cache optimization 🚀)
COPY requirements.txt /app/

# Upgrade pip + install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Now copy full project
COPY . /app

# Streamlit config (prevents CORS / headless issues)
RUN mkdir -p /root/.streamlit && \
    echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = 8501\n\
" > /root/.streamlit/config.toml

# Expose port
EXPOSE 8501

# Healthcheck (optional but good for deployment platforms)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run app
CMD ["streamlit", "run", "app.py"]