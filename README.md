# Multi-Agent DSL — MaaS DSL

> **Estado actual:** Iteración 3 del metamodelo. El modelo está sujeto a cambios; las decisiones de diseño marcadas como _pendientes_ aún no son definitivas.

DSL (Domain-Specific Language) para la especificación de sistemas multi-agente basados en LLMs (MaaS — Multi-Agent as a Service). Desarrollado como parte del TFG en ingeniería informática con Langium sobre Node.js/TypeScript.

---

## Estructura del proyecto

| Paquete | Ruta | Descripción |
|---|---|---|
| **language** | [`packages/language/`](./packages/language/) | Núcleo: gramática, AST generado y validaciones |
| **cli** | [`packages/cli/`](./packages/cli/) | Interfaz de línea de comandos |
| **extension** | [`packages/extension/`](./packages/extension/) | Extensión VSCode con soporte de sintaxis |

### Archivos clave

- **Metamodelo (gramática):** [`packages/language/src/multi-agent-dsl.langium`](./packages/language/src/multi-agent-dsl.langium)
  Define la sintaxis concreta y abstracta del DSL con Langium.

- **AST generado:** [`packages/language/src/generated/ast.ts`](./packages/language/src/generated/ast.ts)
  Generado automáticamente a partir de la gramática. No editar a mano.

- **Restricciones / validaciones:** [`packages/language/src/multi-agent-dsl-validator.ts`](./packages/language/src/multi-agent-dsl-validator.ts)
  Equivalente a restricciones OCL. Aquí se añaden las reglas bien-formedness que no se pueden expresar directamente en la gramática (unicidad de nombres, coherencia entre referencias, etc.).

- **Módulo Langium:** [`packages/language/src/multi-agent-dsl-module.ts`](./packages/language/src/multi-agent-dsl-module.ts)
  Wiring del servicio de lenguaje (parser, linker, validator).

- **Ejemplos:** [`examples/`](./examples/)
  Código escrito a mano simulando el que generaría un generador de código sobre el metamodelo actual, con el objetivo de identificar las limitaciones del metamodelo en escenarios reales. Cada ejemplo incluye tres artefactos:
  - El modelo `.mad` que representa el sistema en el DSL.
  - El código ejecutable generado de forma simulada.
  - Un documento Markdown con los problemas encontrados durante el ejercicio.

---

## Conceptos del metamodelo

Un sistema se describe con la siguiente estructura raíz:

```
{
  environment ...
  profile ...
  tool ...
  agent ...
  <estructura de comunicación> ...
}
```

### `Environment`
Define el entorno en que opera el sistema MaaS. Se divide en tres sub-conceptos:

- **GameRules** — reglas generales expresadas como descripciones de texto. Funcionan como instrucciones de sistema globales. _Pendiente de revisión: evaluar si deben ser prompts estructurados o descripciones libres._
- **Attributes** — atributos tipados del entorno (int / string / boolean) que representan estado compartido: usuario actual, localización, roles virtuales, etc.
- **Messages** — mecanismo de gestión del historial de mensajes. Opciones: `trim` (recortar al superar N mensajes), `mix`, `summarize`, `none`.

### `Profile`
Actualmente se modela como un prompt de descripción textual asignado a un agente. Consideraciones:

- Para el **90% de los casos**, un prompt de descripción es suficiente.
- Se valoró incluir atributos de estado mutables en tiempo de ejecución para que la IA pueda adaptar el comportamiento dinámicamente, pero añade complejidad innecesaria en la mayoría de casos y se reserva para escenarios con requisitos de idioma, rol dinámico, etc.
- Alternativas estudiadas y descartadas por ahora:
  - _Fine Tuning_: rígido, costoso.
  - _Redes neuronales especializadas_: más flexible pero fuera del scope.
  - _Entidad ontológica_: expresivo pero sin razonamiento directo.

### `Agent`
Referencia un `Profile` y declara el modelo LLM a usar (`gpt` | `claude` | `ollama`).

### `Tool`
Tres tipos de herramientas invocables por agentes:
- `PythonTool` — módulo Python local.
- `MCPTool` — servidor MCP remoto.
- `EndPointTool` — endpoint REST (GET / POST / PUT / DELETE).

### `CommunicationStructure`
Define cómo se comunican los agentes entre sí. Se han descartado los paradigmas de comunicación abstractos (`CommunicationParadigm`) para simplificar. El foco actual está en definir _quién habla con quién_ mediante cuatro estructuras concretas:

- `Layered` — organización en capas con niveles y referencias entre capas.
- `Centralized` — un agente coordinador central.
- `SharedMessagePool` — pool de mensajes compartido.
- `Decentralized` — sin coordinación central.

_Nota: a priori se dejó a un lado la expresividad de los paradigmas de comunicación en favor de un enfoque más básico basado en componentes. Puede revisarse en iteraciones futuras._


---

## Restricciones (validator)

Las restricciones de bien-formedness que no pueden expresarse en la gramática se implementan en [`multi-agent-dsl-validator.ts`](./packages/language/src/multi-agent-dsl-validator.ts). Actualmente el validator es el generado por defecto de Langium; las restricciones específicas del DSL están **pendientes de implementar**.

Restricciones planificadas (no exhaustivo):
- Los niveles de `Layer` dentro de un `Layered` deben ser únicos.
- `Centralized` debe referenciar un agente existente como coordinador. 

---


## Instalación y uso

```bash
npm install∫∫
npm run build
```

Para usar la extensión VSCode, abrir el proyecto y ejecutar la tarea de lanzamiento desde `packages/extension/`.

---

## Tecnologías

- [Langium](https://langium.org/) — framework para DSLs en TypeScript
- Node.js / TypeScript
- VSCode Language Server Protocol
