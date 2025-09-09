#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Agregar Columnas Missing a BD
Agregar columna updated_at que falta en tablas de BD
"""

import sys
import os

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def add_missing_columns():
    print("AGREGANDO COLUMNAS MISSING A BD")
    print("=" * 40)
    
    try:
        connector = get_unified_connector()
        
        # Verificar tablas existentes y columnas
        print("Verificando estructura de tablas...")
        
        # 1. Verificar tabla precios_actuales
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'precios_actuales'
            AND column_name = 'updated_at'
        """
        
        result = connector.execute_query(check_query)
        
        if not result:
            print("Agregando columna updated_at a precios_actuales...")
            alter_query = """
                ALTER TABLE precios_actuales 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
            
            connector.execute_update(alter_query)
            print("OK: Columna updated_at agregada a precios_actuales")
        else:
            print("Columna updated_at ya existe en precios_actuales")
        
        # 2. Verificar tabla productos_maestros
        check_query2 = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'productos_maestros'
            AND column_name = 'updated_at'
        """
        
        result2 = connector.execute_query(check_query2)
        
        if not result2:
            print("Agregando columna updated_at a productos_maestros...")
            alter_query2 = """
                ALTER TABLE productos_maestros 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
            
            connector.execute_update(alter_query2)
            print("OK: Columna updated_at agregada a productos_maestros")
        else:
            print("Columna updated_at ya existe en productos_maestros")
        
        # 3. Verificar tabla ai_metadata_cache
        check_query3 = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ai_metadata_cache'
            AND column_name = 'updated_at'
        """
        
        result3 = connector.execute_query(check_query3)
        
        if not result3:
            print("Agregando columna updated_at a ai_metadata_cache...")
            alter_query3 = """
                ALTER TABLE ai_metadata_cache 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
            
            connector.execute_update(alter_query3)
            print("OK: Columna updated_at agregada a ai_metadata_cache")
        else:
            print("Columna updated_at ya existe en ai_metadata_cache")
        
        print("\nCOLUMNAS AGREGADAS EXITOSAMENTE")
        
        return True
        
    except Exception as e:
        print(f"ERROR agregando columnas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    add_missing_columns()