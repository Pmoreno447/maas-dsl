# Multi-Agent DSL — MaaS DSL

> **Estado actual:** Iteración 4 del metamodelo. El metamodelo se considera
> estable a partir de esta versión; las futuras modificaciones se esperan
> como extensiones no rupturistas. Consulta el historial completo de
> iteraciones en [`docs/evolucionMetamodelo.md`](./docs/evolucionMetamodelo.md).

DSL (Domain-Specific Language) para la especificación de sistemas multi-agente basados en LLMs (MaaS — Multi-Agent as a Service). Desarrollado como parte del TFG en ingeniería informática con Langium sobre Node.js/TypeScript.

---

## Versionado

El proyecto sigue una convención de versiones con tres niveles (`vX.Y.Z`):

- **X** — versión de release. Permanece en `0` durante el desarrollo del TFG. Pasará a `1` cuando el sistema se considere completo y publicable.
- **Y** — iteración del metamodelo. Incrementa cuando se introduce una nueva versión del metamodelo con cambios estructurales. El historial completo de iteraciones está en [`docs/evolucionMetamodelo.md`](./docs/evolucionMetamodelo.md).
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

## Documentación del proyecto

La carpeta [`docs/`](./docs/) contiene la documentación técnica del DSL más allá del código fuente:

- **[`docs/evolucionMetamodelo.md`](./docs/evolucionMetamodelo.md)** — historial completo de las iteraciones del metamodelo, desde la versión base inspirada en Barriga et al. (2025) hasta la versión actual, incluyendo decisiones de diseño, alternativas descartadas y limitaciones detectadas en cada fase.

- **[`docs/estructura.md`](./docs/estructura.md)** — descripción detallada de la estructura del proyecto, configuración de la compilación y flujo de trabajo de desarrollo.

- **[`docs/prototipos/`](./docs/prototipos/)** — prototipos de validación del metamodelo. Cada prototipo contiene un modelo `.mad` escrito en el DSL, el código ejecutable que el generador debería producir a partir de ese modelo (implementado manualmente), y un informe Markdown con las limitaciones del metamodelo detectadas durante el ejercicio. Actualmente incluye:
  - [`research-assistant/`](./docs/prototipos/research-assistant/) — asistente de investigación con estructura de comunicación *centralized* y herramientas MCP externas.
  - [`cvReviewer/`](./docs/prototipos/cvReviewer/) — pipeline de evaluación de candidatos con estructura *layered* y herramienta Python local.

Estos prototipos se emplean como mecanismo de validación empírica: antes de cerrar una iteración del metamodelo, se escriben modelos representativos y se genera manualmente el código esperado para identificar qué construcciones faltan o fallan.

---

## Conceptos del metamodelo

Un sistema se describe con la siguiente estructura raíz:
```
{
  environment ...
  profile ...
  tool ...
  agent ...
  <estructuras de comunicación> ...
}
```

### `Environment`
Define el entorno en que opera el sistema MaaS. Se divide en tres sub-conceptos:

- **GameRules** — reglas generales expresadas como descripciones de texto. Funcionan como instrucciones de sistema globales. _Pendiente de revisión: evaluar si deben ser prompts estructurados o descripciones libres._
- **Attributes** — atributos tipados del entorno (int / string / boolean) que representan estado compartido: usuario actual, localización, roles virtuales, etc. Desde v4 incluyen un campo de descripción obligatorio, empleado por el generador para construir esquemas de salida estructurada con metadatos coherentes.
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
Referencia un `Profile` y declara el modelo LLM a usar (`gpt` | `claude` | `ollama`). Desde v4, los agentes admiten además:

- **Parámetros de personalización por nodo** — configuración individual de cada agente (p. ej. temperatura, límites de tokens) para adaptar su comportamiento a su función dentro del sistema.
- **Referencias a atributos del estado** — cada agente puede declarar referencias explícitas de lectura y/o escritura sobre los `attributes` del entorno. Estas referencias serán utilizadas por el generador para inyectar valores del estado en el contexto del modelo (lectura) y para construir esquemas de salida estructurada que actualicen el estado compartido (escritura).

### `Tool`
Tres tipos de herramientas invocables por agentes:
- `PythonTool` — módulo Python local.
- `MCPTool` — servidor MCP remoto. Desde v4 admite un atributo `key` opcional para soportar servidores que requieran autenticación.
- `EndPointTool` — endpoint REST (GET / POST / PUT / DELETE).

### `CommunicationStructure`
Define cómo se comunican los agentes entre sí. Se han descartado los paradigmas de comunicación abstractos (`CommunicationParadigm`) para simplificar. El foco actual está en definir _quién habla con quién_ mediante cuatro estructuras concretas:

- `Layered` — organización en capas con niveles y referencias entre capas.
- `Centralized` — un agente coordinador central.
- `SharedMessagePool` — pool de mensajes compartido.
- `Decentralized` — sin coordinación central.

_Nota: en iteraciones anteriores se exploró un enfoque alternativo basado en componentes de comportamiento reutilizables. Los detalles de esa exploración y por qué se volvió al modelo de estructuras de comunicación están documentados en [`docs/evolucionMetamodelo.md`](./docs/evolucionMetamodelo.md)._

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