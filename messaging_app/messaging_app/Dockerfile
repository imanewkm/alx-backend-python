# Use the official Python runtime image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Note: The container should be run with -p 8000:8000 to publish the exposed port
# Example: docker run -p 8000:8000 messaging_app

# Expose port (default for Django)
EXPOSE 8000

# Start Django server (adjust if using gunicorn for production)
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]