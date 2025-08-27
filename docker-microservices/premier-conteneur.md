## Pré-requis

* Avoir docker installé et démarrer sur sa machine

## Objectif
Créer et déployer une application Node.js simple dans un conteneur Docker.

## Étapes
1. **Créer l'application Node.js**
```javascript
// app.js
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.json({
        message: 'Hello from Docker!',
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'development'
    });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

2. **Créer le package.json**
```json
{
  "name": "docker-microservice-demo",
  "version": "1.0.0",
  "main": "app.js",
  "scripts": {
    "start": "node app.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
```

3. **Créer le Dockerfile**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
USER node
CMD ["npm", "start"]
```

4. **Commandes à exécuter**
```bash
# Construire l'image
docker build -t my-microservice .

# Lancer le conteneur
docker run -p 3000:3000 my-microservice

# Tester l'application
curl http://localhost:3000
```

### Questions
- Que se passe-t-il si vous modifiez le code sans reconstruire l'image ?
- Comment optimiser la taille de l'image ?
