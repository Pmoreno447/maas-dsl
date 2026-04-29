# Evolución del generador de código

## Metodología

El generador se desarrolla de forma incremental, siguiendo el mismo ciclo iterativo que el metamodelo. Cada módulo generado se valida contra el prototipo correspondiente. Los módulos marcados como parciales son funcionales para los casos cubiertos, pero no implementan la totalidad de las construcciones del metamodelo.

## Módulos implementados

| Módulo | Archivo generado | Estado | Versión metamodelo |
|---|---|---|---|
| Prompts | `prompt.py` | ✅ Completo | v5 |
| Configuración | `.env.template` + `config.py` | ✅ Completo | v5 |
| Estado | `state.py` | ✅ Completo | v5 |
| Agentes | `agents.py` | ✅ Completo | v5 |
| Grafo | `graph.py` | 🟡 Parcial | v5 |
| Tools | `tools/` | ✅ Completo | v5 |
| Tools | `langgraph.json` | ✅ Completo | v5 |
| Tools | `checkpointer.py` | ✅ Completo | v5 |

---

## Iteración 1 — MVP del generador

Primera iteración del generador de código sobre el metamodelo v4. El objetivo de esta iteración es producir código ejecutable para el patrón de comunicación *layered*, cubriendo los casos más comunes sin abordar aún la totalidad de las construcciones del metamodelo.

### Módulos generados

**`prompt.py`**
Generación completa sin incidencias. Al tratarse de una proyección directa de los `Profile` del modelo a constantes de texto Python, no presenta complejidad técnica relevante.

**`state.py`**
Generación funcional con soporte para los mecanismos de mensajes `none` y `trim`. El mecanismo `summarize` genera el nodo de resumen pero no lo integra en el grafo, ya que su posición en sistemas con múltiples estructuras de comunicación es ambigua, y carece de utilidad práctica en grafos lineales al no haber riesgo de crecimiento indefinido del historial. Se optó por generarlo al inicio del archivo como solución provisional, a la espera de que el generador incorpore soporte para grafos cíclicos, bifurcaciones y mezcla de structuras de comunicación, per de momento solo con una implementación. básica de layered no tiene sentido implementar esto en el generador. Para más detalle ver [`adr/002-summarize&mixReducer.md`](./adr/002-summarize&mixReducer.md).

**`.env.template` + `config.py`**
Se genera un `.env.template` con los valores definidos en el metamodelo (como `MAX_TOKENS` o `MAX_MESSAGES`) y con las API keys vacías para que el usuario las complete. El `config.py` centraliza la carga del entorno mediante `load_dotenv()` y expone las variables como constantes Python importables desde cualquier módulo, evitando llamadas dispersas a `os.getenv`. La apikey de los modelos usados están hardcodeadas en el generador de momento, por lo que faltaría hacer que en función del modelo importe un apikey u otra.

**`agents.py`**
Generación funcional para agentes sin herramientas. Produce los esquemas de salida estructurada (`BaseModel` + `Field`) a partir de las referencias `stateUpdate` del agente, los modelos con sus parámetros de configuración, y los nodos del grafo con inyección de contexto desde `stateContext`. La generación de agentes con herramientas queda pendiente para la siguiente iteración.

**`graph.py`**
Generación funcional para la estructura de comunicación `Layered`. El algoritmo de ordenación de capas se basa en las referencias `next` entre `Layer`, sin depender del atributo `level`, lo que lo hace más robusto ante modelos mal ordenados. Incluye un bloque de ejecución provisional para facilitar las pruebas durante el desarrollo. Ver [`adr/004-generadorEdges.md`](./adr/004-generadorEdges.md).

### Decisiones y limitaciones de esta iteración

