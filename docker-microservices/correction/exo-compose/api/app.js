// api/app.js
const express = require('express');
const redis = require('redis');
const { Pool } = require('pg');

const app = express();
app.use(express.json());

const redisClient = redis.createClient({
    socket: {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379
    }
});

// Gestion des erreurs Redis
redisClient.on('error', (err) => {
    console.error('Erreur Redis:', err);
});

redisClient.on('connect', () => {
    console.log('Connecté à Redis');
});

// Connexion à Redis (obligatoire avec redis v4+)
redisClient.connect().catch(console.error);

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
    await redisClient.set(`user:${userId}`, 300, JSON.stringify(user));
    
    res.json({ source: 'database', data: user });
});

app.listen(3000);