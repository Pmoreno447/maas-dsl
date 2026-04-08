# Evaluación inicial del metamodelo: primera prueba de generación de código

## Introducción

Con el objetivo de validar la expresividad y la viabilidad del metamodelo propuesto, se llevó a cabo una primera prueba consistente en la implementación manual de un sistema multiagente a partir de una especificación escrita en el DSL. El caso de uso seleccionado fue un asistente de investigación compuesto por cuatro agentes (organizador, investigador, redactor y validador) conectados mediante una estructura de comunicación centralizada, con integración de herramientas MCP externas.

A continuación se documentan las limitaciones identificadas en el metamodelo actual, organizadas por categoría, así como una valoración del resultado funcional obtenido.

## Limitaciones identificadas

### Flujo de control

El metamodelo actual carece de mecanismos explícitos para definir flujos de control entre agentes. En la prueba realizada, el ciclo de trabajo se modeló mediante una estructura de comunicación centralizada en la que un agente coordinador decide dinámicamente el siguiente nodo a ejecutar. Este enfoque presenta un riesgo inherente: al delegar la decisión de enrutamiento a un modelo de lenguaje, existe la posibilidad de que este produzca alucinaciones o decisiones inconsistentes, como omitir nodos obligatorios del flujo o ejecutar transiciones no válidas.

### Gestión de herramientas

El metamodelo permite declarar herramientas y asociarlas a agentes. Sin embargo, no contempla el comportamiento del agente cuando ninguna de las herramientas disponibles es adecuada para la tarea en curso. En la implementación actual, el agente queda limitado a un bucle interno en el que decide qué herramienta utilizar, pero no dispone de un mecanismo para escalar la situación, como saltar a un nodo alternativo del grafo o notificar un fallo al coordinador.

### Composición de estructuras de comunicación

El metamodelo únicamente permite definir una estructura de comunicación por sistema. En escenarios reales, es habitual que un sistema multiagente combine diferentes patrones (por ejemplo, una capa secuencial seguida de un subgrafo centralizado). La ausencia de mecanismos de composición limita la capacidad expresiva del DSL.

### Generación del enrutador

La generación automática del componente de enrutamiento para la estructura centralizada no debería representar un problema técnico significativo. No obstante, se identificó una complejidad adicional: el generador debe determinar si la estructura de comunicación es la última del grafo para poder generar correctamente la condición de terminación. Este aspecto requiere un análisis contextual que el metamodelo actual no facilita.

### Personalización de agentes

El metamodelo carece de atributos para configurar parámetros específicos de cada agente, como la temperatura del modelo de lenguaje, el número máximo de tokens o el modelo concreto a utilizar. Estos parámetros resultan esenciales para adaptar el comportamiento de cada agente a su función dentro del sistema.

### Interacción con el estado

La forma en que los agentes interactúan con el estado compartido del grafo resulta excesivamente rígida. Si bien el metamodelo permite definir atributos adicionales en el entorno (estado), no proporciona un mecanismo para que los agentes lean o escriban en campos específicos del mismo. En la implementación realizada, el campo `next` del estado se gestiona de forma implícita como parte de la estructura de comunicación centralizada, lo cual es correcto. Sin embargo, si se desease que un agente almacenase información adicional en el estado (por ejemplo, el tema de investigación en un campo dedicado), el metamodelo no ofrece la expresividad necesaria para especificarlo.

**Posible Solución**
```python
class RedactorOutput(BaseModel):
    draft: str = Field(description="El paper redactado")
    opinion: str = Field(description="Tu opinión sobre la calidad del paper")

modeloRedactor = init_chat_model("openai:gpt-5-nano", temperature=0).with_structured_output(RedactorOutput)

def nodoRedactor(state):
    prompt = f"{REDACTOR}\n\nFuentes disponibles:\n{state['sources']}"
    response = modeloRedactor.invoke(
        [SystemMessage(content=prompt)]
        + state["messages"]
    )
    return {
        "messages": [AIMessage(content=response.draft)],
        "draft": response.draft,
        "opinion": response.opinion,
    }
```

Una posible solución consistiría en permitir que los agentes del metamodelo incluyan referencias explícitas a los atributos definidos en el entorno (*environment*). Estas referencias permitirían distinguir entre operaciones de lectura y escritura sobre el estado compartido.

En el caso de la escritura, el generador de código podría utilizar dichas referencias para construir automáticamente un esquema de salida estructurada (*structured output*) asociado al agente, incorporando la descripción de cada campo. Asimismo, al detectar la presencia de referencias de escritura, el generador incluiría en el `return` del nodo no solo el campo `messages`, sino también los campos adicionales del estado correspondientes. La descripción de cada atributo debería definirse únicamente en el bloque `environment`, evitando así redundancias en caso de que varios agentes referencien el mismo campo.

Para la lectura, el mecanismo sería análogo: una referencia de lectura en la definición del agente indicaría al generador que debe inyectar el valor del atributo correspondiente del estado en el contexto que se le proporciona al modelo de lenguaje durante la invocación.

### Consistencia sintáctica

Se detectó que la sintaxis para la declaración de los distintos tipos de herramientas presenta inconsistencias con respecto al resto de elementos del metamodelo. Se recomienda unificar la sintaxis para mejorar la coherencia del DSL y facilitar su aprendizaje.

Además se debe refinar las mcp_tools para que se adapten a lo que realmente se genera en el código.

## Resultado funcional

El código generado a partir de la especificación del metamodelo es funcionalmente correcto y ejecutable. El sistema multiagente es capaz de completar el flujo de trabajo previsto: investigación, redacción y revisión de un artículo académico.

No obstante, se identificaron carencias relevantes en cuanto a la robustez del sistema generado. En concreto, la ausencia de mecanismos de gestión de errores implica que, ante un fallo en una herramienta externa (como una respuesta HTTP 429 por exceso de peticiones a la API de Tavily), el grafo continúa su ejecución como si la operación hubiese tenido éxito, o bien se produce un error irrecuperable que interrumpe la ejecución. Asimismo, la falta de límites de iteración podría provocar bucles infinitos en los que el sistema consume tokens de forma indefinida sin alcanzar una condición de terminación.

## Conclusiones

Esta primera evaluación pone de manifiesto que, si bien el metamodelo propuesto es capaz de generar código funcional para sistemas multiagente básicos, presenta limitaciones significativas en áreas clave como el control de flujo, la gestión de errores, la composición de estructuras y la personalización de agentes. Las mejoras identificadas servirán como guía para la evolución del metamodelo en iteraciones posteriores.