- **Mix descartado:** el mecanismo de mensajes `mix` queda fuera del alcance de esta iteración. Su implementación afectaría a cómo los agentes reciben el contexto y añadiría complejidad prematura. Ver [`adr/002-summarize&mixReducer.md`](./adr/002-summarize&mixReducer.md) y [`backlog.md`](./backlog.md).
- **Selector de modelos no implementado:** todos los agentes generan con `gpt-5-nano` por defecto. La selección del modelo según el atributo `model` del agente (`gpt`, `claude`, `ollama`) queda pendiente.
- **Herramientas no implementadas:** la vinculación de herramientas (`PythonTool`, `MCPTool`, `EndPointTool`) a los agentes queda pendiente.
- **Solo estructura Layered:** la combinación de múltiples estructuras de comunicación en un mismo sistema queda pendiente. Ver [`adr/004-generadorEdges.md`](./adr/004-generadorEdges.md).
- **Calidad del código generado:** quedan pendientes mejoras como extraer las descripciones de los campos de `structured output` a variables reutilizables, o deduplicar la definición del modelo cuando varios agentes usan el mismo.

### Cambios menores en el metamodelo motivados por el generador

Durante el desarrollo del generador se detectó la necesidad de los siguientes atributos adicionales en el metamodelo:
- `maxMessages` en `Trim` y `Mix`, necesario para parametrizar el reducer.

### Validación de la iteración

Para validar el generador se utilizó el modelo [`examples/cvReviewer.mad`](../examples/cvReviewer.mad), que cubre las construcciones actualmente soportadas. El código generado a partir de este modelo se adjunta en [`examples/cvReviewer/generated/`](../examples/cvReviewer/generated/) y fue ejecutado satisfactoriamente.

Las construcciones validadas en esta iteración son:

- **Mecanismo de mensajes:** `none`, `trim` y `summarize`, comprobando que el reducer y el nodo se generan en el orden correcto respecto a la clase `State`.
- **Atributos del estado:** los tres tipos soportados por el metamodelo (`string`, `int`, `boolean`), verificando que se mapean correctamente a los tipos Python equivalentes (`str`, `int`, `bool`).
- **Structured outputs:** generación de esquemas `BaseModel` con `Field` a partir de las referencias `stateUpdate` de los agentes, incluyendo la descripción de cada campo.
- **Inyección de contexto:** generación del bloque `HumanMessage` con los campos del estado referenciados en `stateContext` de cada agente.
- **Estructura de comunicación Layered:** generación correcta de los edges `START → capa1 → ... → capaN → END` a partir de las referencias `next` entre capas.

**Referencias en el repositorio.**

- Tag: `v0.4.1`

---

## Iteración 2 — Selector de modelos, configuración por provider y agentes con herramientas

Segunda iteración del generador sobre el metamodelo v4. Tras la iteración 1, que produjo un MVP ejecutable para la estructura `Layered` con agentes sin herramientas y un único provider hardcodeado, el objetivo de esta iteración es cerrar los módulos `agents.py`, `.env.template` + `config.py` y `tools/` para que el código generado represente agentes reales capaces de interactuar con herramientas MCP y Python. Con esto, el generador pasa de producir pipelines puramente conversacionales a producir sistemas multi-agente funcionales en el sentido práctico del término.

### Módulos generados

**`agents.py`**
Generación completa para los tres casos que cubre el metamodelo actual: agentes sin herramientas (nodo síncrono, con o sin structured output), agentes con herramientas y sin `stateUpdate` (nodo `async` con while-loop que sale por mensajes libres) y agentes con herramientas y `stateUpdate` (nodo `async` con while-loop, `tool_choice="required"` y el `BaseModel` de salida bindeado como tool terminal). El patrón de `BaseModel`-como-tool, junto con el bucle interno al nodo, permite combinar tool-calling y salida estructurada sin ramificar el grafo ni duplicar llamadas al modelo. Ver [`adr/009-baseModelComoToolYWhileLoop.md`](./adr/009-baseModelComoToolYWhileLoop.md). El generador emite además un diccionario `_tools_by_name` a nivel de módulo para despachar las tool calls por nombre, y un bloque `try/except` alrededor de `tool.ainvoke` para que los errores de las herramientas en runtime se traduzcan en `ToolMessage` informativos en vez de hacer caer el grafo.

