# ADR 005 — Separación provider/model y catálogo de modelos extraído de la gramática

## Contexto

En la primera iteración del DSL los modelos LLM disponibles para un agente se
definían como un enumerado estático dentro de la propia gramática:

```langium
ModelType returns string:
    'gpt' | 'claude' | 'ollama';
```

Este enfoque tiene tres problemas serios:

1. **Mezcla provider y modelo en un único valor.** `gpt` no es un modelo, es
   una familia que pertenece al provider OpenAI. La generación de código
   necesita saber el provider para emitir las importaciones correctas y, sobre
   todo, para resolver qué API key inyectar (`OPENAI_API_KEY`,
   `ANTHROPIC_API_KEY`, etc.). Sin esa distinción explícita, el generador
   tendría que mantener un mapa interno frágil "modelo → provider" que se
   rompe cada vez que sale un modelo nuevo.

2. **Lista desactualizada por construcción.** Los proveedores publican modelos
   nuevos cada pocos meses (GPT-5, Claude 4.7, Gemini 2.5, etc.). Cualquier
   lista incrustada en la gramática queda desfasada en cuestión de semanas, y
   actualizarla obliga a tocar el `.langium`, regenerar AST y redistribuir la
   extensión.

3. **Granularidad insuficiente.** `gpt` no permite distinguir entre `gpt-4o`,
   `gpt-4o-mini` o `gpt-5-nano`, que tienen costes y capacidades muy
   distintas. El usuario no puede expresar la elección concreta que necesita.

## Alternativas consideradas

### Alternativa A — Mantener todo estático ampliando el enumerado

Listar todos los modelos concretos como literales en la gramática
(`'gpt-4o' | 'gpt-4o-mini' | 'claude-opus-4-7' | ...`). Descartada porque:

- Reproduce el problema del desfase, agravado por tener decenas de literales.
- Cada nuevo modelo exige regenerar AST y republicar la extensión.
- El generador sigue necesitando deducir el provider a partir del nombre del
  modelo, con la fragilidad ya descrita.

### Alternativa B — Modelo como STRING libre sin validación

Aceptar `model=STRING` sin restricciones. El usuario escribiría libremente
cualquier identificador. Descartada porque:

- Se pierde por completo el **autocompletado** de modelos en el editor: un
  STRING es un terminal abierto, el editor no tiene forma de saber qué
  sugerir.
- El usuario depende de consultar la documentación oficial de cada provider
  para conocer los identificadores exactos, lo que rompe la propuesta de
  valor de un DSL específico de dominio (debe guiar, no obligar a buscar
  fuera).
- Errores tipográficos (`gpt4o` en vez de `gpt-4o`) se descubren en tiempo
  de ejecución del código generado, no en el editor.

## Decisión

Se separa el concepto en dos campos del agente:

```langium
ProviderType returns string:
    'openai' | 'anthropic' | 'ollama' | 'google';

Agent:
    'agent' name=ID '{'
        'provider' provider=ProviderType
        'model' model=STRING
        ...
    '}';
```

- **`provider`** se mantiene como enumerado estático en la gramática. La
  lista de proveedores cambia con muy baja frecuencia (años, no meses) y es
  imprescindible que sea estática porque condiciona la generación de código
  (imports, API key, cliente LangChain).

- **`model`** es un STRING validado contra una lista curada por proveedor
  almacenada en [models.ts](../../packages/language/src/models.ts):

  ```ts
  export const MODELS: Record<Provider, readonly string[]> = {
      openai:    ['gpt-5.4', 'gpt-5', 'gpt-4o', ...],
      anthropic: ['claude-opus-4-7', 'claude-sonnet-4-6', ...],
      google:    ['gemini-2.5-pro', 'gemini-2.5-flash', ...],
      ollama:    ['llama3.3', 'qwen3', 'mistral', ...]
  };
  ```

  Hoy esta lista es estática y se mantiene a mano cotejando las páginas
  oficiales de cada proveedor. La elección de un fichero TypeScript
  (en vez de hardcodear en gramática) deja **abierta la puerta a generarlo
  automáticamente** en una iteración futura sin tocar ni gramática ni AST:
  basta con que un script reescriba el contenido de `MODELS`. Posibles
  evoluciones contempladas:

  - Job de CI semanal que consulte las APIs `GET /v1/models` de cada
    proveedor con secrets del proyecto y abra un PR con la lista
    actualizada.
  - Catálogo público hosteado en una URL estable que la extensión consulte
    al activarse, con fallback a la lista bundled.
  - Para Ollama específicamente, consulta a `localhost:11434/api/tags` en
    `activate()` de la extensión, ya que es local y los modelos los gestiona
    el propio usuario con `ollama pull`.

### Validación cruzada y autocompletado personalizado

Como la gramática por sí sola no puede expresar la restricción "el `model`
debe pertenecer a la lista del `provider` declarado", se han añadido dos
servicios al language server:

- **Validator** ([multi-agent-dsl-validator.ts](../../packages/language/src/multi-agent-dsl-validator.ts)):
  comprueba en cada `Agent` que `model ∈ MODELS[provider]` y emite un error
  con la lista de modelos válidos para ese provider si falla.

- **CompletionProvider personalizado** ([multi-agent-dsl-completion-provider.ts](../../packages/language/src/multi-agent-dsl-completion-provider.ts)):
  al ser `model` un STRING libre, Langium no sabría qué sugerir. La clase
  extiende `DefaultCompletionProvider` y, cuando detecta que el cursor está
  sobre la asignación `model` de un `Agent`, lee el `provider` ya tecleado y
  ofrece como sugerencias los modelos correspondientes. El resto de
  completados (keywords, referencias cruzadas, valores de `ProviderType`,
  etc.) sigue funcionando porque el `else` delega en `super.completionFor`.

### Generación de código

El generador construye el identificador que espera `init_chat_model` de
LangChain concatenando ambos campos:

```ts
export function toModel(agent: Agent): string {
    return `${agent.provider}:${agent.model}`;
}
```

Resultado: `init_chat_model(model="openai:gpt-5-nano", ...)`. Esta es además
la convención canónica de LangChain, por lo que la separación
provider/model encaja de forma natural con la herramienta destino.

## Consecuencias

- La lista de modelos puede actualizarse editando un único fichero
  TypeScript, sin tocar gramática ni AST ni regenerar la extensión.
- El editor ofrece autocompletado contextual de modelos filtrado por el
  provider declarado, y marca como error cualquier modelo desconocido para
  ese provider.
- La generación de código puede inyectar la API key correcta porque el
  provider es siempre explícito y forma parte del modelo de datos.
- Queda pavimentado el camino para automatizar la actualización del
  catálogo (CI, catálogo remoto, fetch a Ollama local) sin cambios en la
  arquitectura del lenguaje, solo añadiendo el mecanismo de refresco.
- A día de hoy la lista de modelos sigue siendo estática y se mantiene a
  mano: hay que recordar revisarla periódicamente hasta que se implemente
  el script de refresco automático.
- Los `.mad` existentes que usaban `model gpt` han tenido que migrarse a la
  sintaxis nueva (`provider openai` + `model "gpt-5-nano"`); cualquier
  fichero anterior es incompatible con la gramática actual.
