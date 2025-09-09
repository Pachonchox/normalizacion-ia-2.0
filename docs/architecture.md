# Diseño de arquitectura

```mermaid
flowchart LR
  A[JSONs de scraping] --> B[Ingesta]
  B --> C[Validación entrada]
  C --> D[Normalización & Enriquecimiento]
  D --> E[Categorización (Taxonomía v1)]
  E --> F[Fingerprint & Cache]
  F --> G[Matching (blocking + similitud)]
  G --> H[Persistencia & Reporte]
  subgraph Observabilidad
    I[Logging estructurado]
    J[Métricas y costos]
  end
  D --> I
  G --> J
```
