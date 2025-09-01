# Exercice : Implémentation des patterns Circuit Breaker et Health Check

## Objectif
Implémenter les patterns Circuit Breaker et Health Check dans une architecture microservices avec Docker (durée : 60 min)

## Contexte théorique

### Pattern Health Check
Le Health Check permet de vérifier l'état de santé d'un service en exposant des endpoints dédiés. Docker peut utiliser ces endpoints pour surveiller et redémarrer automatiquement les conteneurs défaillants.

### Pattern Circuit Breaker
Le Circuit Breaker protège les microservices contre les cascades de pannes en "ouvrant le circuit" quand un service devient indisponible, évitant ainsi les appels inutiles.

## Architecture de l'exercice

Nous allons créer 3 services :
- **Service A** (Frontend) - avec Circuit Breaker
- **Service B** (API Gateway) - avec Health Check
- **Service C** (Database Service) - avec Health Check simulé

## Étape 1 : Service C - Database Service (15 min)

### Structure des fichiers
```
service-c/
├── app.py
├── requirements.txt
└── Dockerfile
```

### Code Python (app.py)
```python
from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

# Simulation d'une base de données
database_status = {"healthy": True, "records": 1000}

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Simuler des pannes aléatoirement
    if random.random() < 0.2:  # 20% de chance de panne
        return jsonify({
            "status": "unhealthy",
            "message": "Database connection failed"
        }), 503
    
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "records": database_status["records"]
    })

@app.route('/data')
def get_data():
    """Endpoint de données"""
    if random.random() < 0.1:  # 10% de chance d'erreur
        return jsonify({"error": "Database error"}), 500
    
    # Simuler une latence
    time.sleep(random.uniform(0.1, 0.5))
    
    return jsonify({
        "data": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ],
        "timestamp": int(time.time())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### requirements.txt
```
Flask==2.3.2
requests==2.31.0
```

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

# Health check Docker natif
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
CMD ["python", "app.py"]
```

## Étape 2 : Service B - API Gateway avec Health Check (15 min)

### Structure des fichiers
```
service-b/
├── app.py
├── requirements.txt
└── Dockerfile
```

### Code Python (app.py)
```python
from flask import Flask, jsonify
import requests
import time
from datetime import datetime

app = Flask(__name__)

SERVICE_C_URL = "http://service-c:5000"

@app.route('/health')
def health_check():
    """Health check complet incluant les dépendances"""
    health_status = {
        "service": "api-gateway",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {}
    }
    
    try:
        # Vérifier la santé du service C
        response = requests.get(f"{SERVICE_C_URL}/health", timeout=2)
        if response.status_code == 200:
            health_status["dependencies"]["service-c"] = "healthy"
        else:
            health_status["dependencies"]["service-c"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["service-c"] = f"unreachable: {str(e)}"
        health_status["status"] = "unhealthy"
        return jsonify(health_status), 503
    
    return jsonify(health_status)

@app.route('/api/data')
def proxy_data():
    """Proxy vers le service C"""
    try:
        response = requests.get(f"{SERVICE_C_URL}/data", timeout=3)
        return response.json(), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "Service timeout"}), 504
    except Exception as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/ready')
def readiness_check():
    """Readiness probe - vérifie si le service est prêt à recevoir du trafic"""
    try:
        # Test de connectivité vers les services critiques
        response = requests.get(f"{SERVICE_C_URL}/health", timeout=1)
        if response.status_code == 200:
            return jsonify({"status": "ready"}), 200
        else:
            return jsonify({"status": "not ready", "reason": "dependency unhealthy"}), 503
    except:
        return jsonify({"status": "not ready", "reason": "dependency unreachable"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
```

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

# Health check avec curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

EXPOSE 5001
CMD ["python", "app.py"]
```

## Étape 3 : Service A - Frontend avec Circuit Breaker (20 min)

### Structure des fichiers
```
service-a/
├── app.py
├── requirements.txt
└── Dockerfile
```

### Code Python avec Circuit Breaker (app.py)
```python
from flask import Flask, jsonify, render_template_string
import requests
import time
from enum import Enum
from threading import Lock
from datetime import datetime, timedelta

app = Flask(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Tout fonctionne normalement
    OPEN = "open"          # Circuit ouvert, pas d'appels
    HALF_OPEN = "half_open"  # Test de récupération

class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=10, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # Timeout pour les requêtes
        self.recovery_timeout = recovery_timeout  # Temps avant de tester la récupération
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        """Exécute une fonction à travers le circuit breaker"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self):
        """Vérifie s'il faut tenter une récupération"""
        if self.last_failure_time is None:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Appelé en cas de succès"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Appelé en cas d'échec"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Instance globale du circuit breaker
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=20)

SERVICE_B_URL = "http://service-b:5001"

def call_service_b(endpoint):
    """Fonction pour appeler le service B"""
    response = requests.get(f"{SERVICE_B_URL}{endpoint}", timeout=circuit_breaker.timeout)
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")
    return response.json()

@app.route('/')
def dashboard():
    """Dashboard avec état du circuit breaker"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Circuit Breaker Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: Arial; margin: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .closed { background-color: #d4edda; color: #155724; }
            .open { background-color: #f8d7da; color: #721c24; }
            .half-open { background-color: #fff3cd; color: #856404; }
            .error { background-color: #f8d7da; color: #721c24; margin-top: 10px; }
            button { padding: 10px; margin: 5px; font-size: 16px; }
        </style>
    </head>
    <body>
        <h1>Microservices Dashboard</h1>
        
        <div class="status {{ state_class }}">
            <strong>Circuit Breaker État:</strong> {{ circuit_state }}<br>
            <strong>Échecs consécutifs:</strong> {{ failure_count }}/{{ failure_threshold }}<br>
            <strong>Dernière mise à jour:</strong> {{ timestamp }}
        </div>
        
        <button onclick="location.href='/test-api'">Tester API</button>
        <button onclick="location.href='/health-status'">Vérifier Santé</button>
        <button onclick="location.reload()">Actualiser</button>
        
        {% if error %}
        <div class="error">
            <strong>Erreur:</strong> {{ error }}
        </div>
        {% endif %}
        
        {% if data %}
        <div style="margin-top: 20px;">
            <strong>Données reçues:</strong>
            <pre>{{ data }}</pre>
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    return render_template_string(html,
        circuit_state=circuit_breaker.state.value.upper(),
        state_class=circuit_breaker.state.value.replace('_', '-'),
        failure_count=circuit_breaker.failure_count,
        failure_threshold=circuit_breaker.failure_threshold,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/test-api')
def test_api():
    """Test de l'API à travers le circuit breaker"""
    try:
        data = circuit_breaker.call(call_service_b, '/api/data')
        return dashboard_with_data(data=data)
    except Exception as e:
        return dashboard_with_data(error=str(e))

@app.route('/health-status')
def health_status():
    """Vérification de l'état de santé"""
    try:
        health_data = circuit_breaker.call(call_service_b, '/health')
        return dashboard_with_data(data=health_data)
    except Exception as e:
        return dashboard_with_data(error=str(e))

