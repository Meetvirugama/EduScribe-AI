FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for OpenCV, Whisper (ffmpeg), and PaddleOCR
RUN apt-get update -o Acquire::Retries=5 && \
    apt-get install -y --no-install-recommends --fix-missing \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set python path so modules resolve correctly
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5001

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
