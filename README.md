## How to run the application

This repository is using poetry as python package manager, you can install poetry by running `pip install poetry`

Install Poetry:

```
pip install poetry==1.1.12
```

How to run the applications:

```
poetry install
poetry shell
uvicorn app.main:app --reload
```

Running with docker:

```
docker build -t chad-backend .
docker run -it -p 8080:80 chad-backend
```

## Deploying

### Build and push docker image to image store

A github action will pick up a commit on `main` (as long as its a `backend/` change) and push to GCP.

### Deploy

Log in to GCP and click manually.

### Deprecated Section

#### Staging

```
docker build --platform linux/amd64 --build-arg ENV_VAR=staging -t us-docker.pkg.dev/heckin-unicorn-test/chad-be-staging/chad-be-staging .
docker push us-docker.pkg.dev/heckin-unicorn-test/chad-be-staging/chad-be-staging
```

#### Prod

```
docker build --platform linux/amd64 --build-arg ENV_VAR=prod -t us-docker.pkg.dev/chad-production-379416/chad-be-prod/chad-be-prod .
docker push us-docker.pkg.dev/chad-production-379416/chad-be-prod/chad-be-prod
```
