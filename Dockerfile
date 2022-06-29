FROM python:3.8-slim-buster as python

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install gcc make git -y \
  && apt-get clean

ENV PATH="/root/.local/bin:${PATH}"
RUN pip install --user poetry
RUN python -m poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml /install/

WORKDIR /install

RUN python -m poetry install --no-dev

COPY ./ /app

WORKDIR /app

ENTRYPOINT ["python", "app.py"]
