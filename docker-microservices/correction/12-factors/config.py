# config.py - Configuration centralisée
import os
from dataclasses import dataclass

@dataclass
class Config:
    # Database
    DATABASE_URL: str = os.environ.get(
        'DATABASE_URL', 
        'postgresql://user:password@localhost:5432/userdb'
    )
    
    # Server
    PORT: int = int(os.environ.get('PORT', 8080))
    HOST: str = os.environ.get('HOST', '0.0.0.0')
    
    # Logging
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.environ.get(
        'LOG_FORMAT', 
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # App
    FLASK_ENV: str = os.environ.get('FLASK_ENV', 'production')
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-change-me')