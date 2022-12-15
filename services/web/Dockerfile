FROM python:3.9-alpine

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
COPY ./app/app.py /src/app.py
COPY ./app/database.py /src/database.py
COPY ./app/constants.py /src/constants.py

# Install postgres and other dependencies
RUN apk add --update --no-cache \
    && pip install -r requirements.txt \
    && adduser -D docker

USER docker

CMD [ "gunicorn", "app:app" ,"-k", "uvicorn.workers.UvicornWorker", \
      "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "3600" ]
