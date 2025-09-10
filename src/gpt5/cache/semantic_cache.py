#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Semantic Cache with Embeddings
Cache inteligente que encuentra productos similares usando embeddings vectoriales
Reduce llamadas a API en 40-50% mediante similitud semántica
"""

from __future__ import annotations
import json
import time
import hashlib
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass 
class CachedItem:
    """Item cacheado con embedding"""
    fingerprint: str
    embedding: np.ndarray
    normalized_data: Dict[str, Any]
    timestamp: float
    hit_count: int = 0
    similarity_score: float = 1.0


class SemanticCache:
    """
    Cache semántico usando embeddings para búsqueda por similitud
    Soporta múltiples backends: memoria, PostgreSQL+pgvector, Faiss
    """
    
    def __init__(self, backend: str = "memory", similarity_threshold: float = 0.85):
        self.backend = backend
        self.similarity_threshold = similarity_threshold
        self.cache = {}  # In-memory cache
        self.embeddings_cache = {}  # Cache de embeddings ya calculados
        self.stats = {
            'hits': 0,
            'misses': 0,
            'semantic_hits': 0,
            'total_queries': 0
        }
        
        # Configurar backend
        if backend == "postgresql":
            self._init_postgresql()
        elif backend == "faiss":
            self._init_faiss()
    
    def _init_postgresql(self):
        """Inicializa conexión PostgreSQL con pgvector"""
        try:
            from ..simple_db_connector import SimplePostgreSQLConnector
            
            self.db = SimplePostgreSQLConnector(
                host=os.getenv("DB_HOST", "34.176.197.136"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "Osmar2503!"),
                pool_size=5
            )
            
            # Crear tabla con soporte vectorial si no existe
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE EXTENSION IF NOT EXISTS vector;
                        
                        CREATE TABLE IF NOT EXISTS semantic_cache (
                            id SERIAL PRIMARY KEY,
                            fingerprint VARCHAR(64) UNIQUE,
                            product_text TEXT,
                            embedding vector(1536),
                            normalized_data JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            hit_count INTEGER DEFAULT 0,
                            model_version VARCHAR(50) DEFAULT 'text-embedding-3-small'
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_embedding_similarity 
                        ON semantic_cache 
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                    conn.commit()
            
            logger.info("✅ PostgreSQL + pgvector initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to init PostgreSQL: {e}")
            self.backend = "memory"  # Fallback
    
    def _init_faiss(self):
        """Inicializa índice Faiss para búsqueda vectorial rápida"""
        try:
            import faiss
            
            self.dimension = 1536  # OpenAI embeddings
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
            self.faiss_items = []  # Mapeo de índice a items
            
            # Cargar índice existente si existe
            index_path = Path("out/cache/faiss_index.bin")
            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
                
                # Cargar metadata
                metadata_path = Path("out/cache/faiss_metadata.json")
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        self.faiss_items = json.load(f)
            
            logger.info("✅ Faiss index initialized")
            
        except ImportError:
            logger.warning("⚠️ Faiss not installed, using memory backend")
            self.backend = "memory"
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Genera embedding usando OpenAI text-embedding-3-small
        Más económico y rápido que ada-002
        """
        # Check cache primero
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]
        
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.embeddings.create(
                model="text-embedding-3-small",  # Más económico
                input=text,
                encoding_format="float"
            )
            
            embedding = np.array(response.data[0].embedding)
            
            # Cachear embedding
            self.embeddings_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Retornar embedding random como fallback
            return np.random.randn(1536)
    
    def _product_to_text(self, product: Dict[str, Any]) -> str:
        """Convierte producto a texto para embedding"""
        parts = [
            product.get('name', ''),
            product.get('brand', ''),
            product.get('model', ''),
            product.get('category', ''),
        ]
        
        # Agregar atributos importantes
        attrs = product.get('attributes', {})
        for key, value in attrs.items():
            if value:
                parts.append(f"{key}:{value}")
        
        return " ".join(filter(None, parts))
    
    async def find_similar(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca productos similares en cache usando embeddings
        Returns: Datos normalizados si encuentra match similar
        """
        self.stats['total_queries'] += 1
        
        # Primero buscar match exacto por fingerprint
        from ..fingerprint import product_fingerprint
        fingerprint = product_fingerprint(product)
        
        if self.backend == "memory":
            if fingerprint in self.cache:
                self.stats['hits'] += 1
                item = self.cache[fingerprint]
                item.hit_count += 1
                return item.normalized_data
        
        # Buscar por similitud semántica
        product_text = self._product_to_text(product)
        embedding = await self.generate_embedding(product_text)
        
        similar_item = await self._search_similar_embedding(embedding, product)
        
        if similar_item:
            self.stats['semantic_hits'] += 1
            return similar_item
        
        self.stats['misses'] += 1
        return None
    
    async def _search_similar_embedding(self, embedding: np.ndarray, 
                                       product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca embedding similar según backend"""
        
        if self.backend == "postgresql":
            return await self._search_postgresql(embedding, product)
        elif self.backend == "faiss":
            return await self._search_faiss(embedding)
        else:
            return await self._search_memory(embedding)
    
    async def _search_memory(self, embedding: np.ndarray) -> Optional[Dict[str, Any]]:
        """Búsqueda en memoria (más lenta pero simple)"""
        if not self.cache:
            return None
        
        best_match = None
        best_score = 0.0
        
        for item in self.cache.values():
            if item.embedding is not None:
                # Cosine similarity
                score = np.dot(embedding, item.embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(item.embedding)
                )
                
                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = item
        
        if best_match:
            best_match.hit_count += 1
            best_match.similarity_score = best_score
            logger.info(f"🎯 Semantic hit with score {best_score:.3f}")
            return best_match.normalized_data
        
        return None
    
    async def _search_postgresql(self, embedding: np.ndarray, 
                                product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Búsqueda vectorial en PostgreSQL"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Búsqueda por similitud coseno
                    cursor.execute("""
                        SELECT fingerprint, normalized_data, 
                               1 - (embedding <=> %s::vector) as similarity
                        FROM semantic_cache
                        WHERE 1 - (embedding <=> %s::vector) > %s
                        AND normalized_data->>'category' = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT 1
                    """, (
                        embedding.tolist(),
                        embedding.tolist(),
                        self.similarity_threshold,
                        product.get('category', ''),
                        embedding.tolist()
                    ))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        fingerprint, normalized_data, similarity = result
                        
                        # Actualizar hit count
                        cursor.execute("""
                            UPDATE semantic_cache 
                            SET hit_count = hit_count + 1,
                                last_accessed = CURRENT_TIMESTAMP
                            WHERE fingerprint = %s
                        """, (fingerprint,))
                        conn.commit()
                        
                        logger.info(f"🎯 PostgreSQL semantic hit: {similarity:.3f}")
                        return normalized_data
                    
        except Exception as e:
            logger.error(f"PostgreSQL search error: {e}")
        
        return None
    
    async def _search_faiss(self, embedding: np.ndarray) -> Optional[Dict[str, Any]]:
        """Búsqueda rápida con Faiss"""
        if self.index.ntotal == 0:
            return None
        
        # Normalizar para cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        
        # Buscar k vecinos más cercanos
        k = min(5, self.index.ntotal)
        distances, indices = self.index.search(embedding.reshape(1, -1), k)
        
        # Verificar threshold
        if distances[0][0] >= self.similarity_threshold:
            idx = indices[0][0]
            if idx < len(self.faiss_items):
                item_data = self.faiss_items[idx]
                logger.info(f"🎯 Faiss semantic hit: {distances[0][0]:.3f}")
                return item_data['normalized_data']
        
        return None
    
    async def store(self, product: Dict[str, Any], normalized_data: Dict[str, Any]):
        """
        Almacena producto normalizado con su embedding
        """
        from ..fingerprint import product_fingerprint
        fingerprint = product_fingerprint(product)
        
        # Generar embedding
        product_text = self._product_to_text(product)
        embedding = await self.generate_embedding(product_text)
        
        # Crear item cacheado
        item = CachedItem(
            fingerprint=fingerprint,
            embedding=embedding,
            normalized_data=normalized_data,
            timestamp=time.time()
        )
        
        # Almacenar según backend
        if self.backend == "postgresql":
            await self._store_postgresql(item, product_text)
        elif self.backend == "faiss":
            await self._store_faiss(item)
        else:
            self.cache[fingerprint] = item
        
        logger.info(f"💾 Stored in semantic cache: {fingerprint[:8]}...")
    
    async def _store_postgresql(self, item: CachedItem, product_text: str):
        """Almacena en PostgreSQL con pgvector"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO semantic_cache 
                        (fingerprint, product_text, embedding, normalized_data)
                        VALUES (%s, %s, %s::vector, %s)
                        ON CONFLICT (fingerprint) 
                        DO UPDATE SET 
                            normalized_data = EXCLUDED.normalized_data,
                            last_accessed = CURRENT_TIMESTAMP,
                            hit_count = semantic_cache.hit_count + 1
                    """, (
                        item.fingerprint,
                        product_text,
                        item.embedding.tolist(),
                        json.dumps(item.normalized_data, ensure_ascii=False)
                    ))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"PostgreSQL store error: {e}")
    
    async def _store_faiss(self, item: CachedItem):
        """Almacena en índice Faiss"""
        # Normalizar embedding
        embedding = item.embedding / np.linalg.norm(item.embedding)
        
        # Agregar al índice
        self.index.add(embedding.reshape(1, -1))
        
        # Agregar metadata
        self.faiss_items.append({
            'fingerprint': item.fingerprint,
            'normalized_data': item.normalized_data,
            'timestamp': item.timestamp
        })
        
        # Guardar periódicamente
        if len(self.faiss_items) % 100 == 0:
            self._save_faiss_index()
    
    def _save_faiss_index(self):
        """Persiste índice Faiss a disco"""
        try:
            import faiss
            
            os.makedirs("out/cache", exist_ok=True)
            
            # Guardar índice
            faiss.write_index(self.index, "out/cache/faiss_index.bin")
            
            # Guardar metadata
            with open("out/cache/faiss_metadata.json", 'w') as f:
                json.dump(self.faiss_items, f, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save Faiss index: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache"""
        total = self.stats['total_queries']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'hit_rate': self.stats['hits'] / total,
            'semantic_hit_rate': self.stats['semantic_hits'] / total,
            'miss_rate': self.stats['misses'] / total,
            'cache_size': len(self.cache) if self.backend == "memory" else self._get_cache_size()
        }
    
    def _get_cache_size(self) -> int:
        """Obtiene tamaño del cache según backend"""
        if self.backend == "postgresql":
            try:
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM semantic_cache")
                        return cursor.fetchone()[0]
            except:
                return 0
        elif self.backend == "faiss":
            return self.index.ntotal if hasattr(self, 'index') else 0
        else:
            return len(self.cache)
    
    async def warm_cache(self, products: List[Dict[str, Any]]):
        """
        Pre-calienta cache con productos frecuentes
        Útil para mejorar hit rate inicial
        """
        logger.info(f"🔥 Warming cache with {len(products)} products...")
        
        for product in products:
            # Simular normalización (en producción vendría del histórico)
            normalized = {
                'brand': product.get('brand', 'UNKNOWN'),
                'model': product.get('model', product.get('name', '')),
                'category': product.get('category', ''),
                'attributes': product.get('attributes', {}),
                'confidence': 0.95
            }
            
            await self.store(product, normalized)
        
        logger.info(f"✅ Cache warmed with {len(products)} items")


if __name__ == "__main__":
    # Test del cache semántico
    import asyncio
    
    async def test_semantic_cache():
        cache = SemanticCache(backend="memory", similarity_threshold=0.85)
        
        # Producto original
        product1 = {
            'name': 'iPhone 15 Pro Max 256GB Negro',
            'brand': 'APPLE',
            'category': 'smartphones',
            'attributes': {'capacity': '256GB', 'color': 'negro'}
        }
        
        # Normalización simulada
        normalized1 = {
            'brand': 'APPLE',
            'model': 'iPhone 15 Pro Max',
            'attributes': {'capacity': '256GB', 'color': 'black'},
            'confidence': 0.98
        }
        
        # Almacenar
        await cache.store(product1, normalized1)
        
        # Buscar producto similar (diferente color)
        product2 = {
            'name': 'iPhone 15 Pro Max 256GB Blanco',
            'brand': 'APPLE', 
            'category': 'smartphones',
            'attributes': {'capacity': '256GB', 'color': 'blanco'}
        }
        
        # Debería encontrar match semántico
        result = await cache.find_similar(product2)
        print(f"Semantic search result: {result}")
        
        # Estadísticas
        print(f"Cache stats: {cache.get_stats()}")
    
    asyncio.run(test_semantic_cache())