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

### R003 - Estructuras de comunicación unidas.
Todas las estructuras de comunciacion deben estar entrelazadas de tal forma que no haya ninguna estructura de comunicación a la que sea imposible de acceder. Algoritmo de grafos.
- **Detectada en:**  Refinamiento del generador de código.
- **Pendiente relacionado:** Mecanismos de bifurcación

### R004 - Server MCP
No puede haber distintos servidores mcp con misma url, osea el campo url debe ser único, se podría implementar en el DSL en el caso de que usasemos el url como ID pero descartamos esto para mayor legibilidad del modelo.
- **Detectada en:**  Refinamiento del generador de código.