def dashboard_with_data(data=None, error=None):
    """Dashboard avec données ou erreur"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Circuit Breaker Dashboard</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .closed { background-color: #d4edda; color: #155724; }
            .open { background-color: #f8d7da; color: #721c24; }
            .half-open { background-color: #fff3cd; color: #856404; }
            .error { background-color: #f8d7da; color: #721c24; margin-top: 10px; }
            .success { background-color: #d4edda; color: #155724; margin-top: 10px; }
            button { padding: 10px; margin: 5px; font-size: 16px; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Microservices Dashboard</h1>
        
        <div class="status {{ state_class }}">
            <strong>Circuit Breaker État:</strong> {{ circuit_state }}<br>
            <strong>Échecs consécutifs:</strong> {{ failure_count }}/{{ failure_threshold }}<br>
            <strong>Dernière mise à jour:</strong> {{ timestamp }}
        </div>
        
        <button onclick="location.href='/'">Retour</button>
        <button onclick="location.href='/test-api'">Tester API</button>
        <button onclick="location.href='/health-status'">Vérifier Santé</button>
        
        {% if error %}
        <div class="error">
            <strong>Erreur:</strong> {{ error }}
        </div>
        {% endif %}
        
        {% if data %}
        <div class="success">
            <strong>Succès! Données reçues:</strong>
            <pre>{{ data }}</pre>
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    import json
    return render_template_string(html,
        circuit_state=circuit_breaker.state.value.upper(),
        state_class=circuit_breaker.state.value.replace('_', '-'),
        failure_count=circuit_breaker.failure_count,
        failure_threshold=circuit_breaker.failure_threshold,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        data=json.dumps(data, indent=2) if data else None,
        error=error
    )

@app.route('/health')
def health():
    """Health check du frontend"""
    return jsonify({
        "service": "frontend",
        "status": "healthy",
        "circuit_breaker": {
            "state": circuit_breaker.state.value,
            "failures": circuit_breaker.failure_count
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
```

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:5002/health || exit 1

EXPOSE 5002
CMD ["python", "app.py"]
```

## Étape 4 : Docker Compose (10 min)

### docker-compose.yml
```yaml
version: '3.8'

services:
  service-c:
    build: ./service-c
    container_name: database-service
    ports:
      - "5000:5000"
    networks:
      - microservices-net
    restart: unless-stopped

  service-b:
    build: ./service-b
    container_name: api-gateway
    ports:
      - "5001:5001"
    depends_on:
      - service-c
    networks:
      - microservices-net
    restart: unless-stopped
    environment:
      - SERVICE_C_URL=http://service-c:5000

  service-a:
    build: ./service-a
    container_name: frontend
    ports:
      - "5002:5002"
    depends_on:
      - service-b
    networks:
      - microservices-net
    restart: unless-stopped
    environment:
      - SERVICE_B_URL=http://service-b:5001

networks:
  microservices-net:
    driver: bridge

volumes:
  app-data:
```

## Instructions d'exécution

### 1. Structure finale des fichiers
```
microservices-patterns/
├── service-a/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── service-b/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── service-c/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml
```

### 2. Commandes de lancement
```bash
# Construire et lancer tous les services
docker-compose up --build

# Vérifier l'état des conteneurs
docker-compose ps

# Voir les logs
docker-compose logs -f
```

### 3. Tests à effectuer

1. **Accéder au dashboard** : http://localhost:5002
2. **Tester l'API** : Cliquer sur "Tester API" plusieurs fois
3. **Observer le Circuit Breaker** : 
   - État CLOSED → Tout fonctionne
   - État OPEN → Après 3 échecs consécutifs
   - État HALF_OPEN → Tentative de récupération

4. **Vérifier les Health Checks** :
   - Service A : http://localhost:5002/health
   - Service B : http://localhost:5001/health  
   - Service C : http://localhost:5000/health

5. **Simuler des pannes** :
   ```bash
   # Arrêter le service C
   docker-compose stop service-c
   
   # Observer le comportement du Circuit Breaker
   # Redémarrer le service
   docker-compose start service-c
   ```

## Points d'apprentissage

### Circuit Breaker
- **États** : CLOSED, OPEN, HALF_OPEN
- **Seuil d'échecs** : Nombre d'échecs avant ouverture
- **Timeout de récupération** : Temps d'attente avant test de récupération
- **Protection** : Évite les cascades de pannes

### Health Checks
- **Liveness** : Le service est-il en vie ?
- **Readiness** : Le service est-il prêt à recevoir du trafic ?
- **Dependency checks** : État des services dépendants
- **Docker integration** : HEALTHCHECK dans Dockerfile

### Observabilité
- **Monitoring** : État en temps réel des circuits
- **Métriques** : Nombre d'échecs, états des services
- **Logs** : Traçabilité des erreurs et récupérations

## Extensions possibles

1. **Métriques Prometheus** : Ajout de métriques pour monitoring
2. **Circuit Breaker avancé** : Implémentation avec hystrix-py
3. **Health Check custom** : Vérifications métier spécifiques
4. **Load Balancer** : Nginx avec health checks
5. **Service Discovery** : Consul ou Eureka
