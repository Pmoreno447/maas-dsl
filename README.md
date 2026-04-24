# Multi-Agent DSL — MaaS DSL

> **Estado actual:** Iteración 5 del metamodelo. El metamodelo se considera
> estable a partir de esta versión; las futuras modificaciones se esperan
> como extensiones no rupturistas. Consulta el historial completo de
> iteraciones en [`docs/evolucionMetamodelo.md`](./docs/evolucionMetamodelo.md).

DSL (Domain-Specific Language) para la especificación de sistemas multi-agente basados en LLMs (MaaS — Multi-Agent as a Service). Desarrollado como parte del TFG en ingeniería informática con Langium sobre Node.js/TypeScript.

---

## Versionado

El proyecto sigue una convención de versiones con tres niveles (`vX.Y.Z`):


- **X** — versión de release. Permanece en `0` durante el desarrollo del TFG. Pasará a `1` cuando el sistema se considere completo y publicable.
- **Y** —  iteración del metamodelo. Incrementa cuando se introduce una nueva versión del metamodelo con cambios estructurales. El historial completo de iteraciones está en [`docs/evolucionMetamodelo.md`](./docs/evolucionMetamodelo.md).
- **Z** — iteración del generador de código sobre el metamodelo actual. Incrementa con cada nuevo módulo generado o mejora significativa del generador. El historial está en [`docs/evolucionGenerador.md`](./docs/evolucionGenerador.md).

### Ejemplos

| Tag | Significado |
|---|---|
| `v0.4.0` | Metamodelo v4 estable, generador vacío |
| `v0.4.1` | MVP del generador de código |
| `v0.5.0` | Nueva iteración del metamodelo (bifurcaciones) |

---
## Estructura del proyecto

Para una descripción detallada de la estructura del proyecto y la configuración del entorno de desarrollo, consulta [`docs/estructura.md`](./docs/estructura.md).

---

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

---

## Restricciones (validator)

Las restricciones de bien-formedness que no pueden expresarse en la gramática se implementan en [`multi-agent-dsl-validator.ts`](./packages/language/src/multi-agent-dsl-validator.ts). Actualmente el validator es el generado por defecto de Langium; las restricciones específicas del DSL están **pendientes de implementar**.
 
---

## Instalación y uso

```bash
npm install
npm run build
```

Para usar la extensión VSCode, abrir el proyecto y ejecutar la tarea de lanzamiento desde `packages/extension/`.

---

## Tecnologías

- [Langium](https://langium.org/) — framework para DSLs en TypeScript
- Node.js / TypeScript
- VSCode Language Server Protocol