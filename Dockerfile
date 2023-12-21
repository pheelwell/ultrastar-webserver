FROM python:3.11-slim

RUN pip install poetry

WORKDIR /ultrastar
COPY . .
RUN ls
RUN poetry install --no-root

ENTRYPOINT ["poetry", "run", "flask", "run", "--host=0.0.0.0"]
