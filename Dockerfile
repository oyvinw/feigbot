FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg
    
RUN apt-get update && \
    apt-get install -y opus-tools

RUN apt-get update && \
    apt-get install -y libffi-dev
    
RUN apt-get update && \
    apt-get install -y python-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "."]
