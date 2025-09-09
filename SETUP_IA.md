# 🤖 Setup IA para Normalización Retail

## 📦 Instalación Dependencias IA

```bash
pip install openai>=1.0.0
```

## 🔑 Configuración OpenAI

### 1. Obtener API Key
- Ve a https://platform.openai.com/api-keys
- Crear nueva API key
- Copiar la clave

### 2. Configurar Variables de Entorno

**Windows:**
```cmd
set OPENAI_API_KEY=tu-api-key-aqui
set LLM_ENABLED=true
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="tu-api-key-aqui"
export LLM_ENABLED="true"
```

### 3. O crear archivo `.env`:
```
OPENAI_API_KEY=tu-api-key-aqui
LLM_ENABLED=true
```

## ⚙️ Configuración del Sistema

### Activar IA en config:
```toml
# configs/config.local.toml
[llm]
enabled = true  # ← Cambiar a true
```

## 🚀 Uso

```bash
# Normalizar con IA habilitada
python -m src.cli normalize --input ./tests/data --out ./out

# Output incluirá:
# - ai_enhanced: true
# - ai_confidence: 0.95
# - fingerprint: hash único para BD
# - refined_attributes: datos enriquecidos
```

## 💾 Cache IA

- **Cache indefinido** para metadatos (no expira)
- **Archivo**: `out/ai_metadata_cache.json`
- **Ventaja**: Un producto se procesa con IA solo UNA vez
- **Ahorro**: 95% menos llamadas a OpenAI

## 🎯 Optimizado para Base de Datos

El output incluye campos especiales para tu BD:

```json
{
  "product_id": "abc123...",
  "fingerprint": "def456...",  // 🔑 Para matching inter-retail
  "ai_enhanced": true,
  "ai_confidence": 0.95,
  "processing_version": "v1.1",
  "attributes": {
    "capacity": "256GB",       // Enriquecido por IA
    "color": "negro",         // Normalizado
    "screen_size": "6.7"      // Extraído
  }
}
```

## 💰 Costos OpenAI Estimados

- **gpt-4o-mini**: ~$0.00015 por producto
- **1000 productos**: ~$0.15 USD
- **Con cache**: solo primera vez

## 🔍 Auditoría

Cada producto incluye metadatos para auditar calidad:
- `ai_enhanced`: Si fue procesado con IA
- `ai_confidence`: Confianza del modelo (0-1)
- `processing_version`: Versión del pipeline