**`.env.template` + `config.py`**
El generador deja de asumir OpenAI como único provider. A partir del atributo `provider` de cada agente deriva la variable de entorno correspondiente (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`) y la incluye tanto en el `.env.template` como en el `config.py`, sin duplicados. El mismo mecanismo se aplica a los servidores MCP: cada `apiKeyName` declarado en un `mcpServer` se añade al bloque de variables si el servidor la requiere. Ver [`adr/005-modelosPorProvider.md`](./adr/005-modelosPorProvider.md).

**`tools/`**
Nuevo módulo en esta iteración. El generador produce `tools/mcpClients.py`: un único `MultiServerMCPClient` con una entrada por cada `mcpServer` declarado, inicializado a nivel de módulo con `asyncio.run(_client.get_tools())`, y una variable por cada nombre de tool listado en el `.mad`. La resolución de cada nombre contra el catálogo devuelto por el servidor se hace con un helper `_get_tool` que lanza un `RuntimeError` con mensaje diagnóstico y el catálogo real disponible, de forma que cualquier typo, renombrado en el servidor o conexión degradada se detecta al importar el módulo, antes de arrancar el grafo y sin consumir tokens hasta el punto del fallo. Ver [`adr/008-failFastMcpToolLookup.md`](./adr/008-failFastMcpToolLookup.md). Las herramientas Python se importan directamente desde el `modulePath` declarado en el `.mad`, sin generación intermedia: es responsabilidad del usuario implementar la función decorada con `@tool`.

**`graph.py`**
El `main` pasa a ser siempre `async def main()` con `asyncio.run(main())` y `await graph.ainvoke(...)`, independientemente de si algún agente usa tools. Un grafo de LangGraph es asíncrono si cualquiera de sus nodos lo es, por lo que el generador no necesita detectar la condición: el coste de `asyncio.run` sobre un `main` sin `await` reales es despreciable y simplifica el generador.

### Decisiones y limitaciones de esta iteración

- **Reemplazo de `MCPTool` por `MCPServer`:** al preparar el generador de tools se detectó que el diseño original de `MCPTool` (una tool MCP por declaración) forzaba al generador a agrupar por URL para instanciar un único cliente MCP, con los problemas de coherencia que eso acarreaba (dos declaraciones con la misma URL pero distintas `apiKeyName`, por ejemplo). Se optó por modelar el servidor MCP como entidad de primera clase y listar los nombres de tools que expone como strings, lo cual refleja mejor la realidad del protocolo y elimina la ambigüedad. Ver [`adr/007-toolNameEnMcpTool.md`](./adr/007-toolNameEnMcpTool.md).
- **Eliminación de `EndPointTool`:** la construcción se retira del metamodelo al no poderse generar código útil a partir de su información declarativa (URL + método). Los casos que antes cubría se modelan ahora como `PythonTool`. Ver [`adr/006-eliminacionEndPointTool.md`](./adr/006-eliminacionEndPointTool.md).
- **Structured output y tool-calling combinados mediante `BaseModel` como tool:** LangChain no permite encadenar `bind_tools` y `with_structured_output` sobre el mismo modelo. Se adopta el patrón de bindear el schema de salida como una tool más, reconocida por el while-loop interno del nodo como señal de terminación. Ver [`adr/009-baseModelComoToolYWhileLoop.md`](./adr/009-baseModelComoToolYWhileLoop.md).
- **Bucle interno al nodo en vez de bifurcación en el grafo:** se descartó emitir un `ToolNode` y una `conditional_edge` por cada agente con tools, porque introducen nodos y edges sintéticos que no están en el `.mad` y complican el generador de edges. El bucle queda confinado al nodo, el grafo sigue describiendo únicamente la coreografía entre agentes.

### Cambios menores en el metamodelo motivados por el generador

Durante esta iteración el DSL ha recibido cambios ligeros, adaptaciones necesarias para que el generador pudiera producir código correcto, no actualizaciones rupturistas, por ello mismo no se detallarán en `evolucionMetamodelo.md`:

- Adición del atributo `apiKeyName` en `MCPServer`, para que el generador sepa qué variable de entorno hay que inyectar en la URL del servidor en vez de intentar derivarla del dominio.
- Reemplazo de `MCPTool` por `MCPServer` con una lista de nombres de tools como strings. Ver [`adr/007-toolNameEnMcpTool.md`](./adr/007-toolNameEnMcpTool.md).
- Eliminación de `EndPointTool` del metamodelo. Los casos cubiertos antes por esta construcción pasan a modelarse como `PythonTool` escrito a mano por el usuario. Ver [`adr/006-eliminacionEndPointTool.md`](./adr/006-eliminacionEndPointTool.md).

### Validación de la iteración

Para validar el generador se utilizaron dos modelos. [`examples/mcpToolsExample/mcpToolsExample.mad`](../examples/mcpToolsExample/mcpToolsExample.mad) cubre el caso de agentes con herramientas MCP (`tavily_search`, `tavily_extract`) y Python (`prueba`) sin `stateUpdate`, validando el bucle async con salida por mensajes libres. [`examples/mcpToolsStateExample/mcpToolsExample.mad`](../examples/mcpToolsStateExample/mcpToolsExample.mad) cubre además el caso con `stateUpdate`, validando el patrón `BaseModel`-como-tool, el `tool_choice="required"` y la extracción de argumentos de la tool terminal como salida estructurada. Ambos modelos se generaron y ejecutaron con éxito, invocando realmente los servidores MCP y produciendo el estado esperado.

Las construcciones validadas en esta iteración son:

- **Selector de modelos por provider:** generación de `init_chat_model("provider:model", ...)` con los atributos `temperature`, `maxToken`, `timeOut`, `maxRetries` y `base_url` (este último solo para Ollama) correctamente propagados desde el `.mad`.
- **Variables de entorno por provider y por MCP server:** deduplicación de keys cuando varios agentes comparten provider y cuando varios servidores MCP comparten `apiKeyName`.
- **Tools MCP:** inicialización sincrónica en el import de `tools/mcpClients.py`, resolución fail-fast con mensaje diagnóstico y bindeo correcto a los agentes que las declaran.
- **Tools Python:** importación desde el `modulePath` declarado y bindeo a los agentes correspondientes.
- **Agentes con tools sin `stateUpdate`:** nodo `async`, while-loop que sale por mensajes libres cuando el modelo deja de pedir tools.
- **Agentes con tools + `stateUpdate`:** nodo `async`, while-loop con doble pasada sobre `response.tool_calls` (primero la tool terminal, luego el resto), `tool_choice="required"` que impide al modelo salir sin llamar a la tool de cierre, y extracción de `args` de la tool terminal como salida estructurada.
- **Error handling de tools:** los fallos de `tool.ainvoke` en runtime producen `ToolMessage` con mensaje de error en vez de hacer caer el grafo.

### Cierre de la iteración

Con esta iteración el generador ya es capaz de producir **agentes reales** que interactúan con herramientas MCP y Python, combinando tool-calling con salida estructurada según lo describa el `.mad`. La próxima iteración se centrará en el grafo, pero antes se abordará el trabajo sobre **edges**: introducir bifurcaciones en el metamodelo es el paso que desbloquea la integración real del nodo de resumen en el grafo (hasta ahora generado pero no conectado, ver `adr/002-summarize&mixReducer.md`) y que, combinado con la mezcla de estructuras de comunicación, permitirá modelar grafos cíclicos con condición de terminación.

**Referencias en el repositorio.**

- Tag: `v0.4.2`

---

## Iteración 3 — Bifurcaciones, estructura `Centralized`, mezcla de subgrafos y primer ejemplo real

Tercera iteración del generador sobre el metamodelo v4. Tras la iteración 2, que cerró agentes y herramientas, esta iteración se centra en el módulo `graph.py`: introducir bifurcaciones condicionales en el DSL, completar la estructura `Centralized` y permitir la mezcla de varias estructuras de comunicación en un mismo sistema. Como cierre, se valida todo el conjunto sobre un caso de uso realista de atención al cliente, lo que motivó dos mejoras adicionales sobre el generador.

### Módulos generados

**`graph.py` — bifurcaciones**
El generador soporta ahora transiciones condicionales entre estructuras de comunicación. Las comparaciones disponibles dependen del tipo del atributo del estado: `int` y `string` admiten igualdad, mayor y menor (en `string` el orden lexicográfico es de utilidad limitada, pero se mantiene por uniformidad sintáctica del DSL); `bool` compara contra `true` o `false`. Estas transiciones se materializan como `add_conditional_edges` con un router por estructura origen, que enruta hacia el destino correspondiente según el valor del atributo evaluado.

**`graph.py` — un subgrafo por estructura de comunicación**
Se tomó la decisión de que cada estructura de comunicación genere su propio subgrafo, con `START` y `END` propios, en lugar de aplanarlo todo sobre el grafo principal. Esto desacopla la generación de cada estructura de su posición dentro del grafo general: el generador de bifurcaciones solo ve nodos opacos que se conectan entre sí, y el generador de cada estructura no necesita saber dónde encaja. Ver [`adr/010-estadoPorSubgrafo.md`](./adr/010-estadoPorSubgrafo.md).

**`graph.py` — estructura `Layered`**
Sin complejidad adicional respecto a la iteración 1, más allá de adaptarla al nuevo esquema de subgrafo independiente.

**`graph.py` — estructura `Centralized`**
El reto principal fue cómo modelar el coordinador en el metamodelo. La intención inicial era reutilizar la clase `Agent` mediante una referencia que marcase a uno como coordinador, pero `Agent` lleva consigo `stateContext`, `stateUpdate`, `tools` y otros atributos que no aplican al nodo orquestador (que se genera de forma distinta), aunque sí necesitamos del coordinador su prompt, el modelo y la temperatura. Se evaluaron tres alternativas:

- Reutilizar `Agent` y que el generador detecte el rol y descarte los atributos no aplicables. Descartada por opacidad: el modelo declararía información que el generador ignora silenciosamente.
- Reutilizar `Agent` con restricciones OCL que prohíban los atributos sobrantes y dejar el contexto del coordinador en manos del usuario. Descartada por la sobrecarga de añadir más OCL y porque delegar el contexto al usuario abre la puerta a coordinadores poco efectivos.
- Introducir una clase `Coordinator` independiente. La opción más limpia conceptualmente sería que `Agent` y `Coordinator` heredasen de una entidad común, pero hacerlo en este punto rompía partes del generador. Se optó por una clase nueva sin herencia: introduce algo de acoplamiento, pero a cambio el generador puede inyectar automáticamente como contexto del coordinador todos los atributos del estado que los agentes del cluster escriben, sin que el usuario tenga que declararlo.

**`graph.py` — mezcla de estructuras de comunicación**
La integración de varios subgrafos en el grafo principal se implementó sin incidencias. Es en este punto donde el generador emite los routers que materializan las bifurcaciones del DSL. La interfaz entre el generador del grafo principal y los generadores de cada subgrafo es una función `build_<nombre>()` que devuelve el subgrafo compilado, de modo que añadir nuevas estructuras de comunicación en el futuro no requiere tocar el generador principal.

### Decisiones y limitaciones de esta iteración

- **Subgrafo por estructura en vez de grafo aplanado:** desacopla la generación de bifurcaciones de la de cada estructura y mejora la legibilidad del código generado al hacer explícita la jerarquía. Ver [`adr/010-estadoPorSubgrafo.md`](./adr/010-estadoPorSubgrafo.md).
- **`Coordinator` como clase independiente:** se prefirió frente a la herencia para no romper el generador existente. El acoplamiento introducido es tolerable y, a cambio, el generador puede asignar el contexto del coordinador automáticamente a partir de los `stateUpdate` de los agentes del cluster.
- **Preámbulo de enrutamiento generado:** el código emitido para el coordinador era semánticamente correcto pero poco efectivo en la práctica (el modelo entraba en bucles delegando varias veces sobre el mismo problema). El generador añade ahora un preámbulo fijo al prompt del coordinador con la lista de agentes disponibles, las reglas de enrutamiento y la indicación de que los campos del estado que recibe han sido escritos por los especialistas. El prompt del usuario se concatena tras este preámbulo, manteniéndose responsable únicamente de la lógica de dominio.
- **Soporte para LangSmith:** durante la depuración del coordinador se utilizó LangSmith Studio para inspeccionar las trazas en ejecución. Aunque su soporte estaba previsto en una iteración posterior del backlog, se adelantó por conveniencia: el generador emite ahora las variables de entorno (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`) y el correspondiente bloque en `.env.template`.

