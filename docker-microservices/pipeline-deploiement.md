# Pipeline de déploiement

## Objectif

- Mettre en place un pipeline complet

## Consignes

1. Créez un repository Git avec l'application
2. Configurez GitHub Actions pour :
   - Exécuter les tests
   - Builder l'image Docker
   - Pusher vers un registry
3. Déployez avec Docker Compose
4. Créez les manifestes Kubernetes

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
