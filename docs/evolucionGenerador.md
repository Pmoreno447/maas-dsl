# Evolución del generador de código

## Metodología
El generador se desarrolla de forma incremental, siguiendo el mismo 
ciclo iterativo que el metamodelo. Cada módulo generado se valida 
contra el prototipo correspondiente.

## Módulos implementados

| Módulo | Archivo generado | Estado | Versión metamodelo |
|---|---|---|---|
| Prompts | `prompt.py` | ✅ Completo | v4 |
| Estado | `state.py` | 🟡 Parcial  | v4 |
| Agentes | `agents.py` | ⬜ Pendiente | v4 |
| Grafo | `graph.py` | ⬜ Pendiente | v4 |
| Tools | `tools/` | ⬜ Pendiente | v4 |

## Iteración 1 — Prompts y Estado básico
(Cuando se termine de implementar el MVP del generador se implementará)
- Generador de prompt completo sin problema, al fin y al cabo tan solo es un generador de strings desde profile
- Generador de state problema encontrado la inclusión del mecanismo para resumir, solución tomada, generar el nodo pero aun no se integra en el grafo, además de que se. detecta la necesidad de una nueva restricción ocl, revisar adr/002-summarize&mixReducer.md
- Cambios menores en el metamodelo, se necesitaban algunos atributos extra para el generador:
  - MaxMessage en Trim y Mix
- Se ha incluido un generador de archivos de configuración se genera un .env donde se tiene un template con algunas configuraciones que hay en el metamodelo como maxtokens y otras más privadas como las api keys de los LLM se quedan vacias para que el usuario las escriba, luego un config.py es generado para que se puedan usar desde cualquier otro archivo python y sin ser expuestas en github al subir el proyecto generado.
- Se ha dejado fuera de esta iteración el tipo de gestión de mensaje MIX, que combina el resumen con guardar los ultimos mensajes dado que afectaria en como reciben el contexto los agentes y podría complicar el generador en esta primera iteracion, por lo que se deja para otras iteraciones.
- Se ha dejado fuera de esta iteración el selector de modelos, genera automaticamente el gpt5nano para todos los casos
- Se ha dejado fuera de esta iteración el uso de herramientas de los agentes.
- algunas cosas que mejoren la calidad del codigo generado por ejemplo que la descripciond e los campos del structured output se defina como variable para por si lo usan varios nodos, tambien el nombre del modelo usado,por si algunos modelos estan repetidos, que no esté hardcodeado en todos.