Configuration

Base de Datos (psycopg2)
- `DB_HOST` (ej. `127.0.0.1` o IP/hostname)
- `DB_PORT` (por defecto `5432`)
- `DB_NAME` (por defecto `postgres`)
- `DB_USER` (usuario válido)
- `DB_PASSWORD` (contraseña)
- `DB_POOL_SIZE` (por defecto `5`)

LLM (por defecto ON)
- `LLM_ENABLED` (`true|false`) — activado por defecto por configuración interna; defínelo explícitamente en `.env`.
- `OPENAI_API_KEY` — requerido en producción para GPT‑5.
- `OPENAI_MODEL` — opcional; el router usa `gpt-5-mini` con fallback a `gpt-5`.

Archivos de Configuración
- `configs/taxonomy_v1.json`: taxonomía de categorías (fallback si BD no está disponible)
- `configs/brand_aliases.json`: aliases de marca para inferencia
- `configs/thresholds.toml`: umbrales y parámetros complementarios
- `configs/gates.yaml`: políticas de evolución de esquemas

Buenas Prácticas
- No versionar credenciales ni contraseñas.
- Usar `.env` sólo en desarrollo; variables reales en secretos/CI/CD.
- Preferir `src/unified_connector.py` en vez de conectores legacy.
