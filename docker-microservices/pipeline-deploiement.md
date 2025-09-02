# Pipeline de déploiement

## Objectif

- Mettre en place un pipeline complet

## Consignes

1. Créez un repository Git avec l'application de l'exercice précédent
2. Configurez Gitlab CI pour :
   - Exécuter les tests
   - Builder l'image Docker
   - Pusher vers un registry
3. Lancer l'application avec Docker Compose sur votre poste en utilisant l'image poussez sur la registry

**Template Gitlab CI**

```yaml
services:
- docker:dind

stages:
- test
- build

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

before_script:
  - python --version
  - pip install --upgrade pip
  - pip install -r requirements.txt
test:
  stage: test
  script:
    - pytest --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml
    paths:
      - .pytest_cache/
    expire_in: 1 week

build:
    stage: build
    before_script:
        - apk add --no-cache py3-pip
        - pip install lastversion
        - docker login -u ${DEPLOY_USER} -p ${DEPLOY_TOKEN} registry.gitlab.com
    script:
        - LASTVERSION=`lastversion ansible-community/ansible-lint`
        - docker build --build-arg VERSION=${LASTVERSION} -t registry.gitlab.com/dockerfiles6/ansible-lint:${LASTVERSION} -t registry.gitlab.com/dockerfiles6/ansible-lint:latest .
        - docker push registry.gitlab.com/dockerfiles6/ansible-lint:${LASTVERSION}
        - docker push registry.gitlab.com/dockerfiles6/ansible-lint:latest
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
