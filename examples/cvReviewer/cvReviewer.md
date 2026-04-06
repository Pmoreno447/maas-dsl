# Evaluación del metamodelo: segunda prueba de generación de código

## Introducción

Con el objetivo de continuar validando la expresividad y viabilidad del metamodelo propuesto, se llevó a cabo una segunda prueba consistente en la implementación manual de un sistema multiagente a partir de la especificación escrita en el DSL. El caso de uso seleccionado fue un pipeline de evaluación de candidatos compuesto por cuatro agentes (extractor, evaluador, generador de informes y notificador), conectados mediante una estructura de comunicación de tipo *layered*, en la que cada agente procesa y enriquece el estado compartido de forma secuencial antes de cederlo al siguiente.

A diferencia de la prueba anterior, este sistema no hace uso de herramientas MCP externas, sino de una herramienta Python local que simula el envío de notificaciones por correo electrónico a los candidatos que superan el umbral de puntuación establecido.

A continuación se documentan las limitaciones identificadas en el metamodelo actual, así como una valoración del resultado funcional obtenido.

## Limitaciones identificadas

### Gestión de herramientas

En la prueba anterior, las herramientas utilizadas provenían de servidores MCP externos y requerían un proceso de inicialización asíncrona previo a su vinculación con el modelo. En el presente caso, la herramienta empleada es una función Python decorada con `@tool`, cuya vinculación con el modelo se realiza de forma directa mediante `bind_tools`, sin necesidad de inicialización previa.

Esta diferencia en el mecanismo de integración podría constituir un problema para el generador de código, aunque realmente no es algo que dependa del propio metamodelo. 

### Interacción con el estado

El metamodelo actual no contempla mecanismos explícitos para que los agentes lean o escriban campos específicos del estado compartido del grafo. No obstante, dado que en la iteración anterior se propusieron soluciones concretas para abordar esta limitación, se tomó la decisión de anticipar su aplicación en la implementación manual, haciendo uso de *structured outputs* mediante esquemas Pydantic para que cada agente escribiese de forma estructurada y tipada los resultados de su procesamiento en el estado compartido.

El hecho de que esta aproximación funcione de forma notablemente más efectiva que la empleada en el caso anterior, donde toda la información se transmitía exclusivamente a través del campo `messages`, no hace sino reforzar la necesidad de incorporar estos mecanismos al DSL de forma explícita. La mejora en robustez y coherencia observada en este sistema es, en sí misma, un argumento a favor de incluir en el metamodelo mecanismos de interacción entre agentes y estado tanto para operaciones de lectura como de escritura.

## Conclusiones

Más allá de las limitaciones descritas, no se han identificado nuevas vulnerabilidades estructurales en el metamodelo, lo que sugiere que el nivel de madurez alcanzado es satisfactorio para afrontar la siguiente fase del proyecto. La capacidad del metamodelo para expresar sistemas *layered* funcionales, combinada con la viabilidad demostrada de los *structured outputs*, proporciona una base sólida sobre la que continuar.

El siguiente paso consistirá en proponer una nueva iteración del metamodelo que incorpore las mejoras identificadas en ambas pruebas, y en iniciar el desarrollo del generador de código. Si bien los patrones de comunicación *decentralized* y *shared pool* quedan pendientes de evaluación empírica, su exploración se pospone en favor de avanzar en la generación de código y en la identificación de restricciones que no puedan ser expresadas en el metamodelo en su estado actual.