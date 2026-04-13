# Configuración del entorno de desarrollo

## Estructura del proyecto

El proyecto sigue una arquitectura de monorepo con workspaces de npm, organizado en tres paquetes principales:

```
multiAgentDSL/
├── packages/
│   ├── language/     ← Gramática del DSL y lógica del generador
│   ├── cli/          ← Interfaz de línea de comandos
│   └── extension/    ← Extensión de VSCode
├── examples/         ← Modelos de ejemplo en el DSL
├── docs/             ← Documentación y prototipos
└── package.json      ← Configuración raíz del workspace
```

## Gestión de la compilación

El flujo de compilación de un proyecto Langium implica dos pasos diferenciados:

1. **Generación del AST** (`langium:generate`) → Lee la gramática `.langium` y genera automáticamente los tipos TypeScript que representan el árbol sintáctico abstracto del DSL. Este paso solo es estrictamente necesario cuando se modifica la gramática.

2. **Compilación TypeScript** (`tsc`) → Compila todos los paquetes del workspace a JavaScript ejecutable.

En proyectos de mayor escala, estos dos pasos se mantienen separados para evitar regenerar el AST innecesariamente, ya que la gramática suele ser estable. Sin embargo, dado que el proyecto se encuentra en una fase activa de desarrollo del metamodelo en la que la gramática evoluciona con frecuencia, se ha optado por unificar ambos pasos en un único comando de compilación, modificando el script `build` en el `package.json` raíz:

```json
"build": "npm run langium:generate && tsc -b tsconfig.build.json && npm run build --workspaces"
```

Esta decisión simplifica el flujo de trabajo durante el desarrollo, evitando errores difíciles de diagnosticar causados por un AST desactualizado respecto a la gramática. El coste asumido es un tiempo de compilación ligeramente superior, lo cual resulta aceptable en el contexto de un TFG.

## Flujo de trabajo habitual

```bash
# Compilar todo (gramática + TypeScript + extensión + CLI)
npm run build

# Ejecutar el generador sobre un modelo
node packages/cli/bin/cli.js generate examples/miModelo.mad

# Ejecutar el generador especificando carpeta de salida
node packages/cli/bin/cli.js generate examples/miModelo.mad -d ./output
```

## Estructura de la documentación

La carpeta `docs/` contiene toda la documentación de diseño y desarrollo del proyecto, organizada de la siguiente forma:

```
docs/
├── estructura.md              ← Este archivo
├── evolucionMetamodelo.md
├── evolucionGenerador.md
├── restricciones.md
├── backlog.md
├── metamodelo.md
├── adr/
│   ├── 001-compilacionUnificada.md
│   ├── 002-summarize&mixReducer.md
│   ├── 003-scopeProviderAttributes.md
│   └── 004-generadorEdges.md
└── prototipos/
    ├── cvReviewer/
    │   ├── cvReviewer.mad
    │   ├── cvReviewer.md
    │   └── code/
    └── research-assistant/
        ├── research-assistant.mad
        ├── research-assistant.md
        └── code/
```

### `evolucionMetamodelo.md`

Registro completo del proceso iterativo de diseño del metamodelo del DSL, desde la v1 (basada en Barriga et al.) hasta la v4 actual. Documenta para cada versión los cambios introducidos, las limitaciones detectadas y las decisiones tomadas. Sirve como trazabilidad del diseño y como material de apoyo para la memoria del TFG.

### `evolucionGenerador.md`

Registro del desarrollo incremental del generador de código. Documenta el estado de cada módulo generado (`prompt.py`, `config.py`, `state.py`, `agents.py`, `graph.py`), las decisiones y limitaciones de cada iteración, los cambios que el generador motivó en el metamodelo, y las instrucciones para ejecutar el código generado.

### `restricciones.md`

Catálogo de restricciones de bien-formedness (análogas a restricciones OCL) identificadas durante el desarrollo. Distingue entre restricciones ya implementadas en el validator de Langium y restricciones planificadas pendientes de implementación.

### `backlog.md`

Lista priorizada de tareas pendientes del proyecto, clasificadas por prioridad (alta, media, baja). Incluye desde funcionalidades bloqueantes como los mecanismos de bifurcación y el soporte de herramientas en agentes, hasta mejoras de calidad como flags en el CLI o la invocación del grafo con integración de LangSmith.

### `metamodelo.md`
Esquema del metamodelo y explicación de qué es cada clase.

### `adr/` — Architecture Decision Records

Registros de decisiones arquitectónicas relevantes tomadas durante el desarrollo. Cada ADR sigue la estructura contexto–decisión–consecuencias:

- **`001-compilacionUnificada.md`** — Justifica la unificación de `langium:generate` y `tsc` en un único comando `npm run build`, y la decisión de no aplicar `npm audit fix --force` para las vulnerabilidades de `lodash`.
- **`002-summarize&mixReducer.md`** — Explica por qué el nodo de resumen de mensajes se genera pero no se conecta al grafo: el mecanismo solo tiene sentido en grafos cíclicos, y la posición es ambigua en grafos con múltiples estructuras de comunicación.
- **`003-scopeProviderAttributes.md`** — Documenta la creación de un `ScopeProvider` personalizado en Langium para que las referencias `stateContext` y `stateUpdate` de los agentes puedan resolver los `Attribute` definidos dentro de `Environment`.
- **`004-generadorEdges.md`** — Justifica la separación del generador de edges en un subdirectorio `generators/edges/` con un módulo por estructura de comunicación, anticipando el crecimiento por bifurcaciones y HumanInTheLoop.

### `prototipos/` — Prototipos de validación del metamodelo

Contiene los dos sistemas multiagente implementados manualmente para validar la expresividad del metamodelo antes de desarrollar el generador. Cada prototipo incluye el modelo `.mad`, el código Python implementado a mano y un informe de evaluación con las limitaciones detectadas:

- **`research-assistant/`** — Asistente de investigación con cuatro agentes (organizador, investigador, redactor, validador) conectados mediante una estructura *centralized*, con herramientas MCP externas. Su informe (`research-assistant.md`) identificó limitaciones en flujo de control, gestión de herramientas, composición de estructuras y personalización de agentes.
- **`cvReviewer/`** — Pipeline de evaluación de candidatos con cuatro agentes (extractor, evaluador, generador de informes, notificador) conectados mediante una estructura *layered*, con una herramienta Python local. Su informe (`cvReviewer.md`) reforzó la necesidad de mecanismos de interacción explícita entre agentes y estado compartido mediante *structured outputs*.

## Notas sobre dependencias

Durante la configuración inicial se detectaron vulnerabilidades en la dependencia `lodash` utilizada por `langium-cli`. La solución propuesta por npm (`npm audit fix --force`) fue descartada ya que implicaba una bajada de versión de `langium-cli` a una versión con cambios disruptivos. Dado que las vulnerabilidades afectan únicamente a herramientas de desarrollo y no al código generado, se optó por mantener la versión actual y no aplicar la corrección forzada.