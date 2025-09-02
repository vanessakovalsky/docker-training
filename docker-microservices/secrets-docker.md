# Configuration des secrets Docker

## Objectif

- Sécuriser une base de données avec Docker Secrets

## Consignes

1. Créer les fichiers de secrets
2. Configurer docker-compose avec secrets
3. Modifier l'application pour utiliser les secrets
4. Tester la sécurité

**Fichiers à créer** :

```bash
# Création des secrets
mkdir secrets
echo "super_secret_password" | docker secret create db_password -
echo "api_key_12345" | docker secret create api_key -
```

```yaml
# docker-compose.secrets.yml
version: '3.8'
services:
  db:
    image: postgres:15
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_DB=microservices
      - POSTGRES_USER=admin
    
  app:
    build: .
    secrets:
      - db_password
      - api_key
    environment:
      - DB_HOST=db
      - DB_USER=admin
      - DB_NAME=microservices
    depends_on:
      - db

secrets:
  db_password:
    external: true
  api_key:
    external: true
```

**Questions** :
- Comment vérifier que les secrets ne sont pas visibles dans les variables d'environnement ?
- Que se passe-t-il si on essaie d'accéder aux secrets depuis l'extérieur du conteneur ?
