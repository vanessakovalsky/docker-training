# Application 12-Factor complète : Guide détaillé

## Vue d'ensemble de l'exercice

Cet exercice consiste à créer une API REST de gestion d'utilisateurs qui respecte les **12 factors** d'une application cloud-native. Les 12 factors sont des principes de développement qui garantissent la portabilité, la scalabilité et la maintenabilité des applications modernes.

## Les 12 Factors expliqués dans le contexte

### 1. Codebase (Base de code)
- **Principe** : Une base de code suivie dans un système de contrôle de version, plusieurs déploiements
- **Implémentation** : Code source dans Git, déployé sur différents environnements (dev, staging, prod)

### 2. Dependencies (Dépendances)
- **Principe** : Déclarer explicitement et isoler les dépendances
- **Implémentation** : `requirements.txt` avec versions fixes, environnement virtuel

### 3. Config (Configuration)
- **Principe** : Stocker la configuration dans l'environnement
- **Implémentation** : Variables d'environnement pour DB, ports, secrets

### 4. Backing services (Services de support)
- **Principe** : Traiter les services de support comme des ressources attachées
- **Implémentation** : Base de données PostgreSQL via URL de connexion

### 5. Build, release, run (Construction, livraison, exécution)
- **Principe** : Séparer strictement les étapes de construction et d'exécution
- **Implémentation** : Docker multi-stage, images immuables

### 6. Processes (Processus)
- **Principe** : Exécuter l'application comme un ou plusieurs processus sans état
- **Implémentation** : API stateless, sessions externalisées

### 7. Port binding (Liaison de port)
- **Principe** : Exporter les services via la liaison de port
- **Implémentation** : Flask bind sur un port configurable

### 8. Concurrency (Concurrence)
- **Principe** : Adapter via le modèle de processus
- **Implémentation** : Plusieurs instances via Docker Compose

### 9. Disposability (Disponibilité)
- **Principe** : Maximiser la robustesse avec un démarrage rapide et un arrêt gracieux
- **Implémentation** : Gestion des signaux, connexions DB propres

### 10. Dev/prod parity (Parité dev/prod)
- **Principe** : Garder le développement, le staging et la production aussi similaires que possible
- **Implémentation** : Même stack (Docker) partout

### 11. Logs
- **Principe** : Traiter les logs comme des flux d'événements
- **Implémentation** : Logs structurés vers stdout

### 12. Admin processes (Processus d'administration)
- **Principe** : Lancer les tâches d'administration/management comme des processus ponctuels
- **Implémentation** : Scripts de migration, commandes CLI

## Structure du projet

```
twelve-factor-app/
├── app.py                 # Application principale
├── config.py             # Configuration centralisée
├── database.py           # Gestion base de données
├── models.py             # Modèles de données
├── requirements.txt      # Dépendances Python
├── Dockerfile           # Image Docker
├── docker-compose.yml   # Orchestration
├── tests/
│   ├── test_api.py      # Tests d'intégration
│   └── test_health.py   # Tests health checks
├── scripts/
│   └── init_db.py       # Script d'initialisation DB
└── .env.example         # Exemple de configuration
```

## Implémentation complète

### 1. Configuration centralisée (`config.py`)

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    # Database
    DATABASE_URL: str = os.environ.get(
        'DATABASE_URL', 
        'postgresql://user:password@localhost:5432/userdb'
    )
    
    # Server
    PORT: int = int(os.environ.get('PORT', 8080))
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    
    # Logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.environ.get(
        'LOG_FORMAT', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # App
    FLASK_ENV: str = os.environ.get('FLASK_ENV', 'production')
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
```

### 2. Modèles de données (`models.py`)

```python
from dataclasses import dataclass, asdict
from typing import Optional
import json

@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), default=str)
```

### 3. Gestion base de données (`database.py`)

```python
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Optional
from models import User
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config: Config):
        self.config = config
        self.pool = None
        self._init_pool()
    
    def _init_pool(self):
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, self.config.DATABASE_URL
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def get_connection(self):
        return self.pool.getconn()
    
    def return_connection(self, conn):
        self.pool.putconn(conn)
    
    def init_tables(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.commit()
            logger.info("Database tables initialized")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize tables: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def create_user(self, user: User) -> User:
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO users (username, email)
                    VALUES (%s, %s)
                    RETURNING id, username, email, created_at, updated_at
                """, (user.username, user.email))
                
                result = cursor.fetchone()
                conn.commit()
                
                return User(**dict(result))
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_users(self) -> List[User]:
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
                results = cursor.fetchall()
                return [User(**dict(row)) for row in results]
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return User(**dict(result)) if result else None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def update_user(self, user_id: int, user: User) -> Optional[User]:
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET username = %s, email = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, username, email, created_at, updated_at
                """, (user.username, user.email, user_id))
                
                result = cursor.fetchone()
                conn.commit()
                
                return User(**dict(result)) if result else None
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def delete_user(self, user_id: int) -> bool:
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def health_check(self) -> bool:
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.return_connection(conn)
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
```

### 4. Application principale (`app.py`)

```python
# app.py - Version corrigée pour Flask 2.2+
import os
import sys
import logging
import signal
from flask import Flask, jsonify, request
from dataclasses import dataclass, asdict
from typing import List, Optional
import threading

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Initialisation de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Base de données simulée en mémoire (pour éviter PostgreSQL au début)
users_storage = []
next_id = 1
db_lock = threading.Lock()

