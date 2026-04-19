# ADR 007 — Granularidad por tool en `MCPTool` mediante el campo `toolName`

## Contexto

El metamodelo definía `MCPTool` con la información necesaria para
conectarse a un servidor MCP (`serverUrl`, `transport`, `key` opcional):

```langium
MCPTool:
    'mcpTool' ToolBase '{'
        'serverUrl' serverUrl=STRING
        'transport' transport=STRING
        ('key' key=STRING)?
    '}';
```

Esta declaración representa en realidad **un servidor MCP**, no una
herramienta concreta. Un servidor MCP típicamente expone múltiples tools:
Tavily expone `tavily_search`, `tavily_extract`, `tavily_crawl`, etc.;
servidores de filesystem o de bases de datos pueden exponer decenas o
incluso cientos.

La interpretación inicial considerada para el generador era *"si un agente
referencia este `mcpTool`, se le bindean todas las tools que el servidor
exponga"*. Al evaluarla con números reales aparecieron dos problemas
graves:

**1. Coste por token en cada llamada al LLM.** Cada definición de tool
(nombre + descripción + JSON schema de parámetros) se incluye en el system
prompt en cada turno. Estimación realista:

- Una tool típica ocupa ~100-200 tokens en su definición.
- Un servidor con 100 tools añade ~15k tokens de input por turno.
- Con `gpt-4o-mini` ($0.15 / 1M in): ~$0.002 por turno solo por tools →
  $0.02 en una ejecución de 10 turnos.
- Con `gpt-5` o `claude-opus-4-7` ($5 / 1M in): el mismo escenario
  asciende a $0.75 por ejecución, multiplicando por órdenes de magnitud
  el coste esperado de un agente.

**2. Degradación de la precisión de function-calling.** La capacidad del
modelo para escoger la tool correcta cae bruscamente con el número de
opciones presentes. Empíricamente el rango óptimo se sitúa entre 5 y 20
tools por agente. Con cientos de tools el modelo empieza a alucinar
nombres, escoger la tool equivocada o no llamar a ninguna.

Es decir: el default *"todas las tools del servidor"* no solo es caro,
también es funcionalmente peor que una selección dirigida.

## Alternativas consideradas

### Alternativa A — Mantener default "todas" + filtro opcional

Añadir un campo `only=[STRING+]` opcional para limitar:

```langium
mcpTool Tavily { serverUrl "..." transport "..." only ["tavily_search"] }
```

Descartada porque mantiene el default peligroso ("todas las tools del
server"), confiando en que el usuario sepa que existe el filtro y lo
aplique. La mayoría de usuarios solo lo descubrirán después del primer
recibo de OpenAI.

### Alternativa B — Separar `mcpServer` de `mcpTool`

Introducir dos constructos: uno para la conexión, otro para cada tool que
referencia esa conexión:

```langium
mcpServer Tavily { url "..." transport "..." key "..." }
mcpTool TavilySearch { server Tavily name "tavily_search" }
mcpTool TavilyExtract { server Tavily name "tavily_extract" }
```

Conceptualmente más limpia y elimina la duplicación de configuración
cuando varios `mcpTool` apuntan al mismo servidor. Descartada **por
ahora** porque introduce un constructo nuevo (`mcpServer`) y la
correspondiente referencia cruzada, ampliando la superficie del
metamodelo, del scope provider y del generador. Se mantiene como
evolución futura si la duplicación de `serverUrl` se vuelve molesta en la
práctica.

## Decisión

Se modifica `MCPTool` para que cada declaración represente **una tool
concreta de un servidor MCP**. Se añade el campo obligatorio `toolName`
con el nombre exacto de la tool en el servidor:

```langium
MCPTool:
    'mcpTool' ToolBase '{'
        'serverUrl' serverUrl=STRING
        'transport' transport=STRING
        'toolName' toolName=STRING
        ('key' key=STRING)?
    '}';
```

El nombre del `mcpTool` en el DSL (`name=ID` heredado de `ToolBase`) sigue
siendo el identificador local que usan los agentes para referenciarlo;
`toolName` es el nombre real con el que el servidor MCP la expone. La
distinción permite usar identificadores idiomáticos en el DSL sin
acoplarse a las convenciones de naming del servidor remoto.

Si un agente necesita varias tools del mismo servidor MCP, se declaran
varios `mcpTool` repitiendo `serverUrl` y `transport`. El generador es
responsable de detectar declaraciones que comparten servidor y emitir una
única conexión `MultiServerMCPClient` reutilizada para todas ellas (la
duplicación queda en la sintaxis del DSL, no en el código generado).

## Consecuencias

- El agente bindea solo las tools que necesita. El coste por token de las
  definiciones de tools queda acotado por la cantidad de `mcpTool`
  declaradas y referenciadas, no por el tamaño del servidor remoto.
- La precisión de function-calling se mantiene en el rango óptimo siempre
  que el usuario declare un número razonable de tools por agente.
- La declaración `mcpTool` es ahora granular y simétrica con `pythonTool`:
  cada declaración representa una herramienta individual que el agente
  puede usar, no un agregado opaco.
- Si un proyecto usa N tools del mismo servidor MCP, hay duplicación de
  `serverUrl`, `transport` y `key` en N declaraciones. Se acepta como
  coste a cambio de la simplicidad del metamodelo. La Alternativa B queda
  como posible refactorización si esta duplicación se vuelve un problema
  real.
- El generador necesita lógica adicional: agrupar `mcpTool` por
  `serverUrl` para emitir un solo cliente MCP por servidor, y filtrar las
  tools devueltas por el cliente quedándose con la `toolName`
  correspondiente para cada declaración.
- Los `.mad` que usaran la sintaxis anterior de `MCPTool` (sin
  `toolName`) son incompatibles con la gramática actual y deben migrarse.
