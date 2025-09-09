# 🔍 Scrapers de Búsqueda

Esta carpeta contiene scrapers especializados que realizan **búsquedas de términos específicos** en lugar de navegar por categorías.

## 📁 Estructura

```
scrapers_busqueda/
├── falabella_busqueda_continuo.py  # Scraper continuo de búsquedas Falabella
├── test_falabella_busqueda.py      # Script de prueba para búsquedas
└── README.md                        # Este archivo
```

## 🎯 Características

### Búsquedas vs Categorías
- **Búsquedas**: Usan URLs como `https://www.falabella.com/falabella-cl/search?Ntt={término}`
- **Categorías**: Usan URLs como `https://www.falabella.com/falabella-cl/category/cat123/Nombre`
- **Selectores diferentes**: Las búsquedas usan `.pod` y `[data-pod="catalyst-pod"]`

## 📋 Términos de Búsqueda Configurados

### Falabella
- `smartphone` - Smartphones
- `smartv` - Smart TV  
- `tablet` - Tablets

## 🚀 Uso

### Prueba rápida (1 página por búsqueda)
```bash
python test_falabella_busqueda.py
```

### Scraper continuo (10 páginas, rotación cada 10 minutos)
```bash
python falabella_busqueda_continuo.py
```

## 📊 Formato de Salida

Los archivos se guardan en:
`D:\Scrappers Normalizacion\1.1 ML\Datos de prueba\{Tienda}\`

Con el formato:
`busqueda_{término}_ciclo{número}_{YYYY-MM-DD_HH-MM-SS}.json`

## 🔄 Diferencias con Scrapers de Categorías

| Aspecto | Búsqueda | Categoría |
|---------|----------|-----------|
| URL | `/search?Ntt=término` | `/category/cat123/Nombre` |
| Selectores | `.pod`, `[data-pod]` | `[data-testid]` |
| Estructura HTML | Grid de productos | Lista de productos |
| Precios | `[data-cmr-price]` | `[data-testid="prices-cmr"]` |

## 📝 Estructura de Datos

```json
{
  "metadata": {
    "search_term": "smartphone",
    "search_name": "Smartphones",
    "total_products": 56,
    "pages_scraped": 10,
    "ciclo_number": 1
  },
  "products": [
    {
      "product_code": "143246536",
      "name": "Redmi Note 10",
      "brand": "XIAOMI",
      "card_price_text": "$449.990",
      "card_price": 449990,
      "normal_price_text": "$469.990",
      "normal_price": 469990,
      "original_price_text": "$599.990",
      "original_price": 599990,
      "product_link": "https://...",
      "search_term": "smartphone"
    }
  ]
}
```

## ⚙️ Configuración

Para agregar nuevos términos de búsqueda, editar el diccionario `BUSQUEDAS_CONTINUAS`:

```python
BUSQUEDAS_CONTINUAS = {
    "nuevo_termino": {
        "term": "laptop",  # Término a buscar
        "name": "Laptops"  # Nombre descriptivo
    }
}
```