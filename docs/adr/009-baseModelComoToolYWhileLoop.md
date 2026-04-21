# ADR 009 — `BaseModel` como tool y while-loop unificado para nodos con herramientas

## Contexto

Cuando un agente declara `tools` en el `.mad`, el generador debe producir
un nodo Python capaz de invocar el modelo, recibir `tool_calls`,
ejecutarlas y volver a llamar al modelo hasta que decida terminar. Si
además el agente declara `stateUpdate`, el nodo debe terminar
devolviendo una salida estructurada que actualice el `State` del grafo
(no un mensaje libre).

LangChain ofrece dos primitivas independientes sobre `init_chat_model`:

- `bind_tools([...])`: liga al modelo un conjunto de tools. La respuesta
  puede contener `tool_calls`.
- `with_structured_output(Schema)`: fuerza al modelo a devolver una
  instancia validada de un `BaseModel` (Pydantic) en vez de mensaje
  libre.

El problema central es que **estas dos primitivas no se pueden encadenar
en el mismo modelo**: `with_structured_output` envuelve el modelo en un
runnable que ya no expone `tool_calls`, y `bind_tools` deja la salida
como mensaje normal sin garantía de schema. Combinarlas naivamente
(`bind_tools(...).with_structured_output(...)`) o no funciona, o rompe
la capacidad de iterar entre tool calls.

Un agente típico del proyecto necesita ambas cosas a la vez: por
ejemplo, el `Researcher` del `mcpToolsExample` usa varias tools MCP
(`tavily_search`, `tavily_extract`, ...) y al terminar debe escribir
`research: str` en el `State`. Si solo tiene tools, no hay forma directa
de extraer una salida tipada para `stateUpdate`. Si solo tiene
structured output, no puede invocar las tools que necesita para
construir esa salida.

A esto se suma una segunda decisión sobre **la estructura del bucle de
tool-calling**. LangGraph permite modelar el flujo "modelo ↔ tools" de
dos maneras:

1. **Bifurcación a nivel de grafo**: cada nodo de modelo está conectado
   a un nodo `ToolNode`, con una `conditional_edge` que decide
   "¿hay tool_calls? → tools, si no → fin". El grafo se ramifica.
2. **Bucle interno al nodo**: el nodo es una función `async` que itera
   internamente — invoca el modelo, ejecuta tools, vuelve a invocar —
   hasta que el modelo decide terminar. El grafo no ve el bucle.

La opción 1 es idiomática en LangGraph cuando el grafo lo escribe un
humano. Pero el contexto aquí es distinto: el grafo **lo emite un
generador a partir de un metamodelo**, y el metamodelo describe el
flujo entre agentes (capas, secuencia, ...), no el flujo
modelo-tools-modelo dentro de un mismo agente. Trasladar la opción 1 al
generador obligaría a:

- Emitir un `ToolNode` por cada agente con tools.
- Emitir una `conditional_edge` que elija entre el `ToolNode` y el
  siguiente agente del flujo lógico.
- Reescribir el resto del grafo para que las edges declaradas en el
  `.mad` (capas, `next`) coexistan con estas edges sintéticas
  introducidas por el generador.

Eso ensucia el grafo generado con nodos y edges que no tienen
correspondencia con el `.mad`, complica el generador de edges (ADR 004)
y mezcla dos niveles distintos: la coreografía entre agentes (lo que el
DSL describe) con el bucle interno de un agente (un detalle de
implementación).

## Alternativas consideradas

### Alternativa A — `bind_tools` + nodo síncrono sin structured output

Generar `bind_tools([...])`, dejar que el modelo decida cuándo terminar
basándose en "no hay más `tool_calls`", y devolver el último mensaje
libre. Descartada porque pierde el `stateUpdate`: el `State` esperaba
`research: str` y recibe un `AIMessage` cuyo contenido el siguiente
agente tendría que parsear a mano.

### Alternativa B — `with_structured_output` y simular tools desde fuera

Usar solo `with_structured_output` en el modelo y expresar las tools
como nodos separados del grafo (la opción 1 de arriba). Descartada por
las razones del contexto: introduce nodos y edges sintéticos en el grafo
que no están en el `.mad` y complica el generador de edges.

### Alternativa C — Dos llamadas: primero tools, luego structured

Hacer una primera fase con `bind_tools(...)` en bucle hasta que el
modelo deje de pedir tools, y una segunda llamada al final con
`with_structured_output(...)` sobre el historial acumulado para extraer
la salida tipada. Descartada porque:

