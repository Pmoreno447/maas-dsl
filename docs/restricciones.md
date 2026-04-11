# Restricciones de bien-formedness

## Implementadas
*(ninguna aún)*

## Planificadas
### R001 — Unicidad de niveles en Layered
Los niveles de las capas dentro de un `Layered` deben ser únicos.
- **Detectada en:** iteración 1
- **Prototipo:** research-assistant

### R002 — Summarize y Mix solo en grafos cíclicos
Si la estructura de comunicación es lineal, no se puede usar `Summarize` ni `Mix`.
- **Detectada en:** iteración 4
- **Prototipo:** cvReviewer
- **ADR relacionado:** adr/002-summarize&mixReducer.md
- **Pendiente relacionado:** Mecanismos de bifurcación
