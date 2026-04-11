# Evolución del metamodelo

Este documento recoge el proceso iterativo de diseño del metamodelo del DSL
para sistemas multiagente basados en LLM. Se conserva como registro del
desarrollo y como material de apoyo a la memoria del TFG.

## Metodología

El metamodelo no se definió de una sola vez, sino mediante un ciclo iterativo
en el que cada versión se refinaba a partir de las carencias detectadas en la
anterior. A partir de la tercera iteración, el proceso se apoyó además en
prototipos de validación: modelos de ejemplo escritos en el DSL junto con el
código que el generador debería producir a partir de ellos, utilizados para
identificar de forma empírica las limitaciones del metamodelo.

Los prototipos empleados en este proceso, junto con sus informes de fallos,
se conservan en [`prototipos/`](./prototipos/).

## Resumen de versiones

| Versión | Estado     | Ubicación                     | Descripción breve                                         |
|---------|------------|-------------------------------|-----------------------------------------------------------|
| v1      | Histórica  | Local (no versionada)         | Metamodelo base de Barriga et al. (2025)                  |
| v2      | Histórica  | Local (no versionada)         | Propuesta basada en componentes de comportamiento         |
| v3      | Histórica  | Repositorio (tag `v0.3`)      | Fusión de estructuras de comunicación con tools y estado  |
| v4      | **Actual** | Rama `feature/metamodelo-v4`  | Integración estado–agente y personalización de nodos      |

> **Nota sobre v1 y v2:** las dos primeras iteraciones se desarrollaron en
> local antes de versionar el proyecto en Git, por lo que no existen como
> commits en el historial del repositorio. Se describen aquí con el mismo
> nivel de detalle que el resto para mantener la trazabilidad del proceso.

---

## v1 — Metamodelo base de Barriga et al.

**Origen.** Esta primera iteración toma como punto de partida el metamodelo
propuesto en el artículo *Model-Driven Development Toward LLM-Based
Multi-Agent Systems* (Barriga et al., 2025), facilitado por el cotutor del
TFG y autor del mismo.

**Estructura principal.** El metamodelo original organiza el sistema en
torno a una clase raíz `LLMMultiAgentSystem` que agrupa:

- Una jerarquía `Task → StandardizedOperationalProcess → SubOperationProcess`
  para describir objetivos y su descomposición en pasos.
- Un `Environment` como contexto en el que opera el MAS.
- `GameRule` para expresar restricciones y reglas del sistema.
- `Agent` con `Profile` asociado, `apiKey` y `model`.
- Un `CommunicationModel` compuesto por un `CommunicationParadigm`
  (Cooperative, Debate, Competitive) y una `CommunicationStructure`
  (Layered, SharedMessagePool, Centralized, Decentralized).

**Limitaciones detectadas.**

- La jerarquía de tres niveles para describir tareas (`Task` →
  `StandardizedOperationalProcess` → `SubOperationProcess`) se consideró
  excesivamente compleja respecto al valor aportado, dado que en la práctica
  esa información acaba integrándose directamente en el prompt de los agentes.
- El `CommunicationModel` obliga a caracterizar todo el sistema con un único
  paradigma y una única estructura de comunicación. Este planteamiento
  resultaba demasiado rígido para sistemas reales en los que distintos
  subconjuntos de agentes adoptan patrones de interacción diferentes.
- No existe ningún mecanismo para integrar herramientas externas
  (APIs, funciones locales, servidores MCP) en los agentes, a pesar de que es
  una capacidad central en los MAS basados en LLM actuales.

**Decisión.** Se descartó la jerarquía de tareas a favor de un único atributo
`objective` en la raíz, y se planteó una alternativa al `CommunicationModel`
basada en componentes reutilizables, desarrollada en la v2.

---

## v2 — Propuesta basada en componentes de comportamiento

**Objetivo.** Sustituir el `CommunicationModel` por un sistema de componentes
de comportamiento declarados a nivel de sistema y asignables individualmente
a cada agente, con el propósito de permitir que distintos agentes del mismo
MAS adoptasen patrones de interacción diferentes y combinables.

