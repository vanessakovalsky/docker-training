# Exercice : Logging Centralisé avec Stack ELK
## Durée : 30 minutes

### Objectif
Centraliser les logs de microservices avec ELK et créer un dashboard de monitoring

---

## Phase 1 : Setup ELK rapide (8 min)

### Structure simplifiée
```
elk-quick/
├── docker-compose.yml
├── logstash/
│   └── pipeline.conf
├── services/
│   ├── api
│       └── api.py
│       └── Dockerfile
│   ├── web
│       └── web.js
│       └── Dockerfile
```

### Docker Compose ELK + Services
Créez `docker-compose.yml` :
```yaml
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:7.17.0
    ports:
      - "5000:5000"
      - "5044:5044"
    volumes:
      - ./logstash/pipeline.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    environment:
      - "LS_JAVA_OPTS=-Xmx256m -Xms256m"

  kibana:
    image: kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  # Services métier
  api-service:
    build:
      context: services/api
    ports:
      - "5001:5000"
    depends_on:
      - logstash

  web-service:
    build:
      context: services/web
    ports:
      - "3000:3000"
    depends_on:
      - logstash

volumes:
  es_data:
```

### Configuration Logstash
Créez `logstash/pipeline.conf` :
```ruby
input {
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  mutate {
    add_field => { "[@metadata][index]" => "microservices-%{+YYYY.MM.dd}" }
  }
  
  if [level] == "ERROR" {
    mutate {
      add_tag => [ "error", "alert" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index]}"
  }
  
  stdout { 
    codec => rubydebug 
  }
}
```

---

## Phase 2 : Services avec logs structurés (12 min)

### API Service Python avec logs JSON
Créez `services/api.py` :
```python
import json
import logging
import socket
import time
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuration logging vers Logstash
class LogstashFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "api-service",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, 'request_id', None),
            "user_id": getattr(record, 'user_id', None),
            "execution_time": getattr(record, 'execution_time', None)
        }
        return json.dumps(log_entry)

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler vers Logstash
logstash_handler = logging.handlers.SocketHandler('logstash', 5000)
logstash_handler.setFormatter(LogstashFormatter())
logger.addHandler(logstash_handler)

@app.before_request
def before_request():
    request.start_time = time.time()
    request.request_id = f"req_{int(time.time() * 1000)}"

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    logger.info("HTTP Request", extra={
        'request_id': request.request_id,
        'method': request.method,
        'url': request.url,
        'status_code': response.status_code,
        'execution_time': round(duration * 1000, 2),
        'ip': request.remote_addr
    })
    return response

@app.route('/users')
def get_users():
    try:
        logger.info("Fetching users list", extra={'request_id': request.request_id})
        users = [
            {"id": 1, "name": "Alice", "email": "alice@test.com"},
            {"id": 2, "name": "Bob", "email": "bob@test.com"}
        ]
        return jsonify({"users": users, "count": len(users)})
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", extra={'request_id': request.request_id})
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>')
def get_user(user_id):
    try:
        logger.info(f"Fetching user {user_id}", extra={
            'request_id': request.request_id, 
            'user_id': user_id
        })
        
        if user_id > 10:
            logger.warning(f"User {user_id} not found", extra={
                'request_id': request.request_id,
                'user_id': user_id
            })
            return jsonify({"error": "User not found"}), 404
            
        if user_id == 999:
            # Simulation d'erreur
            raise Exception("Database connection failed")
            
        return jsonify({"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@test.com"})
        
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}", extra={
            'request_id': request.request_id,
            'user_id': user_id
        })
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("API Service starting up")
    app.run(host='0.0.0.0', port=5000)
```

### Web Service Node.js avec Winston
Créez `services/web.js` :
```javascript
const express = require('express');
const winston = require('winston');
const LogstashTransport = require('winston-logstash').Logstash;

const app = express();
const port = 3000;

// Configuration Winston avec Logstash
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'web-service' },
  transports: [
    new LogstashTransport({
      port: 5000,
      node_name: 'web-service',
      host: 'logstash'
    }),
    new winston.transports.Console()
  ]
});

// Middleware de logging
app.use((req, res, next) => {
  const start = Date.now();
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  req.requestId = requestId;
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info('HTTP Request', {
      request_id: requestId,
      method: req.method,
      url: req.url,
      status_code: res.statusCode,
      execution_time: duration,
      user_agent: req.get('User-Agent'),
      ip: req.ip
    });
  });
  
  next();
});

app.get('/', (req, res) => {
  logger.info('Home page accessed', { request_id: req.requestId });
  res.json({
    message: 'Web Service is running',
    timestamp: new Date().toISOString(),
    service: 'web-service'
  });
});

app.get('/dashboard', (req, res) => {
  logger.info('Dashboard accessed', { request_id: req.requestId });
  
  // Simulation d'appel vers l'API
  setTimeout(() => {
    logger.info('Dashboard data loaded', { 
      request_id: req.requestId,
      data_source: 'api-service',
      load_time: 150
    });
  }, 150);
  
  res.json({
    dashboard: 'Main Dashboard',
    widgets: ['users', 'orders', 'analytics'],
    loaded_at: new Date().toISOString()
  });
});

app.get('/error-test', (req, res) => {
  logger.error('Simulated error occurred', {
    request_id: req.requestId,
    error_type: 'simulation',
    error_code: 'SIM_001'
  });
  res.status(500).json({ error: 'Simulated error for testing' });
});

app.listen(port, '0.0.0.0', () => {
  logger.info('Web service started', { port: port });
  console.log(`Web service running on port ${port}`);
});
```

