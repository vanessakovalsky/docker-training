# database.py - Gestionnaire de base de données corrigé
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import logging
from typing import List, Optional
from models import User
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config: Config):
        self.config = config
        self.pool = None
        self._init_pool()
    
    def _init_pool(self):
        try:
            logger.info(f"Initializing connection pool to: {self.config.DATABASE_URL.split('@')[1] if '@' in self.config.DATABASE_URL else 'localhost'}")
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 20, self.config.DATABASE_URL
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def get_connection(self):
        if not self.pool:
            raise Exception("Database pool not initialized")
        return self.pool.getconn()
    
    def return_connection(self, conn):
        if self.pool:
            self.pool.putconn(conn)
    
    def init_tables(self):
        """Initialiser les tables de la base de données"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Créer un index sur name et email pour les recherches
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                """)
                
            conn.commit()
            logger.info("Database tables and indexes initialized successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize tables: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def create_user(self, user: User) -> User:
        """Créer un nouvel utilisateur"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO users (name, email)
                    VALUES (%s, %s)
                    RETURNING id, name, email, 
                             created_at AT TIME ZONE 'UTC' as created_at
                """, (user.name, user.email))
                
                result = cursor.fetchone()
                conn.commit()
                
                created_user = User(
                    id=result['id'],
                    name=result['name'],
                    email=result['email'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None
                )
                
                logger.info(f"User created successfully: {created_user.name} (ID: {created_user.id})")
                return created_user
                
        except psycopg2.IntegrityError as e:
            conn.rollback()
            logger.warning(f"User creation failed - integrity constraint: {e}")
            raise Exception(f"name or email already exists: {e}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_users(self) -> List[User]:
        """Récupérer tous les utilisateurs"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, email, 
                           created_at AT TIME ZONE 'UTC' as created_at
                    FROM users 
                    ORDER BY created_at DESC
                """)
                results = cursor.fetchall()
                
                users = []
                for row in results:
                    user = User(
                        id=row['id'],
                        name=row['name'],
                        email=row['email'],
                        created_at=row['created_at'].isoformat() if row['created_at'] else None
                    )
                    users.append(user)
                
                logger.info(f"Retrieved {len(users)} users from database")
                return users
                
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupérer un utilisateur par son ID"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, email, 
                           created_at AT TIME ZONE 'UTC' as created_at
                    FROM users 
                    WHERE id = %s
                """, (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return User(
                    id=result['id'],
                    name=result['name'],
                    email=result['email'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None
                )
                
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def update_user(self, user_id: int, user: User) -> Optional[User]:
        """Mettre à jour un utilisateur"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET name = %s, email = %s
                    WHERE id = %s
                    RETURNING id, name, email, 
                             created_at AT TIME ZONE 'UTC' as created_at
                """, (user.name, user.email, user_id))
                
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                conn.commit()
                
                updated_user = User(
                    id=result['id'],
                    name=result['name'],
                    email=result['email'],
                    created_at=result['created_at'].isoformat() if result['created_at'] else None
                )
                
                logger.info(f"User updated successfully: {updated_user.name} (ID: {updated_user.id})")
                return updated_user
                
        except psycopg2.IntegrityError as e:
            conn.rollback()
            logger.warning(f"User update failed - integrity constraint: {e}")
            raise Exception(f"name or email already exists: {e}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def delete_user(self, user_id: int) -> bool:
        """Supprimer un utilisateur"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                deleted = cursor.rowcount > 0
                
            conn.commit()
            
            if deleted:
                logger.info(f"User deleted successfully: ID {user_id}")
            else:
                logger.warning(f"No user found with ID {user_id} for deletion")
                
            return deleted
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def health_check(self) -> bool:
        """Vérifier la santé de la connexion à la base de données"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            self.return_connection(conn)
            
            is_healthy = result is not None
            if is_healthy:
                logger.debug("Database health check passed")
            else:
                logger.warning("Database health check failed")
            return is_healthy
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_user_count(self) -> int:
        """Obtenir le nombre total d'utilisateurs"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                logger.info(f"Total users in database: {count}")
                return count
        except Exception as e:
            logger.error(f"Failed to get user count: {e}")
            return 0
        finally:
            self.return_connection(conn)
    
    def close_all_connections(self):
        """Fermer toutes les connexions du pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("All database connections closed")