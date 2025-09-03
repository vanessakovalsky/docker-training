const express = require('express');
const winston = require('winston');
const net = require('net');

const app = express();
const port = 3000;

// Transport TCP personnalisé pour Logstash
class CustomLogstashTransport extends winston.Transport {
    constructor(options) {
        super(options);
        this.host = options.host || 'localhost';
        this.port = options.port || 5000;
    }

    log(info, callback) {
        const logEntry = {
            '@timestamp': new Date().toISOString(),
            ...info
        };
        
        const logData = JSON.stringify(logEntry) + '\n';
        
        const client = new net.Socket();
        client.setTimeout(5000); // Timeout de 5 secondes
        
        client.connect(this.port, this.host, () => {
            client.write(logData);
            client.end();
        });

        client.on('error', (err) => {
            console.error(`Logstash connection error (${this.host}:${this.port}):`, err.message);
            if (callback) callback();
        });

        client.on('timeout', () => {
            console.error(`Logstash connection timeout (${this.host}:${this.port})`);
            client.destroy();
            if (callback) callback();
        });

        client.on('close', () => {
            if (callback) callback();
        });
    }
}

// Configuration Winston avec Logstash
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    defaultMeta: { service: 'web-service' },
    transports: [
        new CustomLogstashTransport({
            host: 'logstash',
            port: 5000
        }),
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.colorize(),
                winston.format.simple()
            )
        })
    ]
});

// Middleware pour parser JSON
app.use(express.json());

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
            ip: req.ip || req.connection.remoteAddress
        });
    });
    
    next();
});

// Gestion d'erreur pour le logger
logger.on('error', (err) => {
    console.error('Logger error:', err);
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

// Middleware de gestion d'erreur global
app.use((err, req, res, next) => {
    logger.error('Unhandled error', {
        request_id: req.requestId,
        error: err.message,
        stack: err.stack
    });
    res.status(500).json({ error: 'Internal server error' });
});

app.listen(port, '0.0.0.0', () => {
    logger.info('Web service started', { port: port });
    console.log(`Web service running on port ${port}`);
});