# Restricciones de bien-formedness

## Implementadas
*(ninguna aún)*

## Planificadas
### R001 — Unicidad de niveles en Layered
Los niveles de las capas dentro de un `Layered` deben ser únicos.
- **Detectada en:** iteración 1
- **Prototipo:** research-assistant

### R002 — Summarize y Mix solo en grafos cíclicos *(descartada)*
~~Si la estructura de comunicación es lineal, no se puede usar `Summarize` ni `Mix`.~~
- **Detectada en:** iteración 4
- **Prototipo:** cvReviewer
- **ADR relacionado:** adr/002-summarize&mixReducer.md
- **Pendiente relacionado:** Mecanismos de bifurcación
- **Motivo del descarte:** Los grafos pueden ejecutarse múltiples veces con estado persistente (checkpointer de LangGraph). En ese contexto, los mensajes se acumulan entre ejecuciones aunque la estructura interna sea lineal, por lo que `Summarize` y `Mix` son igual de pertinentes en grafos lineales.

### R003 - Estructuras de comunicación unidas.
Todas las estructuras de comunciacion deben estar entrelazadas de tal forma que no haya ninguna estructura de comunicación a la que sea imposible de acceder. Algoritmo de grafos.
- **Detectada en:**  Refinamiento del generador de código.
- **Pendiente relacionado:** Mecanismos de bifurcación

### R004 - Server MCP
No puede haber distintos servidores mcp con misma url, osea el campo url debe ser único, se podría implementar en el DSL en el caso de que usasemos el url como ID pero descartamos esto para mayor legibilidad del modelo.
- **Detectada en:**  Refinamiento del generador de código.

### R005 — Unicidad del punto de inicio
Debe existir exactamente una estructura de comunicación con `isStart = true` en el sistema. Tener ninguna impide determinar el punto de entrada del grafo de comunicación; tener más de una genera ambigüedad en el flujo.
- **Detectada en:** Creación de la v0.5.0 del DSL.

### R006 — Sin arcos duplicados con condición desde el mismo origen
Dado un nodo fuente, no pueden existir dos transiciones con condición que apunten al mismo nodo destino. Dos arcos con la misma fuente y el mismo destino son semánticamente equivalentes y producen comportamiento no determinista.
- **Detectada en:** Creación de la v0.5.0 del DSL.

### R007 — Las transiciones únicas no pueden tener condición
Si desde un nodo fuente existe una única transición de salida, dicha transición no puede llevar condición. Una condición en un arco único carece de sentido porque no hay ningún otro arco alternativo al que derivar el flujo cuando la condición no se cumpla.
- **Detectada en:** Creación de la v0.5.0 del DSL.

### R008 — Compatibilidad de tipos en la condición de transición
El tipo del valor literal empleado en una condición de transición debe ser compatible con el tipo declarado del atributo referenciado. Comparar un atributo `int` con un valor `string`, o viceversa, produce una condición inevaluable en tiempo de ejecución.
- **Detectada en:** Creación de la v0.5.0 del DSL.

### R09 - Compatibilidad de transiciones.
Se puede tener una transición sin condición junto a otras transiciones con condiciones, pero tan solo una. La idea de esto es permitir un camino de else en los router, es decir, si no se cumple ni A ni B puedes ir a C. Pero si se usan varias transiciones sin condición, la entrada será invalida.
- **Detectada en:** Creación de la v0.5.1 del generador de código.

### R10 - Temperatura de los agentes
La temperatura del agente debe estar entre 0.0 y 1.0
- **Detectada en:** minor fixes de la sintáxis de la gramática del .langium