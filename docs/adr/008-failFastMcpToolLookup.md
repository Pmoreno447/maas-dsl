# ADR 008 — Fail-fast en la resolución de tools MCP al importar `mcpClients.py`

## Contexto

El módulo generado `tools/mcpClients.py` abre una conexión
`MultiServerMCPClient`, descarga la lista de tools que cada server expone
vía el protocolo MCP (`tools/list`) y expone una variable de módulo por
cada tool declarada en el `.mad`. El patrón inicial era emitir directamente:

```python
_all_tools = asyncio.run(_client.get_tools())

tavily_search  = next(t for t in _all_tools if t.name == "tavily_search")
tavily_extract = next(t for t in _all_tools if t.name == "tavily_extract")
```

Este patrón tiene un problema de diagnóstico. `next()` sin valor por
defecto lanza `StopIteration` cuando el iterador se agota — una excepción
que en tiempo de ejecución el intérprete convierte a `RuntimeError:
generator raised StopIteration` y el mensaje no dice **qué** tool faltaba
ni **qué** tools sí estaban disponibles. Para el usuario que depura, la
traza apunta a una línea genérica dentro de un fichero generado y no da
pistas accionables.

Los modos de fallo reales son variados:

1. **Typo en el `.mad`**: el usuario declara `tools "tavilly_search"` (con
   doble L). El server no expone esa tool, el generador emite la variable
   igualmente, y el fallo aparece al importar el módulo.
2. **Cambio de nombre en el server remoto**: el mantenedor del server MCP
   renombra una tool entre versiones. El `.mad` que funcionaba el lunes
   deja de funcionar el martes, sin cambios locales.
3. **Server parcialmente degradado**: el server responde a `tools/list`
   con un subconjunto de su catálogo (modo lectura, feature flags,
   problemas temporales). Algunas tools aparecen, otras no.
4. **Fallo de conexión silencioso**: `_all_tools` llega como lista vacía
   por un problema de red o auth, y todas las resoluciones fallan en
   cascada con el mismo mensaje opaco.

En cualquiera de estos cuatro casos, la traza de `StopIteration` es
idéntica y no distingue entre "el server no tiene esta tool" y "la lista
llegó vacía".

## Alternativas consideradas

### Alternativa A — Mantener `next(...)` tal cual

La forma más compacta. Descartada porque el coste en debuggability supera
el ahorro de una función helper. El mensaje de error no indica qué tool
faltaba ni qué estaba disponible, y el `StopIteration` en generadores se
considera un antipatrón desde PEP 479.

### Alternativa B — `next(..., None)` + dejar que el error salte después

```python
tavily_search = next((t for t in _all_tools if t.name == "tavily_search"), None)
```

La variable queda a `None`, el import no peta, y el fallo aparece cuando
el agente intenta invocar la tool. Descartada porque difiere el error al
runtime del agente — el usuario ve "NoneType no es callable" o un error
dentro de LangChain a mitad de ejecución, mucho más lejos del origen del
problema. Además una ejecución real consume tokens hasta llegar al punto
del fallo.

### Alternativa C — Validator en el generador

Al compilar el `.mad`, conectar al server MCP, listar sus tools y validar
contra la declaración. Descartada porque:

- Introduce I/O de red en el paso de generación, que hasta ahora es
  offline y determinista.
- Requiere que el server esté disponible en tiempo de compilación, lo que
  rompe el build en CI o en entornos sin red.
- No detecta los casos 2 y 3 de la lista (el server cambia después).

La validación en runtime al importar es más robusta: usa exactamente la
misma respuesta del server que usará el agente.

### Alternativa D — Helper `_get_tool` con fail-fast y mensaje diagnóstico

```python
def _get_tool(name: str):
    tool = next((t for t in _all_tools if t.name == name), None)
    if tool is None:
        raise RuntimeError(
            f"Tool '{name}' no encontrada en el servidor MCP. "
            f"Tools disponibles: {[t.name for t in _all_tools]}"
        )
    return tool

tavily_search = _get_tool("tavily_search")
```

El error ocurre al importar el módulo (antes de que el grafo arranque),
identifica la tool que falta, y enumera las que sí llegaron. Esa lista es
clave: distingue inmediatamente "typo en el nombre" ("pusiste
`tavilly_search`, el server tiene `tavily_search`") de "server caído o
mal configurado" (lista vacía) o "catálogo cambiado" (lista no vacía pero
sin la tool esperada).

## Decisión

Se adopta la **Alternativa D**. El generador emite una función
`_get_tool(name)` al inicio del módulo y la reutiliza para cada variable
de tool.

Propiedades:

- **Fail-fast en el import**: el error aparece antes de que el grafo
  arranque; el stack trace apunta al `_get_tool` y la línea del llamador
  identifica qué variable falló.
- **Mensaje accionable**: nombre de la tool buscada + catálogo real del
  server. Resuelve typos, cambios de catálogo y conexiones degradadas con
  el mismo mensaje.
- **Coste cero en runtime normal**: una función + un `next()` por tool
  declarada, al import. Despreciable frente al `asyncio.run(get_tools())`
  que ya estaba.
- **No requiere red en tiempo de compilación**: la validación sigue
  siendo una propiedad del módulo generado, no del generador.

## Consecuencias

- Cualquier discrepancia entre el `.mad` y el catálogo del server MCP se
  manifiesta como `RuntimeError` claro al cargar `tools/mcpClients.py`,
  con nombre de tool y catálogo disponible en el propio mensaje.
- El módulo generado gana una función auxiliar (`_get_tool`) por fichero,
  con una línea de export implícito. Aceptable.
- Casos de tool ausente en el server (renombrado, feature flag) se
  detectan en el arranque en vez de durante una ejecución real, evitando
  consumir tokens hasta el punto del fallo.
- Si un día se añade un paso de validación offline (Alternativa C) como
  complemento, `_get_tool` sigue sirviendo de red de seguridad para los
  casos 2 y 3 que esa validación no cubre.
