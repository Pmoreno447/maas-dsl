## Estado

**Deprecado.** Sustituido por el ADR 011.

La decisión original de insertar el nodo al inicio del grafo se basaba en una asunción implícita de ejecuciones independientes que dejó de ser válida tras la incorporación del soporte para persistencia mediante checkpointer.

# Pendiente — Implementación de Summarize y Mix en el generador

## Descripción del problema

En LangGraph, el mecanismo habitual para resumir el historial de mensajes consiste en introducir un **nodo dedicado** que, cuando el historial supera un umbral, invoca un LLM para condensarlo y reemplazar los mensajes antiguos por el resumen generado.

Sin embargo, la introducción de este nodo plantea dos problemas no resueltos en el estado actual del generador:

### 1. Ambigüedad de posición en grafos con múltiples estructuras

El metamodelo permite combinar varias estructuras de comunicación en un mismo sistema. En ese escenario no está claro en qué punto del grafo debe insertarse el nodo de resumen: ¿al inicio de cada estructura, entre estructuras, o una única vez al inicio del grafo global? Esta ambigüedad impide generar el nodo de forma automática y correcta sin información adicional que el metamodelo actual no proporciona.

### 2. El resumen solo tiene sentido en grafos cíclicos

El mecanismo de resumen está concebido para sistemas donde el historial de mensajes crece de forma indefinida, lo cual únicamente ocurre en grafos con ciclos. En un grafo lineal como el patrón *layered*, el historial tiene un tamaño acotado y predecible, por lo que el resumen no aporta valor. Esto conecta directamente con la limitación ya identificada de la ausencia de bifurcaciones en el metamodelo: sin soporte para grafos cíclicos, el summarize carece de utilidad práctica en los sistemas actualmente generables.

## Solución adoptada temporalmente

De momento se opta por insertar el nodo de resumen **al inicio del grafo**, antes del primer nodo funcional. Aunque esta posición no tiene sentido semántico en grafos lineales, es la opción más limpia desde el punto de vista del generador, ya que:

- Es un punto de inserción unívoco e independiente de la estructura de comunicación.
- No requiere información adicional en el metamodelo.
- Cuando el generador incorpore soporte para grafos cíclicos y bifurcaciones, esta posición podrá revisarse sin cambios rupturistas en el resto del generador.

Se descarta el uso de wrappers sobre el reducer del estado como solución alternativa por no ser una aproximación limpia ni alineada con los patrones recomendados por LangGraph.