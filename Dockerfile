FROM python:3.11-slim

WORKDIR /app

# Install git for cloning repos
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py .

# Create directories
RUN mkdir -p /workspace /tmp

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the updater
CMD ["python", "main.py", "--config", "/config/config.yaml"]
