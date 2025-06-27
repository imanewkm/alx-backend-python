FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

RUN apt-get update && apt-get install -y netcat-openbsd

RUN chmod +x wait-for-db.sh

EXPOSE 8000
ENTRYPOINT ["./wait-for-db.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
