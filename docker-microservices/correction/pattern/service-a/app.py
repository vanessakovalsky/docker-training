from flask import Flask, jsonify, render_template_string
import requests
import time
from enum import Enum
from threading import Lock
from datetime import datetime, timedelta

app = Flask(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Tout fonctionne normalement
    OPEN = "open"          # Circuit ouvert, pas d'appels
    HALF_OPEN = "half_open"  # Test de récupération

class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=10, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # Timeout pour les requêtes
        self.recovery_timeout = recovery_timeout  # Temps avant de tester la récupération
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = Lock()
    
    def call(self, func, *args, **kwargs):
        """Exécute une fonction à travers le circuit breaker"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self):
        """Vérifie s'il faut tenter une récupération"""
        if self.last_failure_time is None:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Appelé en cas de succès"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Appelé en cas d'échec"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Instance globale du circuit breaker
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=20)

SERVICE_B_URL = "http://service-b:5001"

def call_service_b(endpoint):
    """Fonction pour appeler le service B"""
    response = requests.get(f"{SERVICE_B_URL}{endpoint}", timeout=circuit_breaker.timeout)
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")
    return response.json()

@app.route('/')
def dashboard():
    """Dashboard avec état du circuit breaker"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Circuit Breaker Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body { font-family: Arial; margin: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .closed { background-color: #d4edda; color: #155724; }
            .open { background-color: #f8d7da; color: #721c24; }
            .half-open { background-color: #fff3cd; color: #856404; }
            .error { background-color: #f8d7da; color: #721c24; margin-top: 10px; }
            button { padding: 10px; margin: 5px; font-size: 16px; }
        </style>
    </head>
    <body>
        <h1>Microservices Dashboard</h1>
        
        <div class="status {{ state_class }}">
            <strong>Circuit Breaker État:</strong> {{ circuit_state }}<br>
            <strong>Échecs consécutifs:</strong> {{ failure_count }}/{{ failure_threshold }}<br>
            <strong>Dernière mise à jour:</strong> {{ timestamp }}
        </div>
        
        <button onclick="location.href='/test-api'">Tester API</button>
        <button onclick="location.href='/health-status'">Vérifier Santé</button>
        <button onclick="location.reload()">Actualiser</button>
        
        {% if error %}
        <div class="error">
            <strong>Erreur:</strong> {{ error }}
        </div>
        {% endif %}
        
        {% if data %}
        <div style="margin-top: 20px;">
            <strong>Données reçues:</strong>
            <pre>{{ data }}</pre>
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    return render_template_string(html,
        circuit_state=circuit_breaker.state.value.upper(),
        state_class=circuit_breaker.state.value.replace('_', '-'),
        failure_count=circuit_breaker.failure_count,
        failure_threshold=circuit_breaker.failure_threshold,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/test-api')
def test_api():
    """Test de l'API à travers le circuit breaker"""
    try:
        data = circuit_breaker.call(call_service_b, '/api/data')
        return dashboard_with_data(data=data)
    except Exception as e:
        return dashboard_with_data(error=str(e))

@app.route('/health-status')
def health_status():
    """Vérification de l'état de santé"""
    try:
        health_data = circuit_breaker.call(call_service_b, '/health')
        return dashboard_with_data(data=health_data)
    except Exception as e:
        return dashboard_with_data(error=str(e))

def dashboard_with_data(data=None, error=None):
    """Dashboard avec données ou erreur"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Circuit Breaker Dashboard</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .closed { background-color: #d4edda; color: #155724; }
            .open { background-color: #f8d7da; color: #721c24; }
            .half-open { background-color: #fff3cd; color: #856404; }
            .error { background-color: #f8d7da; color: #721c24; margin-top: 10px; }
            .success { background-color: #d4edda; color: #155724; margin-top: 10px; }
            button { padding: 10px; margin: 5px; font-size: 16px; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Microservices Dashboard</h1>
        
        <div class="status {{ state_class }}">
            <strong>Circuit Breaker État:</strong> {{ circuit_state }}<br>
            <strong>Échecs consécutifs:</strong> {{ failure_count }}/{{ failure_threshold }}<br>
            <strong>Dernière mise à jour:</strong> {{ timestamp }}
        </div>
        
        <button onclick="location.href='/'">Retour</button>
        <button onclick="location.href='/test-api'">Tester API</button>
        <button onclick="location.href='/health-status'">Vérifier Santé</button>
        
        {% if error %}
        <div class="error">
            <strong>Erreur:</strong> {{ error }}
        </div>
        {% endif %}
        
        {% if data %}
        <div class="success">
            <strong>Succès! Données reçues:</strong>
            <pre>{{ data }}</pre>
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    import json
    return render_template_string(html,
        circuit_state=circuit_breaker.state.value.upper(),
        state_class=circuit_breaker.state.value.replace('_', '-'),
        failure_count=circuit_breaker.failure_count,
        failure_threshold=circuit_breaker.failure_threshold,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        data=json.dumps(data, indent=2) if data else None,
        error=error
    )

@app.route('/health')
def health():
    """Health check du frontend"""
    return jsonify({
        "service": "frontend",
        "status": "healthy",
        "circuit_breaker": {
            "state": circuit_breaker.state.value,
            "failures": circuit_breaker.failure_count
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)