---

## Phase 3 : Déploiement et Tests (5 min)

### Démarrage de la stack
```bash
# Démarrage des services
docker-compose up -d

# Vérification des services
docker-compose ps

# Attendre que Elasticsearch soit prêt (30-60 secondes)
curl http://localhost:9200/_cluster/health

# Test génération de logs
curl http://localhost:5001/users
curl http://localhost:3000/dashboard
curl http://localhost:5001/users/999  # Génère une erreur
curl http://localhost:3000/error-test # Génère une erreur
```

---

## Phase 4 : Kibana Dashboard et Alertes (5 min)

### Accès Kibana et configuration
1. **Ouvrir Kibana** : http://localhost:5601
2. **Créer l'index pattern** :
   - Aller dans "Stack Management" > "Index Patterns"
   - Créer pattern : `microservices-*`
   - Choisir `@timestamp` comme time field

### Dashboard rapide
3. **Créer un dashboard** :
   ```json
   // Visualisation 1: Logs par service (Pie chart)
   {
     "aggs": {
       "services": {
         "terms": {
           "field": "service.keyword",
           "size": 10
         }
       }
     }
   }
   
   // Visualisation 2: Erreurs dans le temps (Line chart)
   {
     "query": {
       "match": { "level": "ERROR" }
     },
     "aggs": {
       "errors_over_time": {
         "date_histogram": {
           "field": "@timestamp",
           "interval": "1m"
         }
       }
     }
   }
   
   // Visualisation 3: Top erreurs (Data table)
   {
     "query": {
       "match": { "level": "ERROR" }
     },
     "aggs": {
       "top_errors": {
         "terms": {
           "field": "message.keyword",
           "size": 5
         }
       }
     }
   }
   ```

### Configuration d'alertes simples
4. **Watcher/Alertes** (dans Stack Management) :
   ```json
   {
     "trigger": {
       "schedule": { "interval": "1m" }
     },
     "input": {
       "search": {
         "request": {
           "search_type": "query_then_fetch",
           "indices": ["microservices-*"],
           "body": {
             "query": {
               "bool": {
                 "must": [
                   { "match": { "level": "ERROR" } },
                   { "range": { "@timestamp": { "gte": "now-1m" } } }
                 ]
               }
             }
           }
         }
       }
     },
     "condition": {
       "compare": { "ctx.payload.hits.total": { "gt": 0 } }
     },
     "actions": {
       "log_error": {
         "logging": {
           "text": "ALERT: {{ctx.payload.hits.total}} errors detected in the last minute"
         }
       }
     }
   }
   ```

---

## Tests et Validation

### Commandes de test
```bash
# Génération de logs variés
for i in {1..10}; do
  curl http://localhost:5001/users
  curl http://localhost:3000/dashboard
  sleep 1
done

# Génération d'erreurs
curl http://localhost:5001/users/999
curl http://localhost:3000/error-test

# Vérification dans Elasticsearch
curl "http://localhost:9200/microservices-*/_search?q=level:ERROR&pretty"
```

### Points de vérification
✅ Les logs apparaissent dans Kibana  
✅ Les services sont identifiables  
✅ Les erreurs sont tracées  
✅ Le dashboard affiche les métriques  
✅ Les alertes se déclenchent sur erreurs  

### Questions d'évaluation
1. **Quels avantages apporte la centralisation des logs ?**
2. **Comment optimiser les performances d'Elasticsearch ?**
3. **Quelles métriques sont critiques à surveiller ?**
4. **Comment sécuriser la stack ELK en production ?**

---

## Extensions possibles (bonus)
- Ajout de Filebeat pour les logs de fichiers
- Configuration de retention des données
- Mise en place de rôles et sécurité
- Intégration avec Slack/Teams pour les alertes
