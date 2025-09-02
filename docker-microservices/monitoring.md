# Exercice : Stack de Monitoring Complète
## Durée : 30 minutes

### Objectif
Déployer Prometheus + Grafana et instrumenter des microservices avec métriques et alertes

---

## Phase 1 : Setup Stack Monitoring (8 min)

### Structure du projet
```
monitoring/
├── docker-compose.yml
├── prometheus.yml
├── alertmanager.yml
├── grafana/
│   ├── dashboards/
│   │   └── microservices-dashboard.json
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml
│       └── dashboards/
│           └── dashboard.yml
└── apps/
    ├── user-service/
    │   ├── Dockerfile
    │   └── app.py
    └── order-service/
        ├── Dockerfile
        └── server.js
```

### Docker Compose principal
Créez `docker-compose.yml` :
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alertmanager.yml:/etc/prometheus/alertmanager.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana-storage:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

  # Microservices
  user-service:
    build: ./apps/user-service
    container_name: user-service
    ports:
      - "8001:8000"
    environment:
      - SERVICE_NAME=user-service

  order-service:
    build: ./apps/order-service
    container_name: order-service
    ports:
      - "8002:3000"
    environment:
      - SERVICE_NAME=order-service

volumes:
  grafana-storage:
```

### Configuration Prometheus
Créez `prometheus.yml` :
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'user-service'
    static_configs:
      - targets: ['user-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'order-service'
    static_configs:
      - targets: ['order-service:3000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Configuration Alertmanager
Créez `alertmanager.yml` :
```yaml
global:
  smtp_smarthost: 'localhost:587'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/webhook'
    send_resolved: true
```

---

## Phase 2 : Microservices Instrumentés (12 min)

### User Service (Python + Prometheus)
Créez `apps/user-service/app.py` :
```python
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import random
import os

app = Flask(__name__)

# Métriques Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
ERROR_COUNT = Counter('application_errors_total', 'Total application errors', ['service', 'type'])
BUSINESS_METRICS = Counter('business_operations_total', 'Business operations', ['operation', 'status'])

# Simulation données
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@test.com", "active": True},
    {"id": 2, "name": "Bob", "email": "bob@test.com", "active": True},
    {"id": 3, "name": "Charlie", "email": "charlie@test.com", "active": False}
]

def update_active_users():
    active_count = len([u for u in users_db if u.get('active', False)])
    ACTIVE_USERS.set(active_count)

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # Métriques de requêtes HTTP
    duration = time.time() - request.start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).observe(duration)
    
    return response

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "user-service"})

@app.route('/users')
def get_users():
    try:
        # Simulation latence variable
        time.sleep(random.uniform(0.01, 0.1))
        
        BUSINESS_METRICS.labels(operation='get_users', status='success').inc()
        update_active_users()
        
        return jsonify({
            "users": users_db,
            "total": len(users_db),
            "active": len([u for u in users_db if u.get('active')])
        })
    except Exception as e:
        ERROR_COUNT.labels(service='user-service', type='database_error').inc()
        BUSINESS_METRICS.labels(operation='get_users', status='error').inc()
        return jsonify({"error": str(e)}), 500

@app.route('/users/<int:user_id>')
def get_user(user_id):
    try:
        # Simulation d'erreur pour test
        if user_id == 999:
            ERROR_COUNT.labels(service='user-service', type='not_found').inc()
            return jsonify({"error": "User not found"}), 404
        
        if user_id == 500:
            ERROR_COUNT.labels(service='user-service', type='server_error').inc()
            raise Exception("Database connection failed")
        
        user = next((u for u in users_db if u["id"] == user_id), None)
        if user:
            BUSINESS_METRICS.labels(operation='get_user', status='success').inc()
            return jsonify(user)
        else:
            ERROR_COUNT.labels(service='user-service', type='not_found').inc()
            return jsonify({"error": "User not found"}), 404
            
    except Exception as e:
        ERROR_COUNT.labels(service='user-service', type='server_error').inc()
        BUSINESS_METRICS.labels(operation='get_user', status='error').inc()
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users', methods=['POST'])
def create_user():
    try:
        # Simulation création utilisateur
        time.sleep(random.uniform(0.05, 0.2))
        
        new_user = {
            "id": len(users_db) + 1,
            "name": f"User{len(users_db) + 1}",
            "email": f"user{len(users_db) + 1}@test.com",
            "active": True
        }
        users_db.append(new_user)
        
        BUSINESS_METRICS.labels(operation='create_user', status='success').inc()
        update_active_users()
        
        return jsonify(new_user), 201
    except Exception as e:
        ERROR_COUNT.labels(service='user-service', type='creation_error').inc()
        BUSINESS_METRICS.labels(operation='create_user', status='error').inc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    update_active_users()
    app.run(host='0.0.0.0', port=8000)
```

Créez `apps/user-service/Dockerfile` :
```dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN pip install flask prometheus_client
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
```

### Order Service (Node.js + Prometheus)
Créez `apps/order-service/server.js` :
```javascript
const express = require('express');
const promClient = require('prom-client');

const app = express();
const port = 3000;

// Métriques Prometheus
const collectDefaultMetrics = promClient.collectDefaultMetrics;
collectDefaultMetrics({ timeout: 5000 });

const httpRequestsTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route'],
  buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5]
});

const activeOrders = new promClient.Gauge({
  name: 'active_orders_total',
  help: 'Number of active orders'
});

const businessOperations = new promClient.Counter({
  name: 'business_operations_total',
  help: 'Business operations counter',
  labelNames: ['operation', 'status']
});

// Simulation base de données
let orders = [
  { id: 1, userId: 1, product: "Laptop", amount: 1200, status: "completed" },
  { id: 2, userId: 2, product: "Mouse", amount: 25, status: "pending" },
  { id: 3, userId: 1, product: "Keyboard", amount: 75, status: "active" }
];