- Duplica el coste de tokens (el historial entero se reenvía al modelo
  una vez más solo para tipar la salida).
- Introduce un punto donde el modelo "resume y tipea" lo ya dicho, con
  riesgo de derivar (alucinar campos, omitir información).
- Requiere instanciar el modelo dos veces o re-bindear en runtime,
  rompiendo el patrón "un modelo por agente, configurado al import".

### Alternativa D — `BaseModel` como tool + while-loop interno

Bindear como **una tool más** el `BaseModel` que describe la salida
estructurada. El modelo lo invoca exactamente igual que cualquier otra
tool — con `tool_calls[i].name == "ResearcherOutput"` y los campos
declarados como `args` — y el bucle del nodo trata esa invocación como
señal de terminación: en vez de ejecutar la tool, lee `args` y los
devuelve como `stateUpdate`.

```python
modelResearcher = init_chat_model(...).bind_tools(
    [tavily_search, tavily_extract, tavily_crawl, ResearcherOutput]
)

async def nodeResearcher(state):
    messages = [...]
    while True:
        response = await modelResearcher.ainvoke(messages)
        messages.append(response)
        if not response.tool_calls:
            return {"messages": [response]}
        for tc in response.tool_calls:
            if tc["name"] == "ResearcherOutput":
                return {"research": tc["args"]["research"]}
        for tc in response.tool_calls:
            tool = _tools_by_name[tc["name"]]
            result = await tool.ainvoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
```

Esta alternativa resuelve los dos problemas a la vez: combina tools y
salida estructurada sin duplicar llamadas, y mete el bucle dentro del
nodo para no ramificar el grafo.

## Decisión

Se adopta la **Alternativa D**. El generador emite, para cada agente
con `tools`:

- En `agents.py`: `bind_tools([<tools>, <ClassOutput>?])`, donde
  `<ClassOutput>` solo aparece si el agente tiene `stateUpdate`.
- Un dict `_tools_by_name = {t.name: t for t in [...]}` a nivel de
  módulo, que el bucle usa para despachar `tool_calls` por nombre.
- El nodo se declara `async def` y contiene un `while True` con dos
  pasadas sobre `response.tool_calls`:
  1. Buscar primero la tool terminal (`ClassOutput`); si aparece,
     devolver el `stateUpdate` y salir.
  2. Si no, ejecutar todas las tools normales y volver al modelo.

Cuando el agente no tiene tools, el nodo sigue siendo síncrono y se
mantiene el patrón anterior (`with_structured_output` o mensaje libre,
según haya `stateUpdate` o no). La rama "con tools" no introduce ningún
nodo nuevo en el grafo.

## Consecuencias

- El generador de edges (ADR 004) no se entera de la existencia de
  tools: sigue conectando agentes según las capas y `next` declarados en
  el `.mad`. La complejidad del bucle queda confinada al nodo.
- El metamodelo no necesita un concepto separado de "nodo de tools" ni
  de "edge condicional sintética", lo que mantiene la regla del ADR
  006: el DSL describe lo que es esencial, no detalles de
  implementación.
- Los nodos con tools son `async`. Esto obliga a que `graph.py` invoque
  el grafo con `await graph.ainvoke(...)` en vez de `invoke(...)`
  cuando algún agente use tools — el generador del grafo debe detectar
  esta condición y emitir el lanzador correspondiente. Mientras un solo
  agente lleve tools, todo el flujo pasa a ser asíncrono, lo cual es
  consistente con LangGraph (un grafo es async si cualquiera de sus
  nodos lo es).
- Coste en tokens equivalente al de un agente que solo usa tools: una
  única secuencia de llamadas, sin segunda pasada para "tipar" la
  salida.
- El nombre de la tool terminal es `<AgentName>Output` (ya generado
  para los `BaseModel` de salida en ADR previos), por lo que no hay
  riesgo de colisión con tools reales declaradas en el `.mad`: la
  capitalización Pascal y el sufijo `Output` lo distinguen del estilo
  `snake_case` típico de tools MCP/Python.
- Si en el futuro LangChain expone una API que combine `bind_tools` y
  `with_structured_output` de manera nativa, este patrón puede
  reemplazarse por esa primitiva sin afectar al `.mad`: el cambio es
  local al generador de `agents.py`.
