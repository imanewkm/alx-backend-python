FROM python:3.10

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# set work directory
WORKDIR /messageapp

# install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /messageapp/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# add a non-root user
RUN useradd --create-home appuser
USER appuser

# copy project
COPY . /messageapp/

# Expose the port the app runs on
EXPOSE 8000

# run the application
CMD ["gunicorn", "messaging_app.wsgi:application", "--bind", "0.0.0.0:8000"]