### Validación de la iteración

Para validar el generador se construyó un nuevo ejemplo realista, [`examples/customerServiceMas/customerServiceMas.mad`](../examples/customerServiceMas/customerServiceMas.mad), que modela un sistema de atención al cliente con la siguiente lógica:

1. Validación de la entrada: un agente comprueba si el mensaje es una solicitud real y si el ID de pedido existe (usando una `pythonTool`).
2. Si la entrada no es válida, el grafo termina con una respuesta al cliente; si es válida, otro agente extrae los datos relevantes del pedido.
3. Una estructura `Centralized` delega la resolución del problema en uno de cuatro especialistas (envío, pago, producto, generalista) y, una vez resuelto, un último agente compone la respuesta final al cliente.

Este modelo cubre todas las construcciones introducidas en la iteración: bifurcaciones (transiciones condicionales sobre `isValid`), mezcla de estructuras de comunicación (`Layered` + `Centralized`) y agentes con herramientas dentro de la estructura centralizada. El código generado se ejecutó satisfactoriamente sobre los tres casos de prueba previstos: mensaje no serio, mensaje válido con ID inexistente y mensaje válido con ID correcto.

### Cierre de la iteración

Con esta iteración el generador cubre el módulo `graph.py` de forma completa para las estructuras `Layered` y `Centralized`, incluyendo bifurcaciones y la mezcla de varias estructuras dentro de un mismo sistema. Las próximas iteraciones se centrarán en las estructuras `SharedMessagePool` y `Decentralized`, así como en las mejoras pendientes sobre la calidad del código generado.


