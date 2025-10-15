# Use a slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for SQLite & Chroma
RUN apt-get update && apt-get install -y build-essential libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI server (production mode, no reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
