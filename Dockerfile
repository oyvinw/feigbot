FROM python:3.10-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

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

CMD ["python", "-m", "feigbot"]
