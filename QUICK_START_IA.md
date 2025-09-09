# 🚀 QUICK START - IA ACTIVADA

## ✅ Configuración Completada

Tu API Key OpenAI está configurada y la IA está activada:
- ✅ Archivo `.env` creado con tu API Key
- ✅ `LLM_ENABLED=true` configurado
- ✅ `config.local.toml` actualizado

## 🧪 Probar el Sistema

### 1. Instalar OpenAI (si no está instalado)
```bash
pip install openai>=1.0.0
```

### 2. Ejecutar Pipeline con IA
```bash
python -m src.cli normalize --input ./tests/data --out ./out
```

## 🔍 Qué Esperar

### Primera Ejecución (Cache Frío)
```
🤖 Enriqueciendo con IA: iPhone 16 Pro Max 256GB Titanio Negro Liberado...
✅ Cache IA guardado: def45678...
🤖 Enriqueciendo con IA: Smartphone Galaxy A26 5G 128GB 6.7" Negro...  
✅ Cache IA guardado: abc12345...
[OK] Normalized 2 items → ./out/normalized_products.jsonl
```

### Segunda Ejecución (Cache Hit)
```
⚡ Cache IA hit: iPhone 16 Pro Max 256GB Titanio Negro...
⚡ Cache IA hit: Smartphone Galaxy A26 5G 128GB 6.7"...
[OK] Normalized 2 items → ./out/normalized_products.jsonl
```

## 📊 Verificar Resultados

Revisar el archivo de salida:
```bash
head -2 out/normalized_products.jsonl | jq .
```

Deberías ver campos enriquecidos con IA:
```json
{
  "ai_enhanced": true,
  "ai_confidence": 0.95,
  "fingerprint": "def456...",
  "attributes": {
    "capacity": "256GB",
    "color": "negro", 
    "screen_size": "6.7",
    "network": "5G"
  }
}
```

## 📁 Archivos Creados

- 📄 `.env` - Variables de entorno (NUNCA commitear)
- 📄 `.gitignore` - Excluye archivos sensibles
- 📁 `out/ai_metadata_cache.json` - Cache IA indefinido
- 📄 `out/normalized_products.jsonl` - Productos enriquecidos

## 💰 Costos Estimados

- **Productos de prueba (2 items)**: ~$0.0003 USD
- **1000 productos reales**: ~$0.15 USD  
- **Cache indefinido**: Solo primera vez por producto único

¡El sistema está listo para procesar datos con IA de máxima calidad! 🎯✨