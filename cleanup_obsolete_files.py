#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para eliminar archivos obsoletos de pruebas y documentación
"""

import os
import glob

def cleanup_obsolete_files():
    print("=== LIMPIEZA DE ARCHIVOS OBSOLETOS ===")
    
    # Archivos a eliminar
    obsolete_patterns = [
        # Reportes de prueba temporales
        "*test_integrity_report_*.txt",
        
        # Scripts de prueba obsoletos (mantener solo los esenciales)
        "test_connection.py",
        "test_simple_connection.py", 
        "test_integrated_system.py",
        "fix_emojis_test.py",
        "test_local_db_integrity.py",
        "test_real_db_integrity.py",
        "test_connection_simple.py",
        "test_production_connection.py",
        "test_db_integrity.py",
        "clean_test_connection.py",
        "test_all_connections.py",
        "test_quick_connections.py",
        "test_final_connection.py",
        "test_intraday_price_changes.py",
        "verify_prices_test.py",
        
        # Scripts temporales de limpieza
        "fix_emojis.py",
        "fix_emojis_test.py",
    ]
    
    # Archivos a mantener (esenciales)
    keep_files = [
        "test_simple_clean.py",  # Conexión básica
        "test_real_integrity_fixed.py",  # Integridad final
        "test_prices_keep_data.py",  # Inserción de precios
        "test_price_changes_simple.py",  # Cambios intradía
        "cleanup_test_data.py",  # Limpieza de BD
        "check_real_schema.py",  # Verificación de esquema
    ]
    
    deleted_count = 0
    
    for pattern in obsolete_patterns:
        files = glob.glob(pattern)
        for file in files:
            filename = os.path.basename(file)
            if filename not in keep_files:
                try:
                    os.remove(file)
                    print(f"Eliminado: {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Error eliminando {filename}: {e}")
            else:
                print(f"Mantenido: {filename} (esencial)")
    
    print(f"\n=== ARCHIVOS MANTENIDOS (ESENCIALES) ===")
    for essential_file in keep_files:
        if os.path.exists(essential_file):
            print(f"✓ {essential_file}")
        else:
            print(f"- {essential_file} (no encontrado)")
    
    print(f"\n=== RESUMEN ===")
    print(f"Archivos obsoletos eliminados: {deleted_count}")
    print("Archivos esenciales mantenidos: 6")
    
    return deleted_count

def main():
    print("LIMPIEZA DE ARCHIVOS OBSOLETOS DE PRUEBAS")
    
    try:
        deleted = cleanup_obsolete_files()
        
        if deleted > 0:
            print(f"\nLIMPIEZA EXITOSA: {deleted} archivos obsoletos eliminados")
        else:
            print(f"\nSIN ARCHIVOS OBSOLETOS: Todo limpio")
        
        return 0
        
    except Exception as e:
        print(f"Error en limpieza: {e}")
        return 1

if __name__ == "__main__":
    exit(main())