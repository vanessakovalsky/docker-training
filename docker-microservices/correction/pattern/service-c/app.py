from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

# Simulation d'une base de données
database_status = {"healthy": True, "records": 1000}

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Simuler des pannes aléatoirement
    if random.random() < 0.2:  # 20% de chance de panne
        return jsonify({
            "status": "unhealthy",
            "message": "Database connection failed"
        }), 503
    
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "records": database_status["records"]
    })

@app.route('/data')
def get_data():
    """Endpoint de données"""
    if random.random() < 0.1:  # 10% de chance d'erreur
        return jsonify({"error": "Database error"}), 500
    
    # Simuler une latence
    time.sleep(random.uniform(0.1, 0.5))
    
    return jsonify({
        "data": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ],
        "timestamp": int(time.time())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)