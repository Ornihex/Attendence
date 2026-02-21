FROM python:3.11.14-alpine3.23
COPY ./app /app
COPY ./frontend /frontend
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
