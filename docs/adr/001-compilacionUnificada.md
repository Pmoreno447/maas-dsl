# ADR 001 — Unificación del proceso de compilación

## Contexto

El flujo de compilación de un proyecto Langium implica dos pasos diferenciados: la generación del AST a partir de la gramática (`langium:generate`) y la compilación TypeScript (`tsc`). En proyectos estables estos pasos se mantienen separados para evitar regenerar el AST innecesariamente.

Adicionalmente, el paquete `cli` generado por `yo langium` no disponía de un paso de compilación real, ya que estaba pensado para distribuir el código fuente directamente. Esto requería compilarlo manualmente con `npx tsc` desde `packages/cli` cada vez que se modificaba el generador, lo que resultaba propenso a errores.

Por último, durante la configuración inicial se detectaron vulnerabilidades en `lodash` utilizado por `langium-cli`. La corrección propuesta por npm (`npm audit fix --force`) implicaba una bajada de versión con cambios disruptivos, por lo que fue descartada.

## Decisión

Se han tomado las siguientes medidas para simplificar el flujo de trabajo:

1. Unificar `langium:generate` y `tsc` en un único comando `npm run build` modificando el script en el `package.json` raíz:
```json
"build": "npm run langium:generate && tsc -b tsconfig.build.json && npm run build --workspaces"
```

2. Añadir un script `build` real en `packages/cli/package.json`:
```json
"build": "tsc"
```

3. Instalar `@types/node` en el paquete `cli` para resolver correctamente los módulos de Node.js:
```bash
npm install --save-dev @types/node
```

4. Mantener la versión actual de `langium-cli` sin aplicar `npm audit fix --force`, asumiendo el riesgo de las vulnerabilidades de `lodash` dado que afectan únicamente a herramientas de desarrollo.

## Consecuencias

- Un único comando `npm run build` compila todo el workspace.
- El tiempo de compilación es ligeramente superior al necesario cuando solo se modifica el generador, ya que siempre se regenera el AST.
- Las vulnerabilidades de `lodash` permanecen sin resolver hasta que `langium-cli` actualice su dependencia.