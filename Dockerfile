FROM python:3.9-slim-buster

COPY deps/requirements.txt .

RUN pip install -r requirements.txt