#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AUTO-FILTRO DE PRODUCTOS
Se ejecuta automáticamente para filtrar archivos JSON recién creados
Elimina productos ruidosos antes del procesamiento con IA
"""

import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
from product_filter import ProductFilter

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('../datos/auto_filter.log', encoding='utf-8')
    ]
)

class AutoFilter:
    """Auto-filtrador de productos recién scraped"""
    
    def __init__(self):
        self.filter = ProductFilter()
        self.datos_dir = Path("../datos")
        self.processed_files = set()
        
        # Crear carpetas necesarias
        self.datos_dir.mkdir(exist_ok=True)
    
    def get_recent_json_files(self, minutes_back: int = 10) -> List[Path]:
        """Obtener archivos JSON creados recientemente"""
        recent_files = []
        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)
        
        # Buscar en todas las subcarpetas
        for subfolder in ['falabella', 'ripley', 'paris']:
            folder_path = self.datos_dir / subfolder
            if folder_path.exists():
                for json_file in folder_path.glob('*.json'):
                    # Verificar tiempo de modificación
                    file_time = datetime.fromtimestamp(json_file.stat().st_mtime)
                    if file_time > cutoff_time and json_file not in self.processed_files:
                        recent_files.append(json_file)
        
        return recent_files
    
    def process_file(self, json_file: Path) -> bool:
        """Procesar un archivo JSON individual"""
        try:
            logging.info(f"🧹 Procesando {json_file.name}")
            
            # Filtrar productos y reemplazar archivo original
            stats = self.filter.filter_json_file(str(json_file), replace_original=True)
            
            # Marcar como procesado
            self.processed_files.add(json_file)
            
            # Log de resultados
            reduction_pct = ((stats['total_original'] - stats['total_remaining']) / 
                           stats['total_original'] * 100) if stats['total_original'] > 0 else 0
            
            logging.info(f"✅ {json_file.name} -> {stats['total_remaining']}/{stats['total_original']} productos ({reduction_pct:.1f}% filtrados) [REEMPLAZADO]")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Error procesando {json_file}: {e}")
            return False
    
    def run_once(self) -> int:
        """Ejecutar filtrado una vez"""
        logging.info("🔍 Buscando archivos JSON recientes...")
        
        recent_files = self.get_recent_json_files()
        
        if not recent_files:
            logging.info("📂 No hay archivos nuevos para procesar")
            return 0
        
        processed_count = 0
        for json_file in recent_files:
            if self.process_file(json_file):
                processed_count += 1
        
        logging.info(f"🎯 Procesados {processed_count}/{len(recent_files)} archivos")
        return processed_count
    
    def monitor_and_filter(self, check_interval: int = 60):
        """Monitorear carpeta y filtrar archivos nuevos"""
        logging.info("🤖 INICIANDO AUTO-FILTRO DE PRODUCTOS")
        logging.info(f"📁 Monitoreando: {self.datos_dir}")
        logging.info(f"⏱️ Intervalo de chequeo: {check_interval}s")
        logging.info("🛑 Detener con Ctrl+C")
        logging.info("=" * 50)
        
        try:
            while True:
                processed = self.run_once()
                
                if processed > 0:
                    logging.info(f"😴 Esperando {check_interval}s hasta próximo chequeo...")
                
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logging.info("⚠️ Auto-filtro detenido por usuario")
        except Exception as e:
            logging.error(f"💥 Error crítico en auto-filtro: {e}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto-filtro de productos ruidosos')
    parser.add_argument('--mode', choices=['once', 'monitor'], default='once',
                       help='Modo: once (una vez) o monitor (continuo)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Intervalo de monitoreo en segundos (default: 60)')
    
    args = parser.parse_args()
    
    auto_filter = AutoFilter()
    
    if args.mode == 'monitor':
        auto_filter.monitor_and_filter(args.interval)
    else:
        processed = auto_filter.run_once()
        if processed > 0:
            print(f"Filtrados {processed} archivos")
        else:
            print("No hay archivos nuevos para procesar")

if __name__ == "__main__":
    main()