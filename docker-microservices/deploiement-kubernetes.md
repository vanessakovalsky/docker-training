# Déploiement multi-environnements

## Pré-requis
- Docker et Docker Compose installés
- Minikube installé et configuré : https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download
- kubectl installé : https://kubernetes.io/fr/docs/tasks/tools/install-kubectl/
- Un éditeur de code

### Objectifs pédagogiques
- Comprendre et utiliser docker-compose.override.yml pour différents environnements
- Déployer une application multi-services avec Minikube
- Gérer les configurations spécifiques à l'environnement de recette

## Partie 1 : Préparation de l'environnement (10 min)

### Prérequis


### Structure du projet
Créez la structure suivante :
```
microservices-app/
├── api/
│   ├── Dockerfile
│   └── app.py
├── web/
│   ├── Dockerfile
│   └── index.html
├── docker-compose.yml
├── docker-compose.override.yml
└── k8s/
    ├── api-deployment.yaml
    ├── web-deployment.yaml
    └── database-deployment.yaml
```

---

## Partie 2 : Création des services (15 min)

### Service API (Flask)
Créez `api/app.py` :
```python
from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'timestamp': time.time()
    })

@app.route('/api/users')
def users():
    return jsonify({
        'users': [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ],
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('DEBUG', 'False') == 'True')
```

Créez `api/Dockerfile` :
```dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN pip install flask
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Service Web (Frontend simple)
Créez `web/index.html` :
```html
<!DOCTYPE html>
<html>
<head>
    <title>Microservices App</title>
</head>
<body>
    <h1>Application Microservices</h1>
    <div id="users"></div>
    <script>
        fetch('/api/users')
            .then(response => response.json())
            .then(data => {
                document.getElementById('users').innerHTML = 
                    '<h2>Utilisateurs (' + data.environment + ')</h2>' +
                    data.users.map(u => '<p>' + u.name + '</p>').join('');
            });
    </script>
</body>
</html>
```

Créez `web/Dockerfile` :
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
```


## Partie 3 : Configuration Docker Compose (15 min)

### Fichier principal docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: ./api
    environment:
      - ENVIRONMENT=development
      - DEBUG=True
    ports:
      - "5000:5000"
    depends_on:
      - database

  web:
    build: ./web
    ports:
      - "8080:80"
    depends_on:
      - api

  database:
    image: postgres:13
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - web
      - api

volumes:
  postgres_data:
```

### Fichier docker-compose.override.yml (pour l'environnement de recette)
```yaml
version: '3.8'

services:
  api:
    environment:
      - ENVIRONMENT=staging
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@database:5432/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    restart: unless-stopped

  database:
    environment:
      - POSTGRES_DB=app_staging
      - POSTGRES_USER=staging_user
      - POSTGRES_PASSWORD=staging_secure_password
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U staging_user -d app_staging"]
      interval: 30s
      timeout: 10s
      retries: 5

  nginx:
    restart: unless-stopped
    volumes:
      - ./nginx-staging.conf:/etc/nginx/nginx.conf
```

### Configuration Nginx
Créez `nginx.conf` :
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:5000;
    }

    server {
        listen 80;
        
        location / {
            proxy_pass http://web:80;
        }
        
        location /api/ {
            proxy_pass http://api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### **Questions pratiques :**
1. **Testez la configuration :**
   ```bash
   docker-compose up -d
   ```
   Vérifiez que l'application fonctionne sur http://localhost

2. **Analysez les différences :**
   - Comparez les variables d'environnement entre les deux fichiers
   - Observez les healthchecks ajoutés dans override
   - Notez les politiques de restart

---

## Partie 4 : Déploiement sur Minikube (15 min)

### Démarrage de Minikube
```bash
minikube start --driver=docker
minikube addons enable ingress
```

### Déploiement API
Créez `k8s/api-deployment.yaml` :
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
  labels:
    app: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: microservices-app-api:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 5000
        env:
        - name: ENVIRONMENT
          value: "staging"
        - name: DEBUG
          value: "False"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api
  ports:
    - protocol: TCP
      port: 5000
      targetPort: 5000
  type: ClusterIP
```

### Déploiement Web
Créez `k8s/web-deployment.yaml` :
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: microservices-app-web:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
```

### Déploiement Base de données
Créez `k8s/database-deployment.yaml` :
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
    spec:
      containers:
      - name: database
        image: postgres:13
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "app_staging"
        - name: POSTGRES_USER
          value: "staging_user"
        - name: POSTGRES_PASSWORD
          value: "staging_secure_password"
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: database-service
spec:
  selector:
    app: database
  ports:
    - protocol: TCP
      port: 5432
      targetPort: 5432
  type: ClusterIP
```

---

## Partie 5 : Déploiement et tests (5 min)

### Construction et déploiement
```bash
# Configuration de Docker pour Minikube
eval $(minikube docker-env)

# Construction des images
docker build -t microservices-app-api:latest ./api
docker build -t microservices-app-web:latest ./web

# Déploiement sur Kubernetes
kubectl apply -f k8s/

# Vérification du déploiement
kubectl get pods
kubectl get services

# Exposition du service web
kubectl port-forward service/web-service 8080:80
```

### Tests et validation
```bash
# Test de l'API directement
kubectl port-forward service/api-service 5000:5000
curl http://localhost:5000/health

# Vérification des logs
kubectl logs -l app=api
kubectl logs -l app=web
```

---

## Questions d'évaluation

### Questions théoriques (à discuter en groupe) :
1. **Quels sont les avantages de docker-compose.override.yml par rapport à plusieurs fichiers docker-compose distincts ?**

2. **Comment les healthchecks impactent-ils le déploiement en production ?**

3. **Pourquoi utilise-t-on `imagePullPolicy: Never` dans Minikube ?**

### Exercices pratiques :
1. **Modifiez la configuration override pour ajouter un service Redis**
2. **Créez un Ingress pour exposer l'application via un nom de domaine**
3. **Implémentez un ConfigMap pour externaliser la configuration Nginx**

### Points de discussion :
- **Différences entre environnement de développement et de recette**
- **Stratégies de déploiement (rolling update, blue-green)**
- **Monitoring et observabilité des microservices**

---

## Solutions attendues

### Vérifications à effectuer :
✅ Les services démarrent correctement avec docker-compose  
✅ Les variables d'environnement diffèrent entre dev et staging  
✅ Les healthchecks fonctionnent  
✅ Le déploiement Kubernetes est opérationnel  
✅ Les services communiquent entre eux  
✅ Les ports sont correctement mappés  

### Livrables :
- Application fonctionnelle en local avec Docker Compose
- Déploiement réussi sur Minikube
- Documentation des différences entre environnements
- Plan d'amélioration pour la mise en production

---

## Extensions possibles (bonus)
- Ajout de tests d'intégration avec docker-compose.test.yml
- Implémentation de secrets Kubernetes
- Configuration d'un monitoring avec Prometheus
- Mise en place d'un CI/CD pipeline
