#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 Migrador de Datos Maestros
Migra taxonomy_v1.json y brand_aliases.json a la base de datos PostgreSQL
"""

import json
import sys
import os
from simple_db_connector import SimplePostgreSQLConnector

def migrate_taxonomy_to_db(connector: SimplePostgreSQLConnector, taxonomy_file: str):
    """Migrar taxonomy_v1.json a tabla categories"""
    
    print(">> Migrando taxonomy_v1.json a tabla categories...")
    
    # Leer archivo de taxonomía
    with open(taxonomy_file, 'r', encoding='utf-8') as f:
        taxonomy = json.load(f)
    
    migrated = 0
    
    with connector.get_connection() as conn:
        with conn.cursor() as cursor:
            for node in taxonomy["nodes"]:
                # Preparar datos para inserción
                category_data = (
                    node["id"],                    # category_id
                    node["name"],                  # name
                    node.get("synonyms", []),      # synonyms (array)
                    None,                          # parent_category
                    [],                            # attributes_schema (array)
                    1,                             # level
                    True,                          # active
                    taxonomy.get("version", "1.0") # version
                )
                
                # Insertar categoría
                cursor.execute("""
                    INSERT INTO categories (
                        category_id, name, synonyms, parent_category, 
                        attributes_schema, level, active, version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (category_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        synonyms = EXCLUDED.synonyms,
                        version = EXCLUDED.version,
                        updated_at = CURRENT_TIMESTAMP
                """, category_data)
                
                migrated += 1
            
            conn.commit()
    
    print(f"OK: {migrated} categorías migradas a la base de datos")
    return migrated

def migrate_brands_to_db(connector: SimplePostgreSQLConnector, brands_file: str):
    """Migrar brand_aliases.json a tabla brands"""
    
    print(">> Migrando brand_aliases.json a tabla brands...")
    
    # Leer archivo de marcas
    with open(brands_file, 'r', encoding='utf-8') as f:
        brands = json.load(f)
    
    migrated = 0
    
    with connector.get_connection() as conn:
        with conn.cursor() as cursor:
            for canonical_brand, aliases in brands.items():
                # Preparar datos para inserción
                brand_data = (
                    canonical_brand,  # brand_canonical
                    aliases,          # aliases (array)
                    True,             # active
                    0.8               # confidence_threshold
                )
                
                # Insertar marca
                cursor.execute("""
                    INSERT INTO brands (
                        brand_canonical, aliases, active, confidence_threshold
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (brand_canonical) DO UPDATE SET
                        aliases = EXCLUDED.aliases,
                        updated_at = CURRENT_TIMESTAMP
                """, brand_data)
                
                migrated += 1
            
            conn.commit()
    
    print(f"OK: {migrated} marcas migradas a la base de datos")
    return migrated

def create_attribute_schemas(connector: SimplePostgreSQLConnector):
    """Crear esquemas de atributos predefinidos por categoría"""
    
    print(">> Creando esquemas de atributos por categoría...")
    
    # Definir esquemas de atributos por categoría
    schemas = {
        "smartphones": [
            ("capacity", "string", False, "capacity en GB o TB"),
            ("color", "string", False, "color del dispositivo"),
            ("network", "string", False, "5G, 4G, etc"),
            ("screen_size", "number", False, "tamaño pantalla en pulgadas"),
            ("ram", "string", False, "memoria RAM"),
            ("storage", "string", False, "almacenamiento interno")
        ],
        "perfumes": [
            ("volume_ml", "number", True, "volumen en mililitros"),
            ("concentration", "string", False, "EDP, EDT, PARFUM"),
            ("gender", "string", False, "Mujer, Hombre, Unisex"),
            ("capacity", "string", False, "capacidad formateada con unidad")
        ],
        "notebooks": [
            ("screen_size", "number", False, "tamaño pantalla en pulgadas"),
            ("ram", "string", False, "memoria RAM"),
            ("storage", "string", False, "almacenamiento SSD/HDD"),
            ("processor", "string", False, "procesador")
        ],
        "smart_tv": [
            ("screen_size", "number", True, "tamaño pantalla en pulgadas"),
            ("resolution", "string", False, "4K, UHD, FHD"),
            ("panel", "string", False, "OLED, QLED, LED"),
            ("smart_features", "boolean", False, "funciones inteligentes")
        ],
        "printers": [
            ("print_type", "string", False, "inkjet, laser, multifuncional"),
            ("color_support", "boolean", False, "soporte para color"),
            ("wireless", "boolean", False, "conectividad inalámbrica")
        ]
    }
    
    created = 0
    
    with connector.get_connection() as conn:
        with conn.cursor() as cursor:
            for category_id, attributes in schemas.items():
                for attr_name, attr_type, required, description in attributes:
                    cursor.execute("""
                        INSERT INTO attributes_schema (
                            category_id, attribute_name, attribute_type, 
                            required, default_value, display_order
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (category_id, attribute_name) DO UPDATE SET
                            attribute_type = EXCLUDED.attribute_type,
                            required = EXCLUDED.required
                    """, (category_id, attr_name, attr_type, required, description, created % 10))
                    
                    created += 1
            
            conn.commit()
    
    print(f"OK: {created} esquemas de atributos creados")
    return created

def verify_migration(connector: SimplePostgreSQLConnector):
    """Verificar que los datos se migraron correctamente"""
    
    print(">> Verificando migración...")
    
    with connector.get_connection() as conn:
        with conn.cursor() as cursor:
            # Verificar categorías
            cursor.execute("SELECT COUNT(*) FROM categories WHERE active = true")
            categories_count = cursor.fetchone()[0]
            
            # Verificar marcas
            cursor.execute("SELECT COUNT(*) FROM brands WHERE active = true")
            brands_count = cursor.fetchone()[0]
            
            # Verificar esquemas de atributos
            cursor.execute("SELECT COUNT(*) FROM attributes_schema")
            schemas_count = cursor.fetchone()[0]
            
            print(f"Verificación completada:")
            print(f"  - Categorías activas: {categories_count}")
            print(f"  - Marcas activas: {brands_count}")
            print(f"  - Esquemas de atributos: {schemas_count}")
            
            # Mostrar algunas categorías como ejemplo
            cursor.execute("SELECT category_id, name, array_length(synonyms, 1) as synonym_count FROM categories LIMIT 5")
            categories = cursor.fetchall()
            
            print("\\nCategorías migradas (muestra):")
            for cat in categories:
                print(f"  - {cat[0]}: {cat[1]} ({cat[2] or 0} sinónimos)")

def main():
    """Función principal de migración"""
    
    print("=== MIGRADOR DE DATOS MAESTROS ===")
    print("Migrando taxonomy_v1.json y brand_aliases.json a PostgreSQL")
    
    # Conectar a base de datos
    connector = SimplePostgreSQLConnector(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!",
        pool_size=3
    )
    
    try:
        # Migrar taxonomía
        taxonomy_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "taxonomy_v1.json")
        migrate_taxonomy_to_db(connector, taxonomy_file)
        
        # Migrar marcas
        brands_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs", "brand_aliases.json")
        migrate_brands_to_db(connector, brands_file)
        
        # Crear esquemas de atributos
        create_attribute_schemas(connector)
        
        # Verificar migración
        verify_migration(connector)
        
        print("\\n🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()