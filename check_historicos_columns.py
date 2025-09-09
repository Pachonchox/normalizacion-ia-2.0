#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Verificar Columnas Precios Históricos
Revisar si precios_historicos tiene columnas necesarias
"""

import sys
import os

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def check_historicos_columns():
    print("VERIFICANDO COLUMNAS PRECIOS HISTORICOS")
    print("=" * 50)
    
    try:
        connector = get_unified_connector()
        
        # Verificar todas las columnas de precios_historicos
        columns_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'precios_historicos'
            ORDER BY ordinal_position
        """
        
        columns = connector.execute_query(columns_query)
        
        if not columns:
            print("ERROR: Tabla precios_historicos NO EXISTE")
            return False
        
        print(f"Tabla precios_historicos encontrada con {len(columns)} columnas:")
        print("-" * 70)
        
        column_names = []
        for col in columns:
            column_names.append(col['column_name'])
            print(f"  {col['column_name']:20} | {col['data_type']:15} | {col['is_nullable']:10} | {col['column_default'] or 'NULL'}")
        
        print("-" * 70)
        
        # Verificar columnas específicas que podrían necesitarse
        required_columns = ['updated_at', 'created_at', 'fecha_registro', 'timestamp']
        missing_columns = []
        
        for req_col in required_columns:
            if req_col not in column_names:
                missing_columns.append(req_col)
        
        if missing_columns:
            print(f"\nCOLUMNAS POTENCIALMENTE FALTANTES:")
            for col in missing_columns:
                print(f"  - {col}")
        else:
            print(f"\nTodas las columnas de timestamp parecen estar presentes")
        
        # Verificar si hay referencias a precios_historicos en unified_connector
        print(f"\nVerificando referencias en código...")
        
        return True
        
    except Exception as e:
        print(f"ERROR verificando precios_historicos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_historicos_columns()