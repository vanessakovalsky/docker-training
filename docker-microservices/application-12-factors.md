# Application 12-Factor complète

## Objectif

- Créer une API REST respectant les 12 factors

## Consignes

1. Développez une API simple de gestion d'utilisateurs (CRUD)
2. Implémentez les 12 factors
3. Containerisez l'application
4. Créez les tests d'intégration

**Squelette de code** :
```python
# app.py
import os
import logging
from flask import Flask, jsonify, request
import psycopg2

app = Flask(__name__)
logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/users', methods=['GET'])
def get_users():
    # À implémenter
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

## Solution attendue :
- Configuration via variables d'environnement
- Logs structurés
- Health checks
- Dockerfile optimisé
- docker-compose.yml avec base de données
- Tests automatisés
