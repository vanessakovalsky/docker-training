from flask import Flask, jsonify
import requests
import time
from datetime import datetime

app = Flask(__name__)

SERVICE_C_URL = "http://service-c:5000"

@app.route('/health')
def health_check():
    """Health check complet incluant les dépendances"""
    health_status = {
        "service": "api-gateway",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {}
    }
    
    try:
        # Vérifier la santé du service C
        response = requests.get(f"{SERVICE_C_URL}/health", timeout=2)
        if response.status_code == 200:
            health_status["dependencies"]["service-c"] = "healthy"
        else:
            health_status["dependencies"]["service-c"] = "unhealthy"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["service-c"] = f"unreachable: {str(e)}"
        health_status["status"] = "unhealthy"
        return jsonify(health_status), 503
    
    return jsonify(health_status)

@app.route('/api/data')
def proxy_data():
    """Proxy vers le service C"""
    try:
        response = requests.get(f"{SERVICE_C_URL}/data", timeout=3)
        return response.json(), response.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "Service timeout"}), 504
    except Exception as e:
        return jsonify({"error": f"Service unavailable: {str(e)}"}), 503

@app.route('/ready')
def readiness_check():
    """Readiness probe - vérifie si le service est prêt à recevoir du trafic"""
    try:
        # Test de connectivité vers les services critiques
        response = requests.get(f"{SERVICE_C_URL}/health", timeout=1)
        if response.status_code == 200:
            return jsonify({"status": "ready"}), 200
        else:
            return jsonify({"status": "not ready", "reason": "dependency unhealthy"}), 503
    except:
        return jsonify({"status": "not ready", "reason": "dependency unreachable"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)