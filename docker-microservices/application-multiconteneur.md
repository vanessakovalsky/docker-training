# Application multi-conteneurs
### Objectif
Créer une architecture microservices avec Docker Compose.

### Architecture cible
```
Web App ←→ Redis Cache ←→ PostgreSQL
```

### Étapes
1. **Service Web (API)**
```javascript
// api/app.js
const express = require('express');
const redis = require('redis');
const { Pool } = require('pg');

const app = express();
app.use(express.json());

const redisClient = redis.createClient({
    host: process.env.REDIS_HOST || 'localhost'
});

const pool = new Pool({
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
});

app.get('/users/:id', async (req, res) => {
    const userId = req.params.id;
    
    // Check cache first
    const cached = await redisClient.get(`user:${userId}`);
    if (cached) {
        return res.json({ source: 'cache', data: JSON.parse(cached) });
    }
    
    // Query database
    const result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
    const user = result.rows[0];
    
    // Cache result
    await redisClient.setex(`user:${userId}`, 300, JSON.stringify(user));
    
    res.json({ source: 'database', data: user });
});

app.listen(3000);
```

2. **Docker Compose**
```yaml
version: '3.8'
services:
  web:
    build: ./api
    ports:
      - "3000:3000"
    environment:
      - REDIS_HOST=redis
      - DB_HOST=postgres
      - DB_NAME=myapp
      - DB_USER=user
      - DB_PASSWORD=password
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  postgres_data:
```

3. **Script d'initialisation de la base**
```sql
-- init.sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (name, email) VALUES
('Alice', 'alice@example.com'),
('Bob', 'bob@example.com'),
('Charlie', 'charlie@example.com');
```

### Commandes
```bash
# Démarrer tous les services
docker-compose up --build

# Tester l'API
curl http://localhost:3000/users/1

# Vérifier les logs
docker-compose logs web
```
