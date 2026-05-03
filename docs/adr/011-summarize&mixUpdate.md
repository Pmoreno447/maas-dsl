# ADR 011 — Posición y mecanismo del nodo Summarize en el grafo generado

## Estado

Aceptado. Sustituye al ADR 002 (deprecado).

## Contexto

El metamodelo permite asociar una configuración `Summarize` al sistema, indicando que el historial de mensajes debe condensarse cuando supere un umbral de tokens. La incorporación de este mecanismo en el código generado plantea dos preguntas independientes que deben resolverse a nivel del generador, no del modelo: dónde insertar el nodo en el grafo y cómo determinar cuándo activarlo.

El ADR 002 abordó parcialmente esta cuestión optando por insertar el nodo al inicio del grafo, decisión que se justificaba por su independencia respecto a la estructura de comunicación. Tras el desarrollo del soporte para persistencia mediante checkpointer, esa decisión se ha revelado incorrecta: en sistemas conversacionales con memoria persistente, donde el grafo se ejecuta múltiples veces sobre el mismo historial acumulado, resumir al inicio condensa información que aún no ha sido generada en ese turno y deja sin condensar la conversación recién producida.

## Decisión

El nodo Summarize se inserta al final del grafo, conectado mediante un *conditional edge* desde el último nodo funcional. La condición evalúa si el número de tokens del historial supera el umbral configurado y, en ese caso, redirige al nodo de resumen antes del END. Si no se supera, el grafo termina directamente.

El conteo de tokens utiliza la librería `tiktoken` con la tokenización de OpenAI como aproximación universal, independientemente del proveedor del modelo summarizer configurado en el DSL. El modelo encargado de generar el resumen es configurable desde el modelo, igual que cualquier otro agente del sistema.

La posición del nodo y la lógica de activación condicional son responsabilidad exclusiva del generador. El usuario del DSL declara únicamente el umbral y el modelo summarizer; cómo y dónde se inserta queda completamente abstraído.

## Consecuencias

**Positivas:**

- El nodo se activa con todo el contexto generado durante el turno, lo que produce resúmenes semánticamente correctos.
- En sistemas con checkpointer, cada ejecución termina dejando el historial preparado para la siguiente, que es el comportamiento esperado en aplicaciones conversacionales.
- El conditional edge evita invocar al LLM summarizer cuando el historial no ha crecido lo suficiente, eliminando coste innecesario en producción.
- La decisión refuerza la separación de responsabilidades propia del enfoque MDD: el modelo declara el qué (quiero resumen con un umbral X), el generador resuelve el cómo (posición, condición, integración).

**Negativas:**

- La aproximación universal del conteo mediante `tiktoken` introduce un error de precisión cuando el modelo summarizer no es de OpenAI. El error en la práctica es inferior al 15% y resulta aceptable dado que el umbral es una heurística configurable.
- En grafos con bifurcaciones que contengan múltiples nodos terminales, la inserción del summarize requiere conectar el conditional edge desde todos ellos. Esta complejidad queda absorbida por el generador y no es visible en el modelo.

**Pendientes para iteraciones futuras:**

- Tokenización específica por proveedor: si en el futuro se considera necesario un conteo más preciso, se podrá introducir una capa de abstracción que seleccione el tokenizador según el provider del modelo summarizer.