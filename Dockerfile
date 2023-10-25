FROM python:3.11
WORKDIR /app
RUN apt-get install wget
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "ingest_data.py"]