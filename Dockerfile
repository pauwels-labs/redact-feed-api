FROM python:3.10.0b2-alpine3.13 AS builder

COPY src/ src/
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ARG FLASK_ENV='production'
ARG FLASK_DEBUG='false'
EXPOSE 8080
ENTRYPOINT ["python","src/server.py"]