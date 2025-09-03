# Exercice : Gestion des secrets dans Docker Compose
**Durée estimée : 30 minutes**

## Objectifs
- Comprendre la gestion des secrets avec les fichiers `.env`
- Maîtriser les surcharges avec `docker-compose.override.yml`
- Appliquer les bonnes pratiques de sécurité

## Contexte
Vous devez déployer une application web avec une base de données PostgreSQL. L'application a besoin de différentes configurations selon l'environnement (développement, test, production).

## Structure du projet à créer
```
secrets-exercise/
├── docker-compose.yml
├── docker-compose.override.yml
├── docker-compose.prod.yml
├── .env
├── .env.example
├── app/
│   └── Dockerfile
└── .gitignore
```

## Étape 1 : Préparation (5 min)

### 1.1 Créer la structure
```bash
mkdir secrets-exercise
cd secrets-exercise
mkdir app
```

### 1.2 Créer le Dockerfile de l'application
**Fichier : `app/Dockerfile`**
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
```

### 1.3 Créer une page web simple
**Fichier : `app/index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>App Secrets Demo</title>
</head>
<body>
    <h1>Application de démonstration</h1>
    <p>Environnement : <span id="env">Non défini</span></p>
</body>
</html>
```

## Étape 2 : Configuration de base (10 min)

### 2.1 Créer le fichier .env.example
**Fichier : `.env.example`**
```env
# Configuration de base
COMPOSE_PROJECT_NAME=secrets-demo
APP_PORT=3000
APP_ENV=development

# Base de données
DB_HOST=postgres
DB_NAME=myapp
DB_USER=user
DB_PASSWORD=changeme
POSTGRES_DB=myapp
POSTGRES_USER=user
POSTGRES_PASSWORD=changeme

# Secrets (à personnaliser)
JWT_SECRET=your-jwt-secret-here
API_KEY=your-api-key-here
ADMIN_EMAIL=admin@example.com
```

### 2.2 Créer le fichier .env réel
```bash
cp .env.example .env
```

**Modifier le fichier `.env` avec de vraies valeurs :**
```env
COMPOSE_PROJECT_NAME=secrets-demo
APP_PORT=3000
APP_ENV=development

# Base de données
DB_HOST=postgres
DB_NAME=myapp
DB_USER=devuser
DB_PASSWORD=dev_secure_password_123
POSTGRES_DB=myapp
POSTGRES_USER=devuser
POSTGRES_PASSWORD=dev_secure_password_123

# Secrets
JWT_SECRET=dev_jwt_secret_key_very_long_and_secure
API_KEY=dev_api_key_12345abcdef
ADMIN_EMAIL=dev@example.com
```

### 2.3 Créer le docker-compose.yml principal
**Fichier : `docker-compose.yml`**
```yaml
version: '3.8'

services:
  app:
    build: ./app
    ports:
      - "${APP_PORT}:80"
    environment:
      - APP_ENV=${APP_ENV}
      - JWT_SECRET=${JWT_SECRET}
      - API_KEY=${API_KEY}
    depends_on:
      - postgres
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

## Étape 3 : Surcharges pour le développement (8 min)

### 3.1 Créer docker-compose.override.yml
**Fichier : `docker-compose.override.yml`**
```yaml
version: '3.8'

services:
  app:
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    volumes:
      - ./app:/usr/share/nginx/html:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app-dev.rule=Host(`localhost`)"

  postgres:
    ports:
      - "5432:5432"  # Exposer pour les outils de dev
    environment:
      - POSTGRES_LOG_STATEMENT=all
    volumes:
      - ./init-dev.sql:/docker-entrypoint-initdb.d/init.sql:ro

  # Service additionnel pour le développement
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      - PGADMIN_DEFAULT_EMAIL=${ADMIN_EMAIL}
      - PGADMIN_DEFAULT_PASSWORD=admin123
    ports:
      - "8080:80"
    depends_on:
      - postgres
    networks:
      - app-network
```

### 3.2 Créer un script d'initialisation pour le dev
**Fichier : `init-dev.sql`**
```sql
-- Données de test pour le développement
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email) VALUES 
    ('testuser1', 'test1@example.com'),
    ('testuser2', 'test2@example.com')
ON CONFLICT DO NOTHING;
```