- Tag: `v0.5.1`

## Iteración 4 — Persistencia, integración con LangSmith Studio, `requirements.txt` y mensajes de progreso por nodo

Cuarta iteración del generador sobre el metamodelo v5. El objetivo es que el sistema multi-agente generado sea **desplegable end-to-end**: que persista su estado entre ejecuciones, se observe desde LangSmith Studio, se construya con `langgraph build` sin pasos manuales y exponga al frontend tanto los tokens del modelo como mensajes de progreso por nodo. El metamodelo expone tres opciones de persistencia (`InMemorySaver`, `PostgreSaver`, `MongoDBSaver`); `none` se deja sin tratamiento específico porque equivale al comportamiento por defecto de `InMemorySaver`.

### Módulos generados

**`checkpointer.py` (nuevo)**
Módulo dedicado que expone una función `generate_checkpointer()` envuelta como *context manager*. Su contenido depende del subtipo de persistencia: `InMemorySaver` (síncrono, sin conexión externa), `AsyncPostgresSaver` (asíncrono, con `AsyncConnection` de `psycopg` y llamada a `setup()` para crear las tablas) o `MongoDBSaver`. La conexión se parametriza vía `DB_URI`.

**`langgraph.json` (nuevo `jsonGenerator.ts`)**
Antes generado a mano. En esta iteración se añade `jsonGenerator.ts`, que emite el `langgraph.json` con el campo `checkpointer` apuntando a `./checkpointer.py:generate_checkpointer` y la entrada del grafo. Esto es lo que habilita además la integración con **LangSmith Studio**: arrancar `langgraph dev` con este JSON ya correcto permite inspeccionar trazas y *threads* sin configuración adicional.

**`.env.template` + `config.py`**
Cuando la persistencia requiere conexión externa se añade el bloque `# Configuración de la base de datos` con la variable `DB_URI`, y se expone como constante en `config.py`. Para `InMemorySaver` no se inyecta nada.

**`requirements.txt` (nuevo)**
El generador emite directamente el `requirements.txt`, eliminando el paso manual con `pipreqs`. Como el generador conoce exactamente qué imports va a producir, la lista se construye uniendo un núcleo estático (`langgraph`, `langchain`, `langchain-core`, `python-dotenv`, `pydantic`, `typing-extensions`, `langsmith`) con las dependencias condicionales: el paquete por provider de cada agente o coordinator (`langchain-openai`, `langchain-anthropic`, `langchain-google-genai`, `langchain-ollama`), `langchain-mcp-adapters` si hay servidores MCP, y los paquetes de checkpoint y driver según el tipo de persistencia (`langgraph-checkpoint-postgres` + `psycopg[binary]` o `langgraph-checkpoint-mongodb` + `pymongo`). El `summarize` del reducer se trata como caso especial porque arrastra `tiktoken` y `langchain-openai` aunque ningún agente sea de OpenAI.

**`agents.py` — mensajes de progreso por nodo (`statusMessage`)**
Se añade al metamodelo el atributo opcional `statusMessage` en `Agent`, una cadena estática que el frontend puede mostrar como indicador de la fase actual (estilo "🔎 Buscando en internet…" o "✍️ Resumiendo…" de ChatGPT). Cuando algún agente lo declara, el generador emite el import `from langgraph.config import get_stream_writer` y, al inicio del nodo correspondiente, una llamada `get_stream_writer()({"status": "<mensaje>"})`. El runtime lo expone como evento `custom` en el endpoint `POST /runs/stream`, que el cliente recibe pidiendo `stream_mode=["messages","custom"]`. Si ningún agente lo declara, ni el import ni la llamada se generan.

### Decisiones y limitaciones de esta iteración

- **Checkpointer en archivo aparte, no en `builder.compile()`:** la primera implementación pasaba el checkpointer directamente a `builder.compile(checkpointer=...)`. Esto compila sin error y `setup()` crea las tablas, pero `langgraph dev` (runtime `langgraph_runtime_inmem`) descarta cualquier checkpointer pasado por código y nunca escribe en la base de datos — fallo silencioso, documentado como bug abierto en LangGraph (#5790). La solución adoptada es declararlo en `checkpointer.py` y referenciarlo desde `langgraph.json`, que el runtime sí respeta.

- **`AsyncPostgresSaver` con `AsyncConnection` explícita:** `PostgresSaver.from_conn_string()` devuelve un `_GeneratorContextManager`, no el saver, por lo que llamar a `.setup()` directamente lanza `AttributeError`. El generador instancia el saver con una `AsyncConnection` ya abierta y delega el cierre al `finally`.

- **Validación caja-negra contra el contenedor de DB:** dado que el fallo principal era silencioso, la validación se hizo inspeccionando colecciones/tablas con `mongosh` y `psql`. Comandos en [`docs/comandosCheckpointDB.md`](./comandosCheckpointDB.md).

- **Convención de DB por saver:** `AsyncPostgresSaver` usa la DB de `DB_URI`; `MongoDBSaver` ignora la DB de la URI y crea siempre `checkpointing_db` con colecciones `checkpoints` y `checkpoint_writes`. Esta diferencia indujo inicialmente a pensar que MongoDB no persistía cuando sí lo hacía.

- **Streaming token a token sin cambios en el generador:** la integración con Studio reveló que el streaming token a token ya se cumplía sin tocar el código emitido. Como los nodos llaman a un modelo creado con `init_chat_model(...)`, LangGraph engancha el callback de streaming de LangChain por debajo y la API emite eventos `messages/partial` cuando el cliente pide `stream_mode=["messages"]`. El único requisito adicional es activar `stream_subgraphs: true` cuando los agentes viven dentro de un subgrafo, ya que de lo contrario los chunks no burbujean al SSE.

- **`statusMessage` como cadena estática y no plantilla:** se descartó hacer el atributo interpolable contra el estado para no obligar al generador a parsear placeholders y para mantener la semántica clara — `statusMessage` indica la fase del nodo, no el contenido del mensaje al usuario, que sigue saliendo como `messages/partial`.

### Validación de la iteración

Se introduce el modelo [`examples/bdTester/bdTester.mad`](../examples/bdTester/bdTester.mad), minimalista a propósito (dos agentes en `Layered`), variando el atributo `persistence` entre las tres opciones soportadas y declarando un `statusMessage` por agente. Para cada configuración de persistencia se ejecuta el grafo contra los contenedores Docker de Postgres y Mongo y se comprueba el incremento de checkpoints con consultas directas al contenedor. Los `statusMessage` se validan lanzando runs desde `POST /runs/stream` con `stream_mode=["messages","custom"]` y comprobando la aparición de los eventos `event: custom` con el dict esperado, intercalados con los `messages/partial` del LLM.

Construcciones validadas en esta iteración:

- Generación condicional de `checkpointer.py` y de la variable `DB_URI` según el subtipo de persistencia.
- Carga del checkpointer desde `langgraph.json` por `langgraph dev`, verificada con conteos directos en Postgres y MongoDB.
- `requirements.txt` reproducible desde el modelo, sin escaneo de imports.
- Streaming token a token vía `messages/partial` sobre la API de `langgraph dev`, con `stream_subgraphs: true` cuando aplica.
- Eventos `custom` por nodo emitidos a través de `get_stream_writer()` cuando el agente declara `statusMessage`.

### Cierre de la iteración

Con esta iteración el código generado pasa a ser desplegable de extremo a extremo: persiste estado, se observa desde LangSmith Studio, se empaqueta con `langgraph build` gracias al `requirements.txt` autogenerado y expone al frontend tanto tokens del modelo como mensajes de progreso por nodo. Las próximas iteraciones se centrarán en las estructuras `SharedMessagePool` y `Decentralized` y en mejoras de calidad del código generado.

**Referencias en el repositorio.**

- Tag: `v0.5.2`

---
## Modelo de ejecución del código generado

```bash
# 1. Generar el código desde el modelo .mad
node packages/cli/bin/cli.js generate examples/cvReviewer/cvReviewer.mad -d ./examples/cvReviewer/code   

# 2. Entrar en la carpeta generada

# 3. Rellenar las API keys en el .env.template y renombrarlo
# Editar .env y añadir OPENAI_API_KEY, no es necesario definir la api_key de langsmith

# 4. Crear el entorno virtual e instalar dependencias
python3.11 -m venv venv
source venv/bin/activate

# 5. Generar el requirements.txt automáticamente
pip install pipreqs
pipreqs . --force
pip install -r requirements.txt

# 6. Ejecutar
python graph.py
```

> ⚠️ Antes de ejecutar, asegurarse de que `OPENAI_API_KEY` está definida en el `.env`. Y que se ha definido una entrada en el graph.py, hay ejemplos de entrada y salida junto al código generado.

