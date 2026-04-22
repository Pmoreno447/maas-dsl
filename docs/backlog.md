# Backlog
## Tareas pendientes
| Prioridad | Tarea | Esfuerzo | Descripción |
|---|---|---|---|
| 🔴 Alta | Mecanismos de bifurcación | Alto | El metamodelo no permite expresar edges condicionales entre nodos. Sin esto no es posible modelar grafos cíclicos ni flujos de control no lineales. Bloquea la implementación de Summarize/Mix, HumanInTheLoop y el nodo resumen. |
| 🔴 Alta | Restricciones de bien-formedness | Medio | Redactar e implementar en el validator todas las restricciones OCL identificadas. Catálogo provisional en `restricciones.md`. | 
| 🔴 Alta | Refinar generación de código de estructura `Layered` | Medio | Revisar y mejorar la generación actual de la estructura de comunicación `Layered` para asegurar corrección, legibilidad y coherencia con el resto de estructuras pendientes. |
| 🔴 Alta | Generación de código de estructura `Centralized` | Medio |Implementar en el generador la traducción de la estructura de comunicación `Centralized` (un agente coordinador que orquesta al resto) al grafo de LangGraph. |
| 🔴 Alta  | Soporte langgSmith | Bajo | El generador produce lo necesario para dar soporte a langsmith de tal forma que permita generar tanto una api como una herramienta para debuggearlo. |
| 🔴 Alta | Mezcla de distintos subgrafos (estructuras de comunicación) | Medio | Dar soporte en el generador de código para que los distintos subgrafos sean combinados.|
| 🟡 Media | Generación de código de estructura `SharedMessagePool` | Medio |Implementar en el generador la traducción de la estructura de comunicación `SharedMessagePool` (agentes que publican y consumen sobre un pool común de mensajes) al grafo de LangGraph. |
| 🟡 Media | Generación de código de estructura `Decentralized` | Medio | Implementar en el generador la traducción de la estructura de comunicación `Decentralized` (comunicación directa entre agentes sin coordinador) al grafo de LangGraph. |
| 🟡 Media | Summarize y Mix en el generador | Media | Actualmente se genera el nodo de resumen pero no se conecta al grafo. Su integración completa está bloqueada por la ausencia de bifurcaciones y por la ambigüedad de posición en grafos con múltiples estructuras. Detalle en `adr/002-summarize&mixReducer.md`. |
| 🟡 Media | Human in the Loop | Alto | Añadir al metamodelo un mecanismo para declarar puntos de interrupción en el grafo donde un humano puede revisar o modificar el estado antes de continuar la ejecución. Requiere soporte de bifurcaciones previo. |
| 🟡 Media | Segmentación de módulos por subgrafo | Medio | Refactorizar el generador para que los archivos `agents.py`, `prompt.py` y similares se dividan por estructura de comunicación cuando se mezclan varias. No afecta a la corrección del código generado, pero mejora su legibilidad. Ver [`adr/010-estadoPorSubgrafo.md`](./adr/010-estadoPorSubgrafo.md). |
| 🟢 Baja | Generar código de mecanismo MIX | Alto |Permitir tanto que se guarden los x últimos mensajes como un resumen. Combinación de `trim` y `summarize`. |
| 🟢 Baja | Flags en el CLI | Desconocido | Añadir opciones `--only` y `--skip` al comando `generate` para permitir activar o desactivar la generación de módulos individuales (state, prompts, agents, graph, tools). |

| 🟢 Baja | Estado independiente por subgrafo | Muy alto | Extender el DSL y el generador para que cada subgrafo (estructura de comunicación) tenga su propio `TypedDict`, con proyección de campos compartidos hacia el estado padre. Solo abordar si aparece un caso de uso real que lo justifique. Ver [`adr/010-estadoPorSubgrafo.md`](./adr/010-estadoPorSubgrafo.md). |


## Tareas completadas

| Prioridad | Tarea | Prioridad | Descripción |  Comentario |
|---|---|---|---|---|
| 🔴 Alta | Configuración generada | Bajo | El generador produce un `.env.template` y un `config.py`, pero las variables de API key del LLM están hardcodeadas para OpenAI tanto en el generador de configuración como en el de grafo. Debería variar según el modelo declarado en el metamodelo. | Generado el documento [Adr005](./adr/005-modelosPorProvider.md)|
| 🟡 Media | Incluir selector de modelos | Medio | El generador asigna a todos los agentes el modelo `gpt-5-nano` por defecto, ignorando el atributo `model` del agente en el metamodelo (`gpt`, `claude`, `ollama`). | . |
| 🔴 Alta | Agentes usan herramientas | Alto | El generador de código aún no permite usar herramientas a los agentes. Se decidió no implementar solo herramientas Python en esta iteración porque la generación de herramientas MCP y Python difiere radicalmente, y hacerlo por separado obligaría a descartar código al unificarlas. Se abordará todo de una vez. | Geberados los siguientes documentos [Adr006](./adr/006-eliminacionEndPointTool.md), [Adr007](./adr/007-toolNameEnMcpTool.md), [Adr008](./adr/008-failFastMcpToolLookup.md), [Adr009](./adr/009-baseModelComoToolYWhileLoop.md) |