function updateActiveOrders() {
  const active = orders.filter(o => o.status === 'active' || o.status === 'pending').length;
  activeOrders.set(active);
}

// Middleware pour métriques
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    
    httpRequestsTotal.labels(req.method, req.route?.path || req.path, res.statusCode).inc();
    httpRequestDuration.labels(req.method, req.route?.path || req.path).observe(duration);
  });
  
  next();
});

app.use(express.json());

// Endpoint métriques
app.get('/metrics', (req, res) => {
  res.set('Content-Type', promClient.register.contentType);
  res.end(promClient.register.metrics());
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'order-service' });
});

app.get('/orders', (req, res) => {
  try {
    // Simulation latence
    setTimeout(() => {
      businessOperations.labels('get_orders', 'success').inc();
      updateActiveOrders();
      res.json({
        orders: orders,
        total: orders.length,
        active: orders.filter(o => o.status === 'active').length
      });
    }, Math.random() * 100);
    
  } catch (error) {
    businessOperations.labels('get_orders', 'error').inc();
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/orders/:id', (req, res) => {
  try {
    const orderId = parseInt(req.params.id);
    
    // Simulation d'erreurs pour tests
    if (orderId === 999) {
      businessOperations.labels('get_order', 'not_found').inc();
      return res.status(404).json({ error: 'Order not found' });
    }
    
    if (orderId === 500) {
      businessOperations.labels('get_order', 'error').inc();
      throw new Error('Database error');
    }
    
    const order = orders.find(o => o.id === orderId);
    if (order) {
      businessOperations.labels('get_order', 'success').inc();
      res.json(order);
    } else {
      businessOperations.labels('get_order', 'not_found').inc();
      res.status(404).json({ error: 'Order not found' });
    }
    
  } catch (error) {
    businessOperations.labels('get_order', 'error').inc();
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/orders', (req, res) => {
  try {
    const newOrder = {
      id: orders.length + 1,
      userId: req.body.userId || 1,
      product: req.body.product || 'Unknown Product',
      amount: req.body.amount || 0,
      status: 'active'
    };
    
    orders.push(newOrder);
    businessOperations.labels('create_order', 'success').inc();
    updateActiveOrders();
    
    res.status(201).json(newOrder);
    
  } catch (error) {
    businessOperations.labels('create_order', 'error').inc();
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Order service running on port ${port}`);
  updateActiveOrders();
});
```

Créez `apps/order-service/Dockerfile` :
```dockerfile
FROM node:16-alpine
WORKDIR /app
RUN npm init -y && npm install express prom-client
COPY server.js .
EXPOSE 3000
CMD ["node", "server.js"]
```

---

## Phase 3 : Configuration Grafana (7 min)

### Datasource Prometheus
Créez `grafana/provisioning/datasources/prometheus.yml` :
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Configuration Dashboard
Créez `grafana/provisioning/dashboards/dashboard.yml` :
```yaml
apiVersion: 1

providers:
  - name: 'microservices'
    orgId: 1
    folder: 'Microservices'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

### Dashboard Microservices
Créez `grafana/dashboards/microservices-dashboard.json` :
```json
{
  "dashboard": {
    "id": null,
    "title": "Microservices Monitoring",
    "tags": ["microservices", "prometheus"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{service}} - {{method}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [{"unit": "s"}],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          },
          {
            "expr": "rate(http_requests_total{status_code=~\"4..\"}[5m])",
            "legendFormat": "4xx errors"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Active Users & Orders",
        "type": "stat",
        "targets": [
          {
            "expr": "active_users_total",
            "legendFormat": "Active Users"
          },
          {
            "expr": "active_orders_total",
            "legendFormat": "Active Orders"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "5s"
  }
}
```

---

## Phase 4 : Alertes et Tests (3 min)

### Règles d'alertes
Créez `alert_rules.yml` dans le dossier racine :
```yaml
groups:
- name: microservices_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High response time"
      description: "95th percentile response time is {{ $value }}s"

  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service is down"
      description: "{{ $labels.instance }} is down"
```

### Déploiement et tests
```bash
# Démarrage de la stack
docker-compose up -d

# Attendre que les services démarrent (30-60 secondes)
docker-compose ps

# Tests de génération de métriques
# Requêtes normales
curl http://localhost:8001/users
curl http://localhost:8002/orders

# Génération d'erreurs pour alertes
curl http://localhost:8001/users/999  # 404
curl http://localhost:8001/users/500  # 500
curl http://localhost:8002/orders/999 # 404

# Création de données
curl -X POST http://localhost:8001/users
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{"userId": 1, "product": "Monitor", "amount": 300}'
```

### Accès aux interfaces
- **Prometheus** : http://localhost:9090
- **Grafana** : http://localhost:3000 (admin/admin123)
- **Alertmanager** : http://localhost:9093

---

## Points de validation

### Vérifications
✅ Prometheus collecte les métriques des 2 services  
✅ Grafana affiche le dashboard avec données  
✅ Les métriques business (users actifs, commandes) sont visibles  
✅ Les alertes se déclenchent sur erreurs  
✅ Les temps de réponse sont mesurés  

### Questions d'évaluation
1. **Quelles métriques sont essentielles pour les microservices ?**
2. **Comment optimiser les performances de Prometheus ?**
3. **Quand déclencher des alertes critiques vs warnings ?**
4. **Comment éviter la surcharge de métriques ?**

### Extensions possibles
- Ajout de Jaeger pour le tracing distribué
- Métriques applicatives métier avancées
- Intégration avec des notifications Slack/Teams
- Service mesh monitoring avec Istio
