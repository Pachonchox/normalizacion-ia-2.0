#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor centralizado de configuración
Securiza credenciales usando variables de entorno
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

@dataclass
class DatabaseConfig:
    """Configuración segura de base de datos"""
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 5
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Cargar configuración desde variables de entorno"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            pool_size=int(os.getenv('DB_POOL_SIZE', '5'))
        )

@dataclass 
class OpenAIConfig:
    """Configuración segura de OpenAI"""
    api_key: str
    enabled: bool = True
    model: str = "gpt-4o-mini"
    
    @classmethod
    def from_env(cls) -> 'OpenAIConfig':
        """Cargar configuración desde variables de entorno"""
        return cls(
            api_key=os.getenv('OPENAI_API_KEY', ''),
            enabled=os.getenv('LLM_ENABLED', 'true').lower() == 'true',
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        )

class ConfigManager:
    """Gestor centralizado y seguro de configuración"""
    
    def __init__(self):
        self._db_config: Optional[DatabaseConfig] = None
        self._openai_config: Optional[OpenAIConfig] = None
    
    @property
    def database(self) -> DatabaseConfig:
        """Obtener configuración de base de datos"""
        if self._db_config is None:
            self._db_config = DatabaseConfig.from_env()
            self._validate_db_config()
        return self._db_config
    
    @property
    def openai(self) -> OpenAIConfig:
        """Obtener configuración de OpenAI"""
        if self._openai_config is None:
            self._openai_config = OpenAIConfig.from_env()
            self._validate_openai_config()
        return self._openai_config
    
    def _validate_db_config(self):
        """Validar configuración de BD"""
        if not self._db_config.host:
            raise ValueError("DB_HOST no está configurado")
        if not self._db_config.password:
            raise ValueError("DB_PASSWORD no está configurado")
        if not self._db_config.user:
            raise ValueError("DB_USER no está configurado")
    
    def _validate_openai_config(self):
        """Validar configuración de OpenAI"""
        if self._openai_config.enabled and not self._openai_config.api_key:
            raise ValueError("OPENAI_API_KEY no está configurado pero LLM_ENABLED=true")
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Obtener parámetros de conexión para psycopg2"""
        db = self.database
        return {
            'host': db.host,
            'port': db.port,
            'database': db.database,
            'user': db.user,
            'password': db.password
        }

# Instancia singleton
_config_manager: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """Obtener instancia singleton del gestor de configuración"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager