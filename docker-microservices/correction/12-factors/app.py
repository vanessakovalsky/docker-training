# app.py - Version utilisant database.py
import os
import sys
import logging
import signal
from flask import Flask, jsonify, request
from config import Config
from database import DatabaseManager
from models import User

# Configuration du logging
config = Config()
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format=config.LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Initialisation de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Initialisation de la base de données
logger.info(f"Initializing database with URL: {config.DATABASE_URL}")
db_manager = DatabaseManager(config)

# Initialisation au démarrage de l'application
def initialize_app():
    """Initialiser l'application au démarrage"""
    logger.info("Initializing application...")
    try:
        db_manager.init_tables()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

# Gestion gracieuse de l'arrêt
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        db_healthy = db_manager.health_check()
        status = "healthy" if db_healthy else "unhealthy"
        status_code = 200 if db_healthy else 503
        
        return jsonify({
            "status": status,
            "database": "connected" if db_healthy else "disconnected",
            "version": "1.0.0",
            "database_url": config.DATABASE_URL.split('@')[1] if '@' in config.DATABASE_URL else config.DATABASE_URL
        }), status_code
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/users', methods=['GET'])
def get_users():
    """Récupérer tous les utilisateurs"""
    try:
        logger.info("Getting all users from database")
        users = db_manager.get_users()
        logger.info(f"Retrieved {len(users)} users from database")
        return jsonify({
            "users": [user.to_dict() for user in users],
            "count": len(users)
        })
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users', methods=['POST'])
def create_user():
    """Créer un nouvel utilisateur"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('email'):
            return jsonify({"error": "name and email are required"}), 400
        
        logger.info(f"Creating user: {data['name']}")
        user = User(name=data['name'], email=data['email'])
        created_user = db_manager.create_user(user)
        
        logger.info(f"Created user: {created_user.name} with ID: {created_user.id}")
        return jsonify(created_user.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        # Vérifier si c'est une erreur de contrainte d'unicité
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            return jsonify({"error": "name or email already exists"}), 409
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Récupérer un utilisateur par ID"""
    try:
        logger.info(f"Getting user with ID: {user_id}")
        user = db_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('email'):
            return jsonify({"error": "name and email are required"}), 400
        
        logger.info(f"Updating user with ID: {user_id}")
        user = User(name=data['name'], email=data['email'])
        updated_user = db_manager.update_user(user_id, user)
        
        if not updated_user:
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"Updated user: {updated_user.name}")
        return jsonify(updated_user.to_dict())
        
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        # Vérifier si c'est une erreur de contrainte d'unicité
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            return jsonify({"error": "name or email already exists"}), 409
        return jsonify({"error": "Internal server error"}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Supprimer un utilisateur"""
    try:
        logger.info(f"Deleting user with ID: {user_id}")
        deleted = db_manager.delete_user(user_id)
        
        if not deleted:
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"Deleted user with ID: {user_id}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Route de debug pour vérifier la configuration
@app.route('/debug/info', methods=['GET'])
def debug_info():
    """Informations de debug sur l'application"""
    return jsonify({
        "database_url": config.DATABASE_URL.split('@')[1] if '@' in config.DATABASE_URL else "Not configured",
        "log_level": config.LOG_LEVEL,
        "port": config.PORT,
        "host": config.HOST,
        "flask_env": config.FLASK_ENV
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialiser l'application
    try:
        initialize_app()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    logger.info(f"Database: {config.DATABASE_URL.split('@')[1] if '@' in config.DATABASE_URL else 'Not configured'}")
    app.run(host=config.HOST, port=config.PORT, debug=(config.FLASK_ENV == 'development'))