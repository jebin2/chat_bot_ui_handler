FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Chromium browser
RUN apt-get update && apt-get install -y \
    git \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for headless browser
ENV BROWSER_PATH=/usr/bin/chromium
ENV DISPLAY=:99

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp_dir

# Expose port
EXPOSE 7860

# Run only the Flask app (worker starts automatically on first upload)
CMD ["python", "app.py"]