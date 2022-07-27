FROM python:3.9.2-alpine3.13 AS builder

COPY src/ src/
ADD requirements.txt requirements.txt
RUN apk update && apk add gcc musl-dev python3-dev libffi-dev openssl-dev cargo

RUN pip install --upgrade pip \
    pip install -r requirements.txt

ARG FLASK_ENV='production'
ARG FLASK_DEBUG='false'
EXPOSE 8080
ENTRYPOINT ["python","-u","src/server.py"]