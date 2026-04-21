# Evolución del generador de código

## Metodología

El generador se desarrolla de forma incremental, siguiendo el mismo ciclo iterativo que el metamodelo. Cada módulo generado se valida contra el prototipo correspondiente. Los módulos marcados como parciales son funcionales para los casos cubiertos, pero no implementan la totalidad de las construcciones del metamodelo.

## Módulos implementados

| Módulo | Archivo generado | Estado | Versión metamodelo |
|---|---|---|---|
| Prompts | `prompt.py` | ✅ Completo | v4 |
| Configuración | `.env.template` + `config.py` | ✅ Completo | v4 |
| Estado | `state.py` | 🟡 Parcial | v4 |
| Agentes | `agents.py` | ✅ Completo | v4 |
| Grafo | `graph.py` | 🟡 Parcial | v4 |
| Tools | `tools/` | ⬜ Pendiente | v4 |

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