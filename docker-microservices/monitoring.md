# Stack de monitoring complète

## Objectif

- Déployer Prometheus, Grafana et instrumenter des microservices

## Structure du projet
```
monitoring/
├── docker-compose.yml
├── prometheus.yml
├── grafana/
│   └── dashboards/
└── apps/
    ├── user-service/
    └── order-service/
```

## Consignes

1. Déployer la stack de monitoring
2. Instrumenter deux microservices
3. Créer des dashboards Grafana
4. Configurer des alertes

```javascript
// user-service/app.js
const express = require('express');
const client = require('prom-client');

const app = express();

// Métriques
const register = new client.Registry();
client.collectDefaultMetrics({ register });

const httpDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.1, 0.5, 1, 2, 5]
});

register.registerMetric(httpDuration);

// Middleware de métriques
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    httpDuration
      .labels(req.method, req.route?.path || req.url, res.statusCode)
      .observe(duration);
  });
  next();
});

// Routes
app.get('/users', (req, res) => {
  setTimeout(() => {
    res.json([{ id: 1, name: 'John' }, { id: 2, name: 'Jane' }]);
  }, Math.random() * 100);
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

app.listen(3001);
```
