# ADR 010 — Estado compartido para subgrafos frente a estado por subgrafo

## Contexto

Para soportar la mezcla de estructuras de comunicación (`Layered`, `Centralized`,
`SharedMessagePool`, `Decentralized`) en un mismo sistema, el generador producirá
cada estructura como un subgrafo de LangGraph. La pregunta es cómo gestionar el
estado en ese escenario: si cada subgrafo tiene su propio `TypedDict` o si todos
comparten el estado del grafo padre.

LangGraph permite que un subgrafo tenga su propio esquema de estado, distinto del
padre. En ese caso, el framework se encarga de copiar hacia adentro y hacia afuera
los campos que ambos esquemas tengan en común. Este patrón ofrece aislamiento
(el subgrafo no puede leer ni escribir campos del padre que no hayan sido declarados
explícitamente) y reusabilidad de subgrafos entre sistemas distintos.

Sin embargo, adoptarlo en el generador implicaría:

- Extender el DSL para que el usuario pueda declarar qué atributos del estado
  pertenecen a cada estructura de comunicación y cuáles son compartidos con el
  padre.
- Generar múltiples `TypedDict` (uno por subgrafo más el padre) en vez de uno solo,
  con la lógica de herencia y proyección de campos entre ellos.
- Segmentar el resto de los módulos generados (`agents.py`, `prompt.py`, ...) por
  subgrafo, tanto para mantener la legibilidad del código como para que los agentes
  de cada subgrafo importen únicamente su propio estado.

Se trata de un cambio de gran alcance que rompe partes ya consolidadas del generador
y del DSL, con un coste de implementación muy alto y un beneficio limitado en el
contexto de código generado: la reusabilidad de subgrafos entre sistemas no aporta
valor cuando el código se genera siempre desde el modelo, y el aislamiento también está asegurado por la forma en que definimos en el modelo como interactúan los agentes con los atributos del estado.

## Decisión

Se genera un único `state.py` con un solo `TypedDict` que contiene todos los
atributos del sistema, independientemente del número de estructuras de comunicación
que se mezclen. Todos los subgrafos comparten ese estado del grafo padre.

Esta decisión se refleja en el backlog con dos tareas:

- **Segmentación de módulos por subgrafo** (prioridad media, esfuerzo medio):
  refactorizar el generador para que los archivos `agents.py`, `prompt.py` y
  similares se dividan por estructura de comunicación. No afecta a la corrección
  del código generado, pero mejora su legibilidad.
- **Estado independiente por subgrafo** (prioridad baja, esfuerzo muy alto):
  extender el DSL y el generador para soportar esquemas de estado por subgrafo.
  Solo tiene sentido abordarla si aparece un caso de uso real que lo justifique.

## Consecuencias

La hoja de ruta para alcanzar la v1.0.0 del generador queda ordenada de la
siguiente forma:

1. Soporte de bifurcaciones entre subgrafos en el DSL y en el generador de edges.
2. Generador de código para la mezcla de estructuras de comunicación mediante subgrafos.
3. Generación de al menos una estructura adicional (`Centralized`, `SharedMessagePool`
   o `Decentralized`).
4. Integración de LangSmith Studio para facilitar el uso del grafo generado en
   producción (API automática y trazas de debug).

A partir de ese punto se considerará cerrada la primera versión del generador y las
tareas del backlog se abordarán en función del tiempo disponible.
