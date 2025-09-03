import json
import logging.handlers
import socket
import time
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuration logging vers Logstash
class LogstashFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "api-service",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, 'request_id', None),
            "user_id": getattr(record, 'user_id', None),
            "execution_time": getattr(record, 'execution_time', None)
        }
        return json.dumps(log_entry)

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler vers Logstash
logstash_handler = logging.handlers.SocketHandler('logstash', 5000)
logstash_handler.setFormatter(LogstashFormatter())
logger.addHandler(logstash_handler)

@app.before_request
def before_request():
    request.start_time = time.time()
    request.request_id = f"req_{int(time.time() * 1000)}"

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    logger.info("HTTP Request", extra={
        'request_id': request.request_id,
        'method': request.method,
        'url': request.url,
        'status_code': response.status_code,
        'execution_time': round(duration * 1000, 2),
        'ip': request.remote_addr
    })
    return response

@app.route('/users')
def get_users():
    try:
        logger.info("Fetching users list", extra={'request_id': request.request_id})
        users = [
            {"id": 1, "name": "Alice", "email": "alice@test.com"},
            {"id": 2, "name": "Bob", "email": "bob@test.com"}
        ]
        return jsonify({"users": users, "count": len(users)})
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", extra={'request_id': request.request_id})
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>')
def get_user(user_id):
    try:
        logger.info(f"Fetching user {user_id}", extra={
            'request_id': request.request_id, 
            'user_id': user_id
        })
        
        if user_id > 10:
            logger.warning(f"User {user_id} not found", extra={
                'request_id': request.request_id,
                'user_id': user_id
            })
            return jsonify({"error": "User not found"}), 404
            
        if user_id == 999:
            # Simulation d'erreur
            raise Exception("Database connection failed")
            
        return jsonify({"id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@test.com"})
        
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}", extra={
            'request_id': request.request_id,
            'user_id': user_id
        })
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("API Service starting up")
    app.run(host='0.0.0.0', port=5000)