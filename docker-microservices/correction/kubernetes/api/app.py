from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'timestamp': time.time()
    })

@app.route('/api/users')
def users():
    return jsonify({
        'users': [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ],
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('DEBUG', 'False') == 'True')