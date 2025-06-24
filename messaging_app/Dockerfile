# 1. Using a slim base python image to reduce image size
FROM python:3.10-slim

# 2. Setting environment vaiables to prevent .pyc files and enable real-time logs
ENV PYTHONDONTWRITEBYTECODE=1 \ 
    PYTHONUNBUFFERED=1

# 3. Setting the working directory
WORKDIR /app

# 4. Installing system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && apt-get clean

# 5. Installing applications dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


# 6. Copying the rest of the code into the container
COPY . .

# 7. Exposing default network port (-p)
EXPOSE 8000

# 8. Running django app server/ Default cmd for development (can be overwritten in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]