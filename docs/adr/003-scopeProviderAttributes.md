# ADR 003 — ScopeProvider personalizado para resolver referencias a Attribute

## Contexto

Al definir un agente en el DSL e intentar referenciar atributos del entorno mediante `stateContext` o `stateUpdate`, el language server devolvía el error:

```
Could not resolve reference to Attribute named 'candidateEmail'.
```

La gramática define los `Attribute` como hijos de `Environment`, que a su vez es hijo de `LLMMultiAgentSystem`. Los `Agent` también son hijos directos de `LLMMultiAgentSystem`, es decir, hermanos de `Environment`:

```
LLMMultiAgentSystem
├── Environment
│   └── Attribute*    ← aquí se definen
├── Profile*
├── Tool*
├── Agent*            ← aquí se referencian
└── CommunicationStructure*
```

El mecanismo de scoping por defecto de Langium resuelve referencias subiendo por el árbol AST y recogiendo los nombres visibles en cada nivel de contenedor. En el nivel de `LLMMultiAgentSystem` son visibles sus hijos directos (`Environment`, `Profile`, `Agent`, etc.), pero **no desciende** dentro de `Environment` para encontrar los `Attribute`. Por tanto, cualquier referencia `[Attribute]` desde un `Agent` fallaba.

## Decisión

Se ha creado un `ScopeProvider` personalizado (`MultiAgentDslScopeProvider`) que extiende `DefaultScopeProvider` y sobreescribe el método `getScope`. Cuando la referencia a resolver corresponde a la propiedad `stateContext` o `stateUpdate`, el provider navega hasta el nodo raíz `LLMMultiAgentSystem`, accede a su `Environment` y construye un scope con los `Attribute` definidos en él.

El provider se registra en `MultiAgentDslModule` sobreescribiendo el servicio `references.ScopeProvider`:

```typescript
references: {
    ScopeProvider: (services) => new MultiAgentDslScopeProvider(services)
}
```

Para el resto de referencias (profiles, tools, agents, etc.) se delega en el scope provider por defecto, que las resuelve correctamente al ser hijos directos de `LLMMultiAgentSystem`.

## Consecuencias

- Las referencias `stateContext` y `stateUpdate` en los agentes se resuelven correctamente contra los atributos del entorno.
- El autocompletado del language server sugiere los nombres de los atributos disponibles.
- Si en el futuro se añaden nuevos elementos anidados (por ejemplo, dentro de subestructuras de comunicación) que necesiten ser referenciados desde otros puntos del árbol, habrá que extender el scope provider con lógica análoga.