**Cambios respecto a v1.**

- Eliminación de `CommunicationModel`, `CommunicationParadigm` y
  `CommunicationStructure`.
- Introducción de una jerarquía `AgentComponent` con variantes
  `DebateComponent`, `SelfReflectionComponent`, `HumanInTheLoopComponent`,
  `RAGComponent`, `CoordinatorComponent` y `ToolExecutorComponent`. La
  selección de componentes se basó en los patrones de diseño más frecuentes
  identificados en el estudio de Cai et al. (2025), que analiza 94 sistemas
  MAS basados en LLM.
- Introducción de una clase `Tool` para integrar herramientas externas
  preexistentes (endpoints, funciones locales, servidores MCP) en los agentes.
- Renombrado de `Environment` a `SharedContext`, con el rol más concreto de
  bloque de contenido inyectado como *system prompt* compartido por todos
  los agentes.
- Eliminación definitiva de la jerarquía de tareas.
- `GameRule` se mantuvo pero no se desarrolló en profundidad.

**Limitaciones detectadas.**

- Durante la revisión del diseño se concluyó que el enfoque basado en
  componentes no era realmente incompatible con las estructuras de
  comunicación de v1, sino que en buena medida las solapaba. Las estructuras
  `Layered`, `Centralized`, `SharedMessagePool` y `Decentralized` del
  metamodelo original ya permitían, reinterpretadas adecuadamente, expresar
  buena parte de los patrones que los componentes pretendían modelar.
- Al renunciar por completo a las estructuras de comunicación, v2 perdía un
  vocabulario ya establecido y razonablemente expresivo sin obtener a cambio
  una ganancia neta suficiente.

**Decisión.** En lugar de mantener ambas aproximaciones como alternativas,
se optó por fusionarlas en la v3: recuperar las estructuras de comunicación
de v1 y conservar de v2 las aportaciones genuinamente nuevas (sistema de
herramientas y reinterpretación del contexto compartido).

---

## v3 — Fusión y desarrollo del sistema de herramientas

**Objetivo.** Consolidar una versión del metamodelo que integrase las
estructuras de comunicación del diseño original con las aportaciones útiles
del enfoque por componentes, y desarrollar en profundidad las áreas que
hasta entonces habían quedado superficialmente tratadas.

Primera versión incluida en el repositorio. Corresponde al último commit de
`main` antes del inicio del flujo por ramas.

**Cambios respecto a v2.**

- Recuperación de las estructuras de comunicación de v1 (`Layered`,
  `Centralized`, `SharedMessagePool`, `Decentralized`) como forma principal
  de organizar la interacción entre agentes.
- Desarrollo detallado de la clase `Tool`, distinguiendo tres variantes
  según el tipo de integración: llamadas a APIs externas, módulos Python
  locales del proyecto, y herramientas expuestas mediante servidores MCP.
  Cada variante recoge los atributos específicos que requiere su
  integración posterior en el código generado.
- Reintroducción del nombre `Environment`, pero ya no como simple contenedor
  de contexto, sino descompuesto en dos elementos:
  - `messages`: configuración del mecanismo de gestión del campo de mensajes
    en LangGraph, permitiendo especificar estrategias de *trimming*,
    *summarization*, ambas o ninguna.
  - `attributes`: definición de variables adicionales del estado compartido
    del grafo.
- `GameRule` se mantiene sin desarrollar en profundidad, pendiente de
  iteraciones futuras.

**Evaluación de v3 mediante prototipos.** Tras cerrar esta versión se
pausó el desarrollo del metamodelo para validarlo empíricamente. Se
escribieron dos modelos de ejemplo en el DSL, se implementó manualmente el
código que el generador debería producir a partir de cada uno, y se
documentaron las limitaciones detectadas:

- **`prototipos/research-assistant/`** — Asistente de investigación con
  cuatro agentes (organizador, investigador, redactor y validador)
  conectados mediante una estructura *centralized*, con integración de
  herramientas MCP externas. Informe de fallos en
  [`prototipos/research-assistant/research-assistant.md`](./prototipos/research-assistant/research-assistant.md).
