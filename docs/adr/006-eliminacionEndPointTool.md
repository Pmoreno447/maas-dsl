# ADR 006 — Eliminación de `EndPointTool` del metamodelo

## Contexto

El metamodelo definía tres tipos de herramientas que un agente podía usar:
`PythonTool`, `MCPTool` y `EndPointTool`. Esta última pretendía capturar
una llamada a un endpoint HTTP arbitrario:

```langium
EndPointTool:
    'endpointTool' ToolBase '{'
        'url' url=STRING
        'method' method=MethodType
    '}';
```

La idea era que el generador produjera, a partir de esa declaración, una
función que llamara al endpoint y la expusiera al agente como una tool de
LangChain.

Al revisar los prototipos para preparar el generador de tools se hizo
evidente un problema de fondo: **HTTP es un protocolo de transporte
abierto**, no un mecanismo estandarizado de invocación de herramientas. La
información declarativa que el DSL podía capturar (URL + método) es
insuficiente para generar código útil en la mayoría de casos reales:

- Autenticación: Bearer, API key en header, en query string, OAuth, basic.
- Headers personalizados: `Content-Type`, `Accept`, `User-Agent`, headers
  internos de cada API.
- Body: forma del JSON, serialización, multipart, form-urlencoded.
- Query strings dinámicos en función de los argumentos.
- Manejo de errores, retries, timeouts, paginación.
- Parseo y validación de la respuesta antes de devolverla al agente.

Cualquier extensión del DSL para cubrir estos aspectos terminaría
reproduciendo HTTP entero en sintaxis Langium, contradiciendo la propia
razón de ser de un DSL específico de dominio. Y un generador que se
limitase a `requests.request(method, url)` produciría código que el usuario
tendría que editar a mano para casi cualquier integración real, perdiendo
los cambios en la siguiente regeneración.

## Alternativas consideradas

### Alternativa A — Mantener `EndPointTool` y ampliar sus campos

Añadir progresivamente headers, auth, body templates, etc. a la gramática.
Descartada porque:

- La superficie crece sin límite y nunca cubre todos los casos reales.
- El usuario acaba teniendo que escribir Python igualmente para los casos
  no triviales (parseo de respuesta, transformación de argumentos).
- Reproduce HTTP en el DSL, alejándolo de su propósito.

### Alternativa B — Mantener `EndPointTool` con generación mínima

Generar solo el caso trivial (GET sin auth) y dejar al usuario editar el
fichero. Descartada porque:

- El código generado se sobrescribe en cada regeneración, perdiendo las
  ediciones del usuario.
- Mezcla código generado con código manual en el mismo fichero, rompiendo
  la garantía "todo lo generado es regenerable".

## Decisión

Se elimina `EndPointTool` del metamodelo. Los casos que antes se cubrían
con esta construcción se modelan como `PythonTool`: el usuario escribe una
función decorada con `@tool` que internamente realiza la llamada HTTP con
la librería que prefiera (`requests`, `httpx`, etc.) y aplica la lógica
específica que necesite (auth, parseo, error handling).

Cambios concretos:

- Se borra la regla `EndPointTool` y la regla auxiliar `MethodType` de la
  gramática.
- Se elimina `EndPointTool` de la unión `Tool` y de la lista de tipos
  permitidos en `LLMMultiAgentSystem.tools`.
- Si alguna iteración del generador llegó a producir código para esta
  construcción, se elimina también.

## Consecuencias

- El metamodelo queda con dos tipos ortogonales de tool: `PythonTool`
  (lógica local arbitraria, puede envolver cualquier llamada externa) y
  `MCPTool` (servicio externo conforme al protocolo MCP, ver ADR 007).
- El generador no necesita mantener templates HTTP que serían inferiores
  al código que el usuario escribiría a mano.
- Para casos triviales (GET público sin auth), el usuario asume el coste
  de escribir ~5 líneas de Python en lugar de declararlo en el DSL. Es un
  precio aceptable a cambio de no incluir un constructo cuya información
  declarativa es insuficiente para generar código correcto.
- La regla mental que guía qué merece ser tipo de tool en el DSL queda
  consolidada: **un tipo de tool entra en el metamodelo si su información
  declarativa es suficiente para generar código completo y correcto. Si
  requiere "código del usuario" para ser útil, es un PythonTool
  disfrazado.**
- Si en el futuro aparece un patrón HTTP suficientemente estandarizado
  (por ejemplo, una especificación OpenAPI) que permita generar código
  fiel sin ambigüedad, se puede reintroducir como un nuevo tipo de tool
  apoyado en esa especificación, sin que afecte a la decisión actual.
