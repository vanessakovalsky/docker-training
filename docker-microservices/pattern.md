# Implémentation des patterns (60 min)

## Objectif
Implémenter les patterns Circuit Breaker et Health Check.

## Pattern Health Check
```javascript
// health.js
const express = require('express');
const router = express.Router();

let isHealthy = true;
let dependencies = {
    database: false,
    redis: false
};

router.get('/health', (req, res) => {
    if (isHealthy && dependencies.database && dependencies.redis) {
        res.status(200).json({
            status: 'healthy',
            timestamp: new Date().toISOString(),
            dependencies
        });
    } else {
        res.status(503).json({
            status: 'unhealthy',
            timestamp: new Date().toISOString(),
            dependencies
        });
    }
});

router.get('/ready', (req, res) => {
    // Readiness check
    res.status(200).json({ status: 'ready' });
});

module.exports = router;
```

## Pattern Circuit Breaker
```javascript
// circuit-breaker.js
class CircuitBreaker {
    constructor(threshold = 5, timeout = 60000) {
        this.threshold = threshold;
        this.timeout = timeout;
        this.failureCount = 0;
        this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
        this.nextAttempt = Date.now();
    }

    async call(fn) {
        if (this.state === 'OPEN') {
            if (Date.now() < this.nextAttempt) {
                throw new Error('Circuit breaker is OPEN');
            }
            this.state = 'HALF_OPEN';
        }

        try {
            const result = await fn();
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }

    onSuccess() {
        this.failureCount = 0;
        this.state = 'CLOSED';
    }

    onFailure() {
        this.failureCount++;
        if (this.failureCount >= this.threshold) {
            this.state = 'OPEN';
            this.nextAttempt = Date.now() + this.timeout;
        }
    }
}
```

## Questions de réflexion
1. Comment gérer la montée en charge ?
2. Quels sont les défis de la surveillance distribuée ?
3. Comment assurer la cohérence des données entre services ?
