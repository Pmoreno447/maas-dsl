# ADR 004 — Separación del generador de edges en módulos por estructura de comunicación

## Contexto

El generador de código produce entre otros el archivo `graph.py`, que incluye 
los edges del grafo LangGraph. Cada estructura de comunicación del metamodelo 
(`Layered`, `Centralized`, `SharedMessagePool`, `Decentralized`) genera edges 
con lógica completamente diferente.

A diferencia del resto de generadores, donde la lógica cabe cómodamente en un 
único archivo, el generador de edges se prevé que crezca significativamente con:
- La implementación de las cuatro estructuras de comunicación
- El soporte futuro de bifurcaciones reales
- La incorporación de HumanInTheLoop

## Decisión

Se separa el generador de edges en un subdirectorio `generators/edges/` con un 
módulo por estructura de comunicación y un orquestador `index.ts` que delega 
en el módulo correspondiente según el tipo de estructura.

En la iteración actual solo se implementa `layered.ts`. El resto de estructuras 
se dejan como stubs hasta iteraciones posteriores.

## Consecuencias

- Cada estructura de comunicación puede evolucionar de forma independiente sin 
  afectar al resto.
- Añadir soporte para bifurcaciones o HumanInTheLoop implica modificar un único 
  módulo, no el generador completo.
- El archivo principal del generador de grafos queda limpio, delegando toda la 
  lógica de edges al subdirectorio.