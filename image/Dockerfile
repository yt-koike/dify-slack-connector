FROM python:3.12-slim

RUN mkdir /app
WORKDIR /app

RUN apt update && apt upgrade

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
