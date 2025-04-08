FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Uninstall any existing deepgram-sdk and install the specific version
RUN pip uninstall -y deepgram-sdk && pip install --no-cache-dir deepgram-sdk==2.1.0

# Copy application code
COPY . .

# Create directory for uploaded audio files
RUN mkdir -p /app/uploaded_audio

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 6000

# Command to run the application
CMD ["python", "app.py"] 