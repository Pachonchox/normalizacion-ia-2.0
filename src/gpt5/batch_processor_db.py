#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Batch Processor con Integración BD
Procesamiento batch con OpenAI Batch API y base de datos
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import hashlib
import logging
from enum import Enum

# Importar conector BD
import sys
sys.path.append(str(Path(__file__).parent.parent))
from gpt5_db_connector import GPT5DatabaseConnector, BatchStatus, ModelType

logger = logging.getLogger(__name__)

class BatchProcessorDB:
    """Procesador batch con integración a BD"""
    
    def __init__(self, api_key: str, db_connector: GPT5DatabaseConnector):
        self.api_key = api_key
        self.db = db_connector
        self.base_url = "https://api.openai.com/v1"
        self.batch_dir = Path("out/batches")
        self.batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers para API
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_batch_file(self, products: List[Dict[str, Any]], 
                              model: str, prompt_template: str,
                              batch_id: str = None) -> Tuple[str, str]:
        """Crear archivo JSONL para batch processing"""
        
        if not batch_id:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(products).encode()).hexdigest()[:8]}"
        
        file_path = self.batch_dir / f"{batch_id}.jsonl"
        
        # Crear requests JSONL
        with open(file_path, 'w', encoding='utf-8') as f:
            for idx, product in enumerate(products):
                # Crear custom_id único
                custom_id = f"{batch_id}_{idx}_{product.get('fingerprint', '')[:8]}"
                
                # Formatear prompt según modelo
                prompt = self._format_prompt(product, model, prompt_template)
                
                # Estructura de request para Batch API
                request = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres un experto en normalización de productos retail chilenos. Responde SOLO en formato JSON válido."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.1,
                        "max_completion_tokens": self._get_max_tokens(model),
                        "response_format": {"type": "json_object"}
                    }
                }
                
                f.write(json.dumps(request, ensure_ascii=False) + '\n')
        
        logger.info(f"✅ Archivo batch creado: {file_path} ({len(products)} productos)")
        return str(file_path), batch_id
    
    def _format_prompt(self, product: Dict, model: str, template: str) -> str:
        """Formatear prompt según modelo y estilo"""
        
        # Estilos optimizados por modelo
        if "gpt-5-mini" in model:
            # Ultra-compacto para GPT-5-mini
            if "_batch_mode" in product or "BATCH" in template:
                return f"N:{product.get('name', '')[:100]}|C:{product.get('category', '')}|P:{product.get('price', 0)}"
            else:
                return f"Normaliza: {product.get('name', '')[:150]} [{product.get('category', '')}]"
        
        elif "gpt-5" in model and "gpt-5-mini" not in model:
            # Estándar para GPT-5
            return f"""Producto: {product.get('name', '')}
Categoría: {product.get('category', '')}
Precio: ${product.get('price', 0):,} CLP
Retailer: {product.get('retailer', '')}

Extrae: marca, modelo, atributos clave"""
        
        else:
            # Fallback detallado para GPT-4o
            return template.format(**product) if "{" in template else template
    
    def _get_max_tokens(self, model: str) -> int:
        """Obtener max_completion_tokens según modelo"""
        config = self.db.get_model_config(model)
        if config:
            return min(config.get('max_completion_tokens', 500) // 10, 500)  # Usar 10% del máximo
        
        # Defaults
        return {
            "gpt-5-mini": 200,
            "gpt-5": 400,
            "gpt-4o-mini": 300,
            "gpt-4o": 500
        }.get(model, 300)
    
    async def upload_batch_file(self, file_path: str) -> str:
        """Subir archivo a OpenAI"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('purpose', 'batch')
                data.add_field('file', f, filename=Path(file_path).name)
                
                async with session.post(
                    f"{self.base_url}/files",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        file_id = result['id']
                        logger.info(f"📤 Archivo subido: {file_id}")
                        return file_id
                    else:
                        raise Exception(f"Error subiendo archivo: {result}")
    
    async def create_batch_job(self, file_id: str, batch_id: str, 
                              completion_window: str = "24h") -> str:
        """Crear job de batch en OpenAI"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "input_file_id": file_id,
                "endpoint": "/v1/chat/completions",
                "completion_window": completion_window,
                "metadata": {
                    "batch_id": batch_id,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            async with session.post(
                f"{self.base_url}/batches",
                headers=self.headers,
                json=payload
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    openai_batch_id = result['id']
                    logger.info(f"🚀 Batch job creado: {openai_batch_id}")
                    
                    # Actualizar en BD
                    self.db.update_batch_status(
                        batch_id, 
                        BatchStatus.PROCESSING,
                        metadata={"openai_batch_id": openai_batch_id}
                    )
                    
                    return openai_batch_id
                else:
                    raise Exception(f"Error creando batch: {result}")
    
    async def check_batch_status(self, openai_batch_id: str) -> Dict:
        """Verificar estado de batch en OpenAI"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/batches/{openai_batch_id}",
                headers=self.headers
            ) as response:
                return await response.json()
    
    async def download_results(self, output_file_id: str, batch_id: str) -> str:
        """Descargar resultados del batch"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/files/{output_file_id}/content",
                headers=self.headers
            ) as response:
                content = await response.text()
                
                # Guardar resultados
                output_path = self.batch_dir / f"{batch_id}_results.jsonl"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"📥 Resultados descargados: {output_path}")
                return str(output_path)
    
    async def process_batch_results(self, results_path: str, batch_id: str) -> List[Dict]:
        """Procesar resultados del batch y actualizar BD"""
        processed_results = []
        successful = 0
        failed = 0
        total_tokens_input = 0
        total_tokens_output = 0
        total_cost = 0.0
        
        with open(results_path, 'r', encoding='utf-8') as f:
            for line in f:
                result = json.loads(line)
                custom_id = result.get('custom_id', '')
                
                if result.get('response', {}).get('status_code') == 200:
                    # Éxito
                    response_body = result['response']['body']
                    choices = response_body.get('choices', [])
                    
                    if choices:
                        content = choices[0]['message']['content']
                        try:
                            normalized_data = json.loads(content)
                            
                            # Extraer fingerprint del custom_id
                            parts = custom_id.split('_')
                            fingerprint = parts[-1] if len(parts) > 2 else None
                            
                            if fingerprint:
                                # Guardar en cache IA
                                cache = GPT5AICache(self.db)
                                cache.set(
                                    fingerprint=fingerprint,
                                    metadata=normalized_data,
                                    model_used=response_body.get('model'),
                                    tokens_used=response_body.get('usage', {}).get('total_tokens'),
                                    batch_id=batch_id
                                )
                            
                            processed_results.append({
                                'custom_id': custom_id,
                                'fingerprint': fingerprint,
                                'normalized': normalized_data,
                                'tokens': response_body.get('usage', {})
                            })
                            
                            successful += 1
                            
                            # Acumular tokens y costos
                            usage = response_body.get('usage', {})
                            total_tokens_input += usage.get('prompt_tokens', 0)
                            total_tokens_output += usage.get('completion_tokens', 0)
                            
                        except json.JSONDecodeError:
                            logger.error(f"Error parseando JSON para {custom_id}")
                            failed += 1
                else:
                    # Error
                    logger.error(f"Error en {custom_id}: {result.get('error')}")
                    failed += 1
        
        # Calcular costo total con descuento batch
        model_config = self.db.get_model_config(batch_id.split('_')[0] if '_' in batch_id else 'gpt-5-mini')
        if model_config:
            cost_input = (total_tokens_input / 1000) * model_config['cost_per_1k_input']
            cost_output = (total_tokens_output / 1000) * model_config['cost_per_1k_output']
            total_cost = (cost_input + cost_output) * model_config['batch_discount']
        
        # Actualizar batch en BD
        self.db.update_batch_status(
            batch_id,
            BatchStatus.COMPLETED if failed == 0 else BatchStatus.COMPLETED,
            processed=successful + failed,
            metadata={
                'successful': successful,
                'failed': failed,
                'total_tokens_input': total_tokens_input,
                'total_tokens_output': total_tokens_output,
                'actual_cost': total_cost
            }
        )
        
        logger.info(f"""
        ✅ Batch {batch_id} procesado:
        - Exitosos: {successful}
        - Fallidos: {failed}
        - Tokens: {total_tokens_input} input, {total_tokens_output} output
        - Costo: ${total_cost:.4f} (con 50% descuento)
        """)
        
        return processed_results
    
    async def process_products_batch(self, products: List[Dict], model: str,
                                    prompt_template: str = "Normalize: {name}") -> List[Dict]:
        """Pipeline completo de batch processing"""
        
        # 1. Registrar batch en BD
        batch_id = self.db.create_batch_job(
            model=model,
            products=products,
            estimated_cost=self._estimate_cost(products, model)
        )
        
        try:
            # 2. Crear archivo JSONL
            file_path, _ = await self.create_batch_file(products, model, prompt_template, batch_id)
            
            # 3. Subir archivo a OpenAI
            file_id = await self.upload_batch_file(file_path)
            
            # 4. Crear batch job
            openai_batch_id = await self.create_batch_job(file_id, batch_id)
            
            # 5. Esperar completación (polling)
            max_attempts = 720  # 12 horas máximo
            attempt = 0
            
            while attempt < max_attempts:
                status = await self.check_batch_status(openai_batch_id)
                
                if status['status'] == 'completed':
                    # 6. Descargar resultados
                    output_file_id = status['output_file_id']
                    results_path = await self.download_results(output_file_id, batch_id)
                    
                    # 7. Procesar resultados
                    return await self.process_batch_results(results_path, batch_id)
                
                elif status['status'] == 'failed':
                    error_msg = status.get('errors', {}).get('data', [{}])[0].get('message', 'Unknown error')
                    self.db.update_batch_status(batch_id, BatchStatus.FAILED, error=error_msg)
                    raise Exception(f"Batch failed: {error_msg}")
                
                # Esperar antes del siguiente intento
                await asyncio.sleep(60)  # Verificar cada minuto
                attempt += 1
            
            # Timeout
            self.db.update_batch_status(batch_id, BatchStatus.FAILED, error="Timeout after 12 hours")
            raise Exception("Batch processing timeout")
            
        except Exception as e:
            logger.error(f"Error en batch processing: {e}")
            self.db.update_batch_status(batch_id, BatchStatus.FAILED, error=str(e))
            raise
    
    def _estimate_cost(self, products: List[Dict], model: str) -> float:
        """Estimar costo del batch"""
        avg_tokens_per_product = 250  # Estimado
        total_tokens = len(products) * avg_tokens_per_product
        
        config = self.db.get_model_config(model)
        if config:
            cost = (total_tokens / 1000) * config['cost_per_1k_input']
            return cost * config['batch_discount']  # Aplicar descuento
        
        return len(products) * 0.0003  # Default

class BatchOrchestrator:
    """Orquestador de batches con BD"""
    
    def __init__(self, api_key: str, db_connector: GPT5DatabaseConnector):
        self.processor = BatchProcessorDB(api_key, db_connector)
        self.db = db_connector
    
    async def process_pending_batches(self):
        """Procesar todos los batches pendientes"""
        pending = self.db.get_pending_batches(limit=5)
        
        for batch in pending:
            batch_id = batch['batch_id']
            logger.info(f"📋 Procesando batch pendiente: {batch_id}")
            
            # TODO: Recuperar productos del batch y procesarlos
            # Este método necesitaría acceso a los productos originales
            # guardados en algún lugar (archivo o BD)
    
    def create_optimized_batches(self, products: List[Dict], 
                                max_batch_size: int = 50000) -> List[Dict]:
        """Crear batches optimizados por modelo y tamaño"""
        
        # Agrupar por complejidad/modelo
        batches_by_model = {
            ModelType.GPT5_MINI.value: [],
            ModelType.GPT5.value: [],
            ModelType.GPT4O_MINI.value: []
        }
        
        for product in products:
            # Calcular complejidad y obtener modelo
            fingerprint = product.get('fingerprint', '')
            complexity = self.db.get_complexity_analysis(fingerprint)
            
            if complexity:
                model = complexity['model_assigned']
            else:
                # Calcular complejidad si no existe
                # (simplificado aquí, debería usar ComplexityAnalyzer)
                model = ModelType.GPT5_MINI.value
            
            batches_by_model[model].append(product)
        
        # Dividir en sub-batches por tamaño
        final_batches = []
        
        for model, products_list in batches_by_model.items():
            if not products_list:
                continue
            
            # Dividir en chunks
            for i in range(0, len(products_list), max_batch_size):
                chunk = products_list[i:i + max_batch_size]
                
                if chunk:
                    batch_id = self.db.create_batch_job(
                        model=model,
                        products=chunk,
                        estimated_cost=self.processor._estimate_cost(chunk, model)
                    )
                    
                    final_batches.append({
                        'batch_id': batch_id,
                        'model': model,
                        'products': chunk,
                        'size': len(chunk)
                    })
        
        logger.info(f"📦 Creados {len(final_batches)} batches optimizados")
        return final_batches

# Cache IA para compatibilidad
from gpt5_db_connector import GPT5AICache

if __name__ == "__main__":
    # Testing
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        # Conectar a BD
        db = GPT5DatabaseConnector(
            host="34.176.197.136",
            port=5432,
            database="postgres",
            user="postgres",
            password="Osmar2503!",
            pool_size=5
        )
        
        # Crear procesador
        processor = BatchProcessorDB(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            db_connector=db
        )
        
        # Productos de prueba
        test_products = [
            {
                "fingerprint": hashlib.sha1(f"test_{i}".encode()).hexdigest(),
                "name": f"iPhone 15 Pro Max {i}GB",
                "category": "smartphones",
                "price": 1200000 + i * 10000,
                "retailer": "falabella"
            }
            for i in range(128, 513, 128)
        ]
        
        if os.getenv("OPENAI_API_KEY"):
            # Solo ejecutar si hay API key
            results = await processor.process_products_batch(
                test_products,
                "gpt-5-mini",
                "Normalize: {name}"
            )
            
            print(f"✅ Procesados {len(results)} productos")
        else:
            print("⚠️ No hay OPENAI_API_KEY configurada")
        
        db.close()
    
    # asyncio.run(test())