#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 GPT-5 Batch Processor
Sistema optimizado de procesamiento batch con OpenAI Batch API
Reduce costos en 50% para cargas masivas de normalización
"""

from __future__ import annotations
import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """Estructura de request para Batch API"""
    custom_id: str
    method: str = "POST"
    url: str = "/v1/chat/completions"
    body: Dict[str, Any] = None


@dataclass
class BatchJob:
    """Representa un trabajo batch en OpenAI"""
    id: str
    status: str  # validating, in_progress, completed, failed
    created_at: datetime
    products: List[Dict[str, Any]]
    model: str
    estimated_cost: float
    file_id: Optional[str] = None
    result_file_id: Optional[str] = None
    errors: List[str] = None


class BatchProcessor:
    """Procesador de batches con OpenAI Batch API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.batch_jobs = {}
        self.results_cache = {}
        self.max_batch_size = 50000  # Límite OpenAI
        self.batch_window_hours = 24  # Ventana de procesamiento
        
        # Directorio para archivos batch
        self.batch_dir = Path("out/batch_jobs")
        self.batch_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_batch_file(self, products: List[Dict[str, Any]], 
                               model: str, prompt_template: str) -> Tuple[str, str]:
        """
        Crea archivo JSONL para Batch API
        Returns: (file_path, file_content_hash)
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        file_path = self.batch_dir / f"{batch_id}.jsonl"
        
        requests = []
        for i, product in enumerate(products):
            # Crear request individual
            request = BatchRequest(
                custom_id=f"{batch_id}_{i}_{product.get('sku', 'unknown')}",
                body={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres un experto en normalización de productos retail chilenos. Responde SOLO en JSON válido."
                        },
                        {
                            "role": "user",
                            "content": self._format_prompt(prompt_template, product)
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 250 if "mini" in model else 500,
                    "response_format": {"type": "json_object"}
                }
            )
            requests.append(request)
        
        # Escribir archivo JSONL
        with open(file_path, 'w', encoding='utf-8') as f:
            for request in requests:
                f.write(json.dumps(asdict(request), ensure_ascii=False) + '\n')
        
        logger.info(f"✅ Batch file created: {file_path} ({len(products)} products)")
        return str(file_path), batch_id
    
    def _format_prompt(self, template: str, product: Dict[str, Any]) -> str:
        """Formatea prompt con datos del producto"""
        return template.format(
            name=product.get('name', ''),
            category=product.get('category', ''),
            price=product.get('price', 0),
            retailer=product.get('retailer', ''),
            sku=product.get('sku', '')
        )
    
    async def submit_batch(self, file_path: str, model: str, 
                          products: List[Dict[str, Any]]) -> BatchJob:
        """
        Envía batch a OpenAI para procesamiento
        """
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            # Subir archivo
            with open(file_path, 'rb') as f:
                file_response = client.files.create(
                    file=f,
                    purpose='batch'
                )
            
            # Crear batch job
            batch_response = client.batches.create(
                input_file_id=file_response.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={
                    "model": model,
                    "product_count": str(len(products)),
                    "created_at": datetime.now().isoformat()
                }
            )
            
            # Crear objeto BatchJob
            job = BatchJob(
                id=batch_response.id,
                status=batch_response.status,
                created_at=datetime.now(),
                products=products,
                model=model,
                estimated_cost=self._estimate_cost(products, model),
                file_id=file_response.id
            )
            
            self.batch_jobs[job.id] = job
            
            logger.info(f"🚀 Batch submitted: {job.id} ({len(products)} products, ${job.estimated_cost:.2f})")
            return job
            
        except Exception as e:
            logger.error(f"❌ Error submitting batch: {e}")
            raise
    
    async def check_batch_status(self, job_id: str) -> BatchJob:
        """Verifica estado de un batch job"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            batch = client.batches.retrieve(job_id)
            job = self.batch_jobs.get(job_id)
            
            if job:
                job.status = batch.status
                
                if batch.status == "completed":
                    job.result_file_id = batch.output_file_id
                    logger.info(f"✅ Batch completed: {job_id}")
                elif batch.status == "failed":
                    job.errors = [batch.errors] if batch.errors else ["Unknown error"]
                    logger.error(f"❌ Batch failed: {job_id}")
                
                self.batch_jobs[job_id] = job
            
            return job
            
        except Exception as e:
            logger.error(f"❌ Error checking batch status: {e}")
            return None
    
    async def retrieve_results(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Recupera resultados de un batch completado
        """
        job = self.batch_jobs.get(job_id)
        if not job or not job.result_file_id:
            logger.error(f"No results available for job {job_id}")
            return []
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            # Descargar archivo de resultados
            result_content = client.files.content(job.result_file_id)
            
            # Parsear resultados JSONL
            results = []
            for line in result_content.text.split('\n'):
                if line.strip():
                    result = json.loads(line)
                    custom_id = result.get('custom_id', '')
                    
                    # Extraer respuesta del modelo
                    if result.get('response', {}).get('body', {}).get('choices'):
                        content = result['response']['body']['choices'][0]['message']['content']
                        try:
                            normalized_data = json.loads(content)
                            normalized_data['_batch_id'] = job_id
                            normalized_data['_custom_id'] = custom_id
                            results.append(normalized_data)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON for {custom_id}")
                            results.append({"error": "json_parse_error", "_custom_id": custom_id})
            
            # Cachear resultados
            self.results_cache[job_id] = results
            
            logger.info(f"📥 Retrieved {len(results)} results from batch {job_id}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error retrieving results: {e}")
            return []
    
    def _estimate_cost(self, products: List[Dict[str, Any]], model: str) -> float:
        """Estima costo del batch con 50% descuento"""
        tokens_per_product = 250 if "mini" in model else 500
        total_tokens = len(products) * tokens_per_product
        
        # Precios estimados (ajustar según anuncio oficial)
        prices = {
            "gpt-5-mini": 0.0003,  # por 1K tokens
            "gpt-5": 0.001,
            "gpt-4o-mini": 0.0015
        }
        
        base_cost = (total_tokens / 1000) * prices.get(model, 0.001)
        batch_cost = base_cost * 0.5  # 50% descuento
        
        return batch_cost
    
    async def process_batch_with_fallback(self, products: List[Dict[str, Any]], 
                                         model: str, prompt_template: str) -> List[Dict[str, Any]]:
        """
        Procesa batch con fallback a procesamiento síncrono si falla
        """
        try:
            # Crear y enviar batch
            file_path, batch_id = await self.create_batch_file(products, model, prompt_template)
            job = await self.submit_batch(file_path, model, products)
            
            # Esperar completación (con timeout)
            max_wait = 3600 * 24  # 24 horas
            check_interval = 60  # Revisar cada minuto
            elapsed = 0
            
            while elapsed < max_wait:
                job = await self.check_batch_status(job.id)
                
                if job.status == "completed":
                    return await self.retrieve_results(job.id)
                elif job.status == "failed":
                    logger.error(f"Batch failed, falling back to sync processing")
                    break
                
                await asyncio.sleep(check_interval)
                elapsed += check_interval
            
            # Fallback a procesamiento síncrono
            logger.warning("Batch timeout or failed, using synchronous processing")
            return await self._process_sync_fallback(products, model, prompt_template)
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}, using fallback")
            return await self._process_sync_fallback(products, model, prompt_template)
    
    async def _process_sync_fallback(self, products: List[Dict[str, Any]], 
                                    model: str, prompt_template: str) -> List[Dict[str, Any]]:
        """Procesamiento síncrono como fallback"""
        results = []
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            for product in products:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Eres un experto en normalización de productos retail chilenos."},
                            {"role": "user", "content": self._format_prompt(prompt_template, product)}
                        ],
                        temperature=0.1,
                        max_tokens=250 if "mini" in model else 500,
                        timeout=15
                    )
                    
                    content = response.choices[0].message.content
                    normalized = json.loads(content)
                    results.append(normalized)
                    
                except Exception as e:
                    logger.error(f"Error processing product: {e}")
                    results.append({"error": str(e)})
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
        
        return results
    
    def get_batch_status_summary(self) -> Dict[str, Any]:
        """Resumen del estado de todos los batches"""
        summary = {
            'total_jobs': len(self.batch_jobs),
            'by_status': {},
            'total_products': 0,
            'estimated_total_cost': 0.0
        }
        
        for job in self.batch_jobs.values():
            status = job.status
            if status not in summary['by_status']:
                summary['by_status'][status] = 0
            summary['by_status'][status] += 1
            summary['total_products'] += len(job.products)
            summary['estimated_total_cost'] += job.estimated_cost
        
        return summary


class BatchOrchestrator:
    """Orquestador de procesamiento batch para poblamiento masivo"""
    
    def __init__(self):
        self.processor = BatchProcessor()
        self.batch_queue = []
        self.processing_stats = {
            'total_processed': 0,
            'total_cost': 0.0,
            'start_time': None,
            'batches_completed': 0
        }
    
    async def process_initial_population(self, products: List[Dict[str, Any]], 
                                        batch_size: int = 10000) -> Dict[str, Any]:
        """
        Procesa población inicial de productos en batches grandes
        Optimizado para máximo ahorro en costos
        """
        logger.info(f"🚀 Starting initial population: {len(products)} products")
        self.processing_stats['start_time'] = datetime.now()
        
        # Dividir en mega-batches
        batches = []
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"📦 Created {len(batches)} batches of ~{batch_size} products")
        
        # Procesar batches en paralelo (hasta 3 simultáneos)
        semaphore = asyncio.Semaphore(3)
        
        async def process_batch_with_limit(batch, index):
            async with semaphore:
                logger.info(f"Processing batch {index + 1}/{len(batches)}")
                return await self.processor.process_batch_with_fallback(
                    batch, 
                    "gpt-5-mini",  # Usar modelo económico para población inicial
                    self._get_minimal_prompt_template()
                )
        
        # Ejecutar todos los batches
        tasks = [process_batch_with_limit(batch, i) for i, batch in enumerate(batches)]
        results = await asyncio.gather(*tasks)
        
        # Consolidar resultados
        all_results = []
        for batch_results in results:
            if batch_results:
                all_results.extend(batch_results)
                self.processing_stats['batches_completed'] += 1
        
        self.processing_stats['total_processed'] = len(all_results)
        
        # Calcular estadísticas finales
        elapsed = (datetime.now() - self.processing_stats['start_time']).total_seconds()
        
        return {
            'status': 'completed',
            'total_products': len(products),
            'processed': len(all_results),
            'batches': len(batches),
            'elapsed_seconds': elapsed,
            'products_per_second': len(all_results) / elapsed if elapsed > 0 else 0,
            'estimated_cost': self.processor._estimate_cost(products, "gpt-5-mini"),
            'results': all_results
        }
    
    def _get_minimal_prompt_template(self) -> str:
        """Template minimalista para población inicial (ahorro de tokens)"""
        return """Producto: {name}
Cat: {category}
Precio: ${price}

JSON:
{{
  "brand": "marca detectada",
  "model": "modelo específico",
  "attributes": {{"capacity": "", "color": "", "size": ""}},
  "confidence": 0.95
}}"""


if __name__ == "__main__":
    # Test del procesador batch
    async def test_batch():
        processor = BatchProcessor()
        
        test_products = [
            {"name": f"Product {i}", "category": "test", "price": 1000 * i}
            for i in range(5)
        ]
        
        # Test crear archivo batch
        file_path, batch_id = await processor.create_batch_file(
            test_products,
            "gpt-5-mini",
            "Normalize: {name}"
        )
        print(f"✅ Test file created: {file_path}")
        
        # Test estimación de costos
        cost = processor._estimate_cost(test_products, "gpt-5-mini")
        print(f"💰 Estimated cost: ${cost:.4f}")
        
        # Test orquestador
        orchestrator = BatchOrchestrator()
        print("\n🎯 Testing orchestrator with 100 products...")
        
        large_test = [
            {"name": f"iPhone {i}", "category": "smartphones", "price": 1000000}
            for i in range(100)
        ]
        
        # Simular procesamiento (sin API real)
        print(f"Would process {len(large_test)} products in batches")
        print(f"Estimated savings: 50% with Batch API")
    
    # Ejecutar test
    asyncio.run(test_batch())