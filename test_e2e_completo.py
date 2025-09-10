#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test E2E completo del sistema GPT-5
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Configurar entorno
os.environ['REDIS_MOCK'] = 'true'
os.environ['OPENAI_API_KEY'] = 'sk-test-key-for-testing'

# Cambiar al directorio src
os.chdir(Path(__file__).parent / 'src')
sys.path.insert(0, '.')

async def test_sistema_completo():
    """Test del sistema completo con pipeline real"""
    print("=== TEST E2E SISTEMA GPT-5 COMPLETO ===\n")
    
    try:
        # Usar el orquestador principal
        from gpt5.main_e2e import GPT5Pipeline, ProcessingMode
        
        # Crear datos de prueba
        productos_test = [
            {
                'name': 'iPhone 15 Pro Max 256GB Natural Titanium Liberado',
                'category': 'smartphones',
                'price': 1299990,
                'retailer': 'falabella',
                'url': 'https://falabella.com/product/123',
                'brand': 'Apple'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 512GB Titanium Gray 5G',
                'category': 'smartphones', 
                'price': 1399990,
                'retailer': 'paris',
                'url': 'https://paris.cl/product/456'
            },
            {
                'name': 'MacBook Pro 16 M3 Max 48GB RAM 1TB SSD Space Gray',
                'category': 'notebooks',
                'price': 3899990,
                'retailer': 'ripley',
                'url': 'https://ripley.cl/product/789'
            }
        ]
        
        # Crear directorio temporal de datos
        test_dir = Path('../test_data_temp')
        test_dir.mkdir(exist_ok=True)
        
        # Guardar productos como JSON para ingest
        with open(test_dir / 'productos_test.json', 'w', encoding='utf-8') as f:
            json.dump({
                'retailer': 'test_retailer',
                'category': 'test_category',
                'products': productos_test
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Datos de prueba creados: {len(productos_test)} productos")
        
        # Configurar pipeline
        config = {
            'input_dir': str(test_dir),
            'output_dir': '../out_test',
            'processing_mode': ProcessingMode.SINGLE,  # Modo individual para testing
            'enable_quality_gate': True,
            'min_quality_score': 0.5,  # Más permisivo para testing
            'save_to_db': False,  # No guardar en BD para testing
            'save_to_jsonl': True
        }
        
        print(f"📋 Configuración del pipeline:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        
        # Crear y ejecutar pipeline
        print(f"\n🚀 Iniciando pipeline GPT-5...")
        pipeline = GPT5Pipeline(config)
        
        # Ejecutar pipeline completo
        stats = await pipeline.run()
        
        print(f"\n📊 ESTADÍSTICAS FINALES:")
        print(f"   Total productos: {stats['total_products']}")
        print(f"   Procesados: {stats['processed']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Errores: {stats['errors']}")
        print(f"   Duración: {stats.get('duration_seconds', 0):.1f}s")
        
        # Verificar outputs
        output_dir = Path(config['output_dir'])
        if output_dir.exists():
            output_files = list(output_dir.glob('*.jsonl'))
            if output_files:
                print(f"\n📄 Archivos generados:")
                for file in output_files:
                    print(f"   {file.name}: {file.stat().st_size} bytes")
                    
                # Leer primer resultado
                with open(output_files[0], 'r', encoding='utf-8') as f:
                    primer_resultado = json.loads(f.readline())
                    
                print(f"\n🔍 PRIMER RESULTADO:")
                print(f"   Nombre: {primer_resultado.get('name', 'N/A')}")
                print(f"   Marca: {primer_resultado.get('brand', 'N/A')}")
                print(f"   Modelo: {primer_resultado.get('model', 'N/A')}")
                print(f"   Categoría: {primer_resultado.get('category', 'N/A')}")
                print(f"   AI Enhanced: {primer_resultado.get('ai_enhanced', False)}")
                print(f"   AI Confidence: {primer_resultado.get('ai_confidence', 0)}")
                print(f"   Processing Version: {primer_resultado.get('processing_version', 'N/A')}")
        
        print(f"\n✅ PIPELINE E2E COMPLETADO EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN PIPELINE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Limpiar archivos temporales
        try:
            import shutil
            if 'test_dir' in locals() and test_dir.exists():
                shutil.rmtree(test_dir)
                print(f"🧹 Archivos temporales limpiados")
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_sistema_completo())
    print(f"\n🏁 RESULTADO FINAL: {'✅ ÉXITO' if success else '❌ FALLO'}")
    sys.exit(0 if success else 1)