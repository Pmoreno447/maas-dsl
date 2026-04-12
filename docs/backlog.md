# Backlog

| Prioridad | Tarea | Descripción |
|---|---|---|
| 🔴 Alta | Restricciones de bien-formedness | Redactar e implementar en el validator todas las restricciones OCL identificadas. Catálogo completo en `restricciones.md`. |
| 🔴 Alta | Mecanismo de inicio y fin del grafo | El generador actualmente no tiene forma de determinar cuál es el nodo inicial y cuál es el nodo final de una estructura de comunicación. Necesario para generar correctamente los edges `START` y `END` de LangGraph. |
| 🔴 Alta | Mecanismos de bifurcación | El metamodelo no permite expresar edges condicionales entre nodos. Sin esto no es posible modelar grafos cíclicos ni flujos de control no lineales. Bloquea la implementación de Summarize/Mix y HumanInTheLoop. |
| 🔴 Alta | Agentes usan herramientas | El generador de código aun no permite usar herramientas a los agentes. |
| 🔴 Alta | Incluir selector de modelos | El generador de código asigna a los agentes el modelo gpt-5-nano. |
| 🟡 Media | Human in the Loop | Añadir al metamodelo un mecanismo para declarar puntos de interrupción en el grafo donde un humano puede revisar o modificar el estado antes de continuar la ejecución. Requiere soporte de bifurcaciones previo. |
| 🟡 Media | Summarize y Mix en el generador | Actualmente se genera el nodo de resumen pero no se conecta al grafo. Su integración completa está bloqueada por la ausencia de bifurcaciones y por la ambigüedad de posición en grafos con múltiples estructuras. Detalle en `adr/002-summarize&mixReducer.md`. |
| 🟢 Baja | Flags en el CLI | Añadir opciones `--only` y `--skip` al comando `generate` para permitir activar o desactivar la generación de módulos individuales (state, prompts, agents, graph, tools). |
| 🟢 Baja | Generar código de mecanismo MIX | Permitir tanto que se guarden los x últimos mensajes como un resumen |