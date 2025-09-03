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