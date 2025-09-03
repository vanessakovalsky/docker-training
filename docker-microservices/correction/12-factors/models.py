# models.py - Modèles de données
from dataclasses import dataclass, asdict
from typing import Optional
import json

@dataclass
class User:
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    created_at: Optional[str] = None
    
    def to_dict(self):
        """Convertir l'objet User en dictionnaire"""
        return asdict(self)
    
    def to_json(self):
        """Convertir l'objet User en JSON"""
        return json.dumps(self.to_dict(), default=str)
    
    def __str__(self):
        return f"User(id={self.id}, username='{self.name}', email='{self.email}')"
    
    def __repr__(self):
        return self.__str__()