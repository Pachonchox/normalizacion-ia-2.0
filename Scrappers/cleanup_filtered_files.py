#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 LIMPIADOR DE ARCHIVOS FILTRADOS
Elimina archivos *_filtered.json y mantiene solo los filtrados directamente
"""

import os
import glob
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def cleanup_filtered_files(datos_dir: str = "../datos"):
    """Limpiar archivos _filtered duplicados"""
    datos_path = Path(datos_dir)
    
    if not datos_path.exists():
        logging.error(f"Directorio no encontrado: {datos_dir}")
        return 0
    
    removed_count = 0
    total_size = 0
    
    logging.info("🧹 INICIANDO LIMPIEZA DE ARCHIVOS FILTRADOS")
    logging.info(f"📁 Directorio: {datos_path.absolute()}")
    logging.info("=" * 50)
    
    # Buscar en todas las subcarpetas
    for subfolder in ['falabella', 'ripley', 'paris']:
        folder_path = datos_path / subfolder
        if not folder_path.exists():
            logging.info(f"⏭️ Saltando {subfolder} - no existe")
            continue
            
        logging.info(f"📂 Procesando carpeta: {subfolder}")
        
        # Buscar archivos *_filtered.json
        filtered_files = list(folder_path.glob('*_filtered.json'))
        
        if not filtered_files:
            logging.info(f"  ✅ {subfolder}: Sin archivos _filtered para limpiar")
            continue
        
        # Eliminar archivos _filtered
        for filtered_file in filtered_files:
            try:
                file_size = filtered_file.stat().st_size
                filtered_file.unlink()
                removed_count += 1
                total_size += file_size
                logging.info(f"  🗑️ Eliminado: {filtered_file.name} ({file_size:,} bytes)")
                
            except Exception as e:
                logging.error(f"  ❌ Error eliminando {filtered_file.name}: {e}")
    
    # Resumen
    logging.info("=" * 50)
    logging.info("📊 RESUMEN DE LIMPIEZA")
    logging.info(f"🗑️ Archivos eliminados: {removed_count}")
    logging.info(f"💾 Espacio liberado: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    logging.info("✅ Limpieza completada")
    
    return removed_count

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpiar archivos _filtered duplicados')
    parser.add_argument('--datos-dir', default='../datos',
                       help='Directorio de datos (default: ../datos)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Solo mostrar qué se eliminaría (no eliminar realmente)')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logging.info("🔍 MODO DRY-RUN: Solo mostrando archivos que se eliminarían")
        # TODO: Implementar dry-run si es necesario
    
    removed = cleanup_filtered_files(args.datos_dir)
    
    if removed > 0:
        print(f"Limpieza exitosa: {removed} archivos eliminados")
    else:
        print("No hay archivos _filtered para limpiar")

if __name__ == "__main__":
    main()