- **`prototipos/cvReviewer/`** — Pipeline de evaluación de candidatos con
  cuatro agentes (extractor, evaluador, generador de informes y notificador)
  conectados mediante una estructura *layered*, usando una herramienta
  Python local. Informe de fallos en
  [`prototipos/cvReviewer/cvReviewer.md`](./prototipos/cvReviewer/cvReviewer.md).

**Limitaciones detectadas en v3 (sintetizadas de ambos prototipos).**

- **Interacción con el estado.** El metamodelo permitía declarar atributos
  en el entorno, pero no ofrecía ningún mecanismo para que un agente
  concreto leyese o escribiese campos específicos de ese estado. Durante la
  implementación manual del segundo prototipo se comprobó que el uso de
  *structured outputs* con esquemas Pydantic para escribir en el estado
  mejoraba de forma notable la robustez y la coherencia del sistema
  respecto al enfoque basado únicamente en el canal de mensajes. Esta
  mejora hizo evidente la necesidad de incorporar al DSL referencias
  explícitas entre agentes y atributos del estado.
- **Personalización de agentes.** El metamodelo carecía de atributos para
  configurar parámetros propios de cada agente (temperatura, número máximo
  de tokens, modelo concreto, etc.), necesarios para adaptar el
  comportamiento de cada nodo a su función dentro del sistema.
- **Atributos del estado sin descripción.** La falta de un campo
  descriptivo en los atributos del entorno impedía generar automáticamente
  esquemas de salida estructurada correctamente documentados para los
  modelos.
- **Autenticación en herramientas MCP.** La definición de `MCPTool` no
  contemplaba la posibilidad de pasar claves de autenticación al servidor,
  requeridas por muchos servidores MCP reales.
- **Otras limitaciones detectadas pero no abordadas en v4.** Los informes
  recogen además carencias relativas al control de flujo explícito, la
  composición de varias estructuras de comunicación en un mismo sistema, y
  la gestión de errores y límites de iteración del grafo. Estas áreas
  quedan fuera del alcance de v4 y se abordarán en iteraciones posteriores
  si el cronograma del TFG lo permite.

**Referencias en el repositorio.**

- Tag: `v0.3`

---

## v4 — Integración estado–agente y personalización de nodos *(actual)*

**Objetivo.** Incorporar al metamodelo los mecanismos de interacción
explícita entre agentes y estado compartido, junto con la personalización
de parámetros por agente, tal como evidenciaron los prototipos de v3.

**Cambios respecto a v3.**

- **Referencias entre agentes y atributos del estado.** Se han añadido al
  metamodelo referencias explícitas desde `Agent` hacia los `attributes`
  del entorno, permitiendo distinguir entre operaciones de lectura y de
  escritura. Estas referencias serán utilizadas por el generador de código
  para construir automáticamente los esquemas de salida estructurada
  (escritura) y para inyectar los valores correspondientes del estado en
  el contexto proporcionado al modelo (lectura).
- **Parámetros de personalización por agente.** Se han añadido atributos
  que permiten configurar de forma individual cada nodo del grafo, de
  manera que agentes distintos dentro del mismo sistema puedan operar con
  configuraciones adaptadas a su función.
- **Campo de descripción en atributos del estado.** Los `attributes` del
  entorno incorporan ahora un campo descriptivo obligatorio, necesario
  para que el generador pueda producir esquemas de salida estructurada
  con metadatos coherentes.
- **Claves de autenticación en herramientas MCP.** Se ha añadido un
  atributo `key` a la definición de `MCPTool` para soportar servidores
  MCP que requieran autenticación.

**Estado.** A partir de esta iteración el metamodelo se considera
suficientemente estable para iniciar el desarrollo del generador de código.
Las futuras modificaciones se esperan como extensiones no rupturistas sobre
esta base.



**Referencias en el repositorio.**

- Tag: `v0.4`