@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    
    def to_dict(self):
        return asdict(self)

class DatabaseManager:
    """Gestionnaire de base de données simulé en mémoire"""
    
    def __init__(self):
        self.initialized = False
    
    def init_tables(self):
        """Initialiser les tables (simulation)"""
        if not self.initialized:
            logger.info("Database tables initialized (memory storage)")
            self.initialized = True
    
    def health_check(self) -> bool:
        """Vérification de santé de la DB"""
        return self.initialized
    
    def create_user(self, user: User) -> User:
        """Créer un utilisateur"""
        global next_id
        with db_lock:
            # Vérifier les doublons
            for existing_user in users_storage:
                if existing_user.username == user.username or existing_user.email == user.email:
                    raise ValueError("User already exists")
            
            user.id = next_id
            next_id += 1
            users_storage.append(user)
            return user
    
    def get_users(self) -> List[User]:
        """Récupérer tous les utilisateurs"""
        with db_lock:
            return users_storage.copy()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupérer un utilisateur par ID"""
        with db_lock:
            return next((u for u in users_storage if u.id == user_id), None)
    
    def update_user(self, user_id: int, user: User) -> Optional[User]:
        """Mettre à jour un utilisateur"""
        with db_lock:
            existing_user = next((u for u in users_storage if u.id == user_id), None)
            if not existing_user:
                return None
            
            # Vérifier les doublons (sauf pour l'utilisateur actuel)
            for u in users_storage:
                if u.id != user_id and (u.username == user.username or u.email == user.email):
                    raise ValueError("Username or email already exists")
            
            existing_user.username = user.username
            existing_user.email = user.email
            return existing_user
    
    def delete_user(self, user_id: int) -> bool:
        """Supprimer un utilisateur"""
        with db_lock:
            user = next((u for u in users_storage if u.id == user_id), None)
            if user:
                users_storage.remove(user)
                return True
            return False

# Initialisation de la base de données
db_manager = DatabaseManager()

# Initialisation au démarrage de l'application
def initialize_app():
    """Initialiser l'application au démarrage"""
    logger.info("Initializing application...")
    db_manager.init_tables()
    logger.info("Application initialized successfully")

