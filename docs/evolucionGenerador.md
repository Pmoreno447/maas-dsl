# Evolución del generador de código

## Metodología

El generador se desarrolla de forma incremental, siguiendo el mismo ciclo iterativo que el metamodelo. Cada módulo generado se valida contra el prototipo correspondiente. Los módulos marcados como parciales son funcionales para los casos cubiertos, pero no implementan la totalidad de las construcciones del metamodelo.

## Módulos implementados

| Módulo | Archivo generado | Estado | Versión metamodelo |
|---|---|---|---|
| Prompts | `prompt.py` | ✅ Completo | v4 |
| Configuración | `.env.template` + `config.py` | 🟡 Parcial | v4 |
| Estado | `state.py` | 🟡 Parcial | v4 |
| Agentes | `agents.py` | 🟡 Parcial | v4 |
| Grafo | `graph.py` | 🟡 Parcial | v4 |
| Tools | `tools/` | ⬜ Pendiente | v4 |

---

## Iteración 1 — MVP del generador

Primera iteración del generador de código sobre el metamodelo v4. El objetivo de esta iteración es producir código ejecutable para el patrón de comunicación *layered*, cubriendo los casos más comunes sin abordar aún la totalidad de las construcciones del metamodelo.

### Módulos generados

**`prompt.py`**
Generación completa sin incidencias. Al tratarse de una proyección directa de los `Profile` del modelo a constantes de texto Python, no presenta complejidad técnica relevante.

**`state.py`**
Generación funcional con soporte para los mecanismos de mensajes `none` y `trim`. El mecanismo `summarize` genera el nodo de resumen pero no lo integra en el grafo, ya que su posición en sistemas con múltiples estructuras de comunicación es ambigua, y carece de utilidad práctica en grafos lineales al no haber riesgo de crecimiento indefinido del historial. Se optó por generarlo al inicio del archivo como solución provisional, a la espera de que el generador incorpore soporte para grafos cíclicos, bifurcaciones y mezcla de structuras de comunicación, per de momento solo con una implementación. básica de layered no tiene sentido implementar esto en el generador. Para más detalle ver [`adr/002-summarize&mixReducer.md`](./adr/002-summarize&mixReducer.md).

**`.env.template` + `config.py`**
Se genera un `.env.template` con los valores definidos en el metamodelo (como `MAX_TOKENS` o `MAX_MESSAGES`) y con las API keys vacías para que el usuario las complete. El `config.py` centraliza la carga del entorno mediante `load_dotenv()` y expone las variables como constantes Python importables desde cualquier módulo, evitando llamadas dispersas a `os.getenv`. La apikey de los modelos usados están hardcodeadas en el generador de momento, por lo que faltaría hacer que en función del modelo importe un apikey u otra.

**`agents.py`**
Generación funcional para agentes sin herramientas. Produce los esquemas de salida estructurada (`BaseModel` + `Field`) a partir de las referencias `stateUpdate` del agente, los modelos con sus parámetros de configuración, y los nodos del grafo con inyección de contexto desde `stateContext`. La generación de agentes con herramientas queda pendiente para la siguiente iteración.

**`graph.py`**
Generación funcional para la estructura de comunicación `Layered`. El algoritmo de ordenación de capas se basa en las referencias `next` entre `Layer`, sin depender del atributo `level`, lo que lo hace más robusto ante modelos mal ordenados. Incluye un bloque de ejecución provisional para facilitar las pruebas durante el desarrollo. Ver [`adr/004-generadorEdges.md`](./adr/004-generadorEdges.md).

### Decisiones y limitaciones de esta iteración

- **Mix descartado:** el mecanismo de mensajes `mix` queda fuera del alcance de esta iteración. Su implementación afectaría a cómo los agentes reciben el contexto y añadiría complejidad prematura. Ver [`adr/002-summarize&mixReducer.md`](./adr/002-summarize&mixReducer.md) y [`backlog.md`](./backlog.md).
- **Selector de modelos no implementado:** todos los agentes generan con `gpt-5-nano` por defecto. La selección del modelo según el atributo `model` del agente (`gpt`, `claude`, `ollama`) queda pendiente.
- **Herramientas no implementadas:** la vinculación de herramientas (`PythonTool`, `MCPTool`, `EndPointTool`) a los agentes queda pendiente.
- **Solo estructura Layered:** la combinación de múltiples estructuras de comunicación en un mismo sistema queda pendiente. Ver [`adr/004-generadorEdges.md`](./adr/004-generadorEdges.md).
- **Calidad del código generado:** quedan pendientes mejoras como extraer las descripciones de los campos de `structured output` a variables reutilizables, o deduplicar la definición del modelo cuando varios agentes usan el mismo.

### Cambios menores en el metamodelo motivados por el generador

Durante el desarrollo del generador se detectó la necesidad de los siguientes atributos adicionales en el metamodelo:
- `maxMessages` en `Trim` y `Mix`, necesario para parametrizar el reducer.

### Validación de la iteración

Para validar el generador se utilizó el modelo [`examples/cvReviewer.mad`](../examples/cvReviewer.mad), que cubre las construcciones actualmente soportadas. El código generado a partir de este modelo se adjunta en [`examples/cvReviewer/generated/`](../examples/cvReviewer/generated/) y fue ejecutado satisfactoriamente.

Las construcciones validadas en esta iteración son:

- **Mecanismo de mensajes:** `none`, `trim` y `summarize`, comprobando que el reducer y el nodo se generan en el orden correcto respecto a la clase `State`.
- **Atributos del estado:** los tres tipos soportados por el metamodelo (`string`, `int`, `boolean`), verificando que se mapean correctamente a los tipos Python equivalentes (`str`, `int`, `bool`).
- **Structured outputs:** generación de esquemas `BaseModel` con `Field` a partir de las referencias `stateUpdate` de los agentes, incluyendo la descripción de cada campo.
- **Inyección de contexto:** generación del bloque `HumanMessage` con los campos del estado referenciados en `stateContext` de cada agente.
- **Estructura de comunicación Layered:** generación correcta de los edges `START → capa1 → ... → capaN → END` a partir de las referencias `next` entre capas.

**Referencias en el repositorio.**

- Tag: `v0.4.1`

---

## Modelo de ejecución del código generado

```bash
# 1. Generar el código desde el modelo .mad
node packages/cli/bin/cli.js generate examples/cvReviewer/cvReviewer.mad -d ./examples/cvReviewer/code   

# 2. Entrar en la carpeta generada

# 3. Rellenar las API keys en el .env.template y renombrarlo
# Editar .env y añadir OPENAI_API_KEY, no es necesario definir la api_key de langsmith

# 4. Generar el requirements.txt automáticamente
pip install pipreqs
pipreqs . --force

# 5. Crear el entorno virtual e instalar dependencias
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Ejecutar
python graph.py
```

> ⚠️ Antes de ejecutar, asegurarse de que `OPENAI_API_KEY` está definida en el `.env`. Y que se ha definido una entrada en el graph.py, hay ejemplos de entrada y salida junto al código generado.