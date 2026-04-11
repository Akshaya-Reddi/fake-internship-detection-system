FROM python:3.10-slim

WORKDIR /app

# System dependencies (important for scipy/sklearn + OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Upgrade pip first (VERY IMPORTANT)
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]