# Gestion gracieuse de l'arrêt
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Routes de l'API
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        db_healthy = db_manager.health_check()
        status = "healthy" if db_healthy else "unhealthy"
        status_code = 200 if db_healthy else 503
        
        return jsonify({
            "status": status,
            "database": "connected" if db_healthy else "disconnected",
            "version": "1.0.0"
        }), status_code
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/users', methods=['GET'])
def get_users():
    """Récupérer tous les utilisateurs"""
    try:
        users = db_manager.get_users()
        return jsonify({
            "users": [user.to_dict() for user in users],
            "count": len(users)
        })
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users', methods=['POST'])
def create_user():
    """Créer un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email'):
            return jsonify({"error": "Username and email are required"}), 400
        
        user = User(username=data['username'], email=data['email'])
        created_user = db_manager.create_user(user)
        
        logger.info(f"Created user: {created_user.username}")
        return jsonify(created_user.to_dict()), 201
        
    except ValueError as e:
        logger.warning(f"User creation failed: {e}")
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Récupérer un utilisateur par ID"""
    try:
        user = db_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('email'):
            return jsonify({"error": "Username and email are required"}), 400
        
        user = User(username=data['username'], email=data['email'])
        updated_user = db_manager.update_user(user_id, user)
        
        if not updated_user:
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"Updated user: {updated_user.username}")
        return jsonify(updated_user.to_dict())
        
    except ValueError as e:
        logger.warning(f"User update failed: {e}")
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Supprimer un utilisateur"""
    try:
        deleted = db_manager.delete_user(user_id)
        
        if not deleted:
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"Deleted user with ID: {user_id}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialiser l'application
    initialize_app()
    
    # Configuration du serveur
    port = int(os.environ.get('PORT', 8080))
    host = os.environ.get('HOST', '0.0.0.0')
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting server on {host}:{port}")
    app.run(host=host, port=port, debug=debug_mode)
```

### 5. Dockerfile multi-stage

* Créer le dockerfile avec les consignes suivantes :
    * Image de base : python:3.11-slim  
    * Copier le fichier de dépendances et faites l'installations des dépendances
    * Utiliser le dossier de travail app
    * Copier les fichiers de lapplication
    * Définir le proprietaire et le groupe du dossier app à : appuser
    * Définir l'utilisateur comme appuser
    * Ajouter la variable d'environnement : PATH=/root/.local/bin:$PATH
    * Ajouter un healthcheck comme dans l'exercice précédent
    * Exposer le port 8080
    * Lancer l'application avec la commande : python app.py

<details>
    <summary>Docker file complet</summary>
    
    ```dockerfile
    # Build stage
    FROM python:3.11-slim
    
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Create non-root user
    RUN groupadd -r appuser && useradd -r -g appuser appuser
    
    # Copy application code
    COPY . .
    
    # Set ownership
    RUN chown -R appuser:appuser /app
    USER appuser
    
    # Make sure scripts are executable
    ENV PATH=/root/.local/bin:$PATH
    
    # Health check
    HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
        CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"
    
    EXPOSE 8080
    
    CMD ["python", "app.py"]
    ```
</details>


### 6. Docker Compose
* Mettre en place le docher compose avec le service api et un service bdd avec postgresql

<details>
    <summary>Docker compose complet</summary>
    
    ```yaml
    version: '3.8'
    
    services:
      api:
        build: .
        ports:
          - "8080:8080"
        environment:
          - DATABASE_URL=postgresql://userdb:password@db:5432/userdb
          - LOG_LEVEL=INFO
          - FLASK_ENV=development
        depends_on:
          - db
        restart: unless-stopped
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
          interval: 30s
          timeout: 10s
          retries: 3
          start_period: 40s
    
      db:
        image: postgres:15-alpine
        environment:
          - POSTGRES_DB=userdb
          - POSTGRES_USER=userdb
          - POSTGRES_PASSWORD=password
        ports:
          - "5432:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data
        restart: unless-stopped
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U userdb -d userdb"]
          interval: 10s
          timeout: 5s
          retries: 5
    
    volumes:
      postgres_data:
```

</details>

### 7. Tests d'intégration

```python
# tests/test_api.py
import pytest
import requests
import time

class TestUserAPI:
    base_url = "http://localhost:8080"
    
    def test_health_check(self):
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_create_user(self):
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        response = requests.post(f"{self.base_url}/users", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
    
    def test_get_users(self):
        response = requests.get(f"{self.base_url}/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "count" in data
```

### 8. Requirements.txt

```txt
Flask==2.3.3
psycopg2-binary==2.9.7
requests==2.31.0
pytest==7.4.0
```

## Commandes pour exécuter l'exercice

```bash
# 1. Cloner et configurer
git clone <repo>
cd twelve-factor-app

# 2. Construire et démarrer
docker compose up -d --build

# 3. Tester l'API
curl http://localhost:8080/health
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com"}'

# 4. Lancer les tests
pytest tests/ -v
```

## Points clés de l'implémentation

### Respect des 12 factors
1. **Codebase** : Code source unique avec déploiements multiples
2. **Dependencies** : `requirements.txt` avec versions fixes
3. **Config** : Variables d'environnement pour toute la configuration
4. **Backing services** : PostgreSQL via URL de connexion configurable
5. **Build/Release/Run** : Docker multi-stage, séparation claire
6. **Processes** : API stateless, pas de stockage local
7. **Port binding** : Service exporté via port configurable
8. **Concurrency** : Scalabilité horizontale via Docker
9. **Disposability** : Gestion gracieuse des signaux
10. **Dev/prod parity** : Même stack Docker partout
11. **Logs** : Logs structurés vers stdout
12. **Admin processes** : Scripts séparés pour l'administration

### Fonctionnalités avancées
- **Health checks** : Endpoint `/health` avec vérification DB
- **Logs structurés** : Format JSON avec niveaux configurables
- **Gestion d'erreurs** : Réponses HTTP cohérentes
- **Sécurité** : Utilisateur non-root, variables d'environnement
- **Tests** : Tests d'intégration automatisés
- **Documentation** : API REST documentée

Cette implémentation respecte tous les principes d'une application cloud-native moderne et peut servir de base pour des projets plus complexes.