## Étape 4 : Configuration production (5 min)

### 4.1 Créer docker-compose.prod.yml
**Fichier : `docker-compose.prod.yml`**
```yaml
version: '3.8'

services:
  app:
    restart: unless-stopped
    environment:
      - DEBUG=false
      - LOG_LEVEL=warn
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app-prod.rule=Host(`myapp.example.com`)"
      - "traefik.http.routers.app-prod.tls.certresolver=letsencrypt"
    # Ne pas exposer les volumes en production
    volumes: []

  postgres:
    restart: unless-stopped
    # Ne pas exposer le port en production
    ports: []
    environment:
      - POSTGRES_LOG_STATEMENT=none
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      # Pas de script d'init en production

  # Retirer pgadmin en production
  pgadmin:
    deploy:
      replicas: 0

volumes:
  postgres_prod_data:
    external: true
```

### 4.2 Créer .env.prod.example
**Fichier : `.env.prod.example`**
```env
COMPOSE_PROJECT_NAME=secrets-demo-prod
APP_PORT=80
APP_ENV=production

# Base de données (utiliser des valeurs sécurisées)
DB_HOST=postgres
DB_NAME=myapp_prod
DB_USER=prod_user
DB_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
POSTGRES_DB=myapp_prod
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=CHANGE_THIS_SECURE_PASSWORD

# Secrets (générer de nouvelles valeurs)
JWT_SECRET=GENERATE_A_VERY_LONG_AND_SECURE_JWT_SECRET
API_KEY=GENERATE_A_SECURE_API_KEY
ADMIN_EMAIL=admin@yourdomain.com
```

## Étape 5 : Sécurisation (2 min)

### 5.1 Créer .gitignore
**Fichier : `.gitignore`**
```gitignore
# Secrets - NE JAMAIS COMMITER
.env
.env.prod
.env.local
*.env

# Logs
*.log
logs/

# Données locales
data/
volumes/

# OS
.DS_Store
Thumbs.db
```

### 5.2 Script de déploiement sécurisé
**Fichier : `deploy.sh`**
```bash
#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}

case $ENVIRONMENT in
  "dev")
    echo "🚀 Déploiement en développement"
    docker-compose up -d
    ;;
  "prod")
    echo "🚀 Déploiement en production"
    if [ ! -f .env.prod ]; then
      echo "❌ Fichier .env.prod manquant"
      echo "Copiez .env.prod.example vers .env.prod et configurez les vraies valeurs"
      exit 1
    fi
    docker-compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d
    ;;
  *)
    echo "Usage: $0 [dev|prod]"
    exit 1
    ;;
esac
```

## Tests et validation

### Tester l'environnement de développement
```bash
# Démarrer en dev (utilise automatiquement .env et docker-compose.override.yml)
docker-compose up -d

# Vérifier les services
docker-compose ps

# Voir les logs
docker-compose logs app

# Accéder à l'app : http://localhost:3000
# Accéder à pgAdmin : http://localhost:8080
```

### Tester la configuration production
```bash
# Créer .env.prod à partir de l'exemple
cp .env.prod.example .env.prod
# Éditer .env.prod avec de vraies valeurs sécurisées

# Déployer en prod
chmod +x deploy.sh
./deploy.sh prod
```

### Vérifications de sécurité
```bash
# Vérifier que les secrets ne sont pas dans l'historique Git
git log --grep=password
git log -S "JWT_SECRET"

# Vérifier les variables d'environnement des conteneurs
docker-compose exec app env | grep -E "(JWT|API|PASSWORD)"
```

## Questions de réflexion
1. Pourquoi ne pas mettre les mots de passe directement dans docker-compose.yml ?
2. Quels sont les avantages des fichiers de surcharge ?
3. Comment gérer les secrets en production de manière encore plus sécurisée ?
4. Que se passe-t-il si on oublie de créer le fichier .env ?

## Bonus (si temps restant)
- Utiliser Docker Secrets au lieu des variables d'environnement
- Intégrer avec un gestionnaire de secrets externe (HashiCorp Vault, AWS Secrets Manager)
- Créer un script de rotation des secrets

## Nettoyage
```bash
# Arrêter et nettoyer
docker-compose down -v
cd ..
rm -rf secrets-exercise
```
