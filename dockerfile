FROM python:3.9

# Install Rust for zen-engine
# RUN curl https://sh.rustup.rs -sSf | sh -s -- --default-toolchain stable -y
# ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt-get update -qq && \
  apt-get -qq install \
  jq

WORKDIR /code

RUN pip install poetry

COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

ARG ENV_VAR
ENV ENV_VAR=$ENV_VAR

ARG ENV_B64
ENV ENV_B64=$ENV_B64

ARG GCP_B64
ENV GCP_B64=$GCP_B64

COPY ./app /code/app

RUN echo "Environment is: ${ENV_VAR}"
RUN echo "$GCP_B64" | base64 --decode | jq > /code/credentials.json
RUN echo "$ENV_B64" | base64 --decode > "/code/${ENV_VAR}.env"

COPY .en[v] /code/.env

ENV GOOGLE_APPLICATION_CREDENTIALS=/code/credentials.json

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
