# Pipeline de déploiement

## Objectif

- Mettre en place un pipeline complet

## Consignes

1. Créez un repository Git avec l'application de l'exercice précédent
2. Ajouter le pipeline Gitlab CI pour :
   - Builder l'image Docker
   - Pusher vers un registry
3. Lancer l'application avec Docker Compose sur votre poste en utilisant l'image poussez sur la registry

**Template Gitlab CI**

```yaml
image: docker:20.10.24 # image principale (contient docker client + apk)

services:
  - docker:dind

stages:
  - build

build:
  stage: build
  before_script:
    - apk add --no-cache py3-pip
    - pip install lastversion
    - echo "${CI_JOB_TOKEN}" | docker login registry.gitlab.com --username gitlab-ci-token --password-stdin
  script:
    - docker build -t registry.gitlab.com/${CI_PROJECT_PATH}:${CI_JOB_ID} .
    - docker push registry.gitlab.com/${CI_PROJECT_PATH}:${CI_JOB_ID}

```

**Template GitHub Actions** :
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      # À compléter
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      # À compléter
      
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      # À compléter
```
