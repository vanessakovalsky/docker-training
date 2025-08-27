# Distributed Tracing avec Jaeger

**Objectif** : Tracer les appels entre microservices

**Architecture** :
- API Gateway → User Service → Database
- API Gateway → Order Service → User Service

**Instructions** :
1. Déployer Jaeger
2. Instrumenter les microservices avec OpenTracing
3. Créer des appels de service à service
4. Analyser les traces

```javascript
// api-gateway/app.js
const express = require('express');
const axios = require('axios');
const { initTracer, tracingMiddleware } = require('./tracing');

const app = express();
const tracer = initTracer('api-gateway');

app.use(tracingMiddleware);

app.get('/api/user/:id', async (req, res) => {
  const span = req.span;
  
  try {
    // Appel au user-service avec propagation du contexte
    const headers = {};
    tracer.inject(span, 'http_headers', headers);
    
    const response = await axios.get(
      `http://user-service:3001/users/${req.params.id}`,
      { headers }
    );
    
    res.json(response.data);
  } catch (error) {
    span.setTag('error', true);
    span.log({ event: 'error', message: error.message });
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000);
```
