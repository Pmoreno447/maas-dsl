# Configuración del entorno de desarrollo

## Estructura del proyecto

El proyecto sigue una arquitectura de monorepo con workspaces de npm, organizado en tres paquetes principales:

```
multiAgentDSL/
├── packages/
│   ├── language/     ← Gramática del DSL y lógica del generador
│   ├── cli/          ← Interfaz de línea de comandos
│   └── extension/    ← Extensión de VSCode
├── examples/         ← Modelos de ejemplo en el DSL
├── docs/             ← Documentación y prototipos
└── package.json      ← Configuración raíz del workspace
```

## Gestión de la compilación

El flujo de compilación de un proyecto Langium implica dos pasos diferenciados:

1. **Generación del AST** (`langium:generate`) → Lee la gramática `.langium` y genera automáticamente los tipos TypeScript que representan el árbol sintáctico abstracto del DSL. Este paso solo es estrictamente necesario cuando se modifica la gramática.

2. **Compilación TypeScript** (`tsc`) → Compila todos los paquetes del workspace a JavaScript ejecutable.

En proyectos de mayor escala, estos dos pasos se mantienen separados para evitar regenerar el AST innecesariamente, ya que la gramática suele ser estable. Sin embargo, dado que el proyecto se encuentra en una fase activa de desarrollo del metamodelo en la que la gramática evoluciona con frecuencia, se ha optado por unificar ambos pasos en un único comando de compilación, modificando el script `build` en el `package.json` raíz:

```json
"build": "npm run langium:generate && tsc -b tsconfig.build.json && npm run build --workspaces"
```

Esta decisión simplifica el flujo de trabajo durante el desarrollo, evitando errores difíciles de diagnosticar causados por un AST desactualizado respecto a la gramática. El coste asumido es un tiempo de compilación ligeramente superior, lo cual resulta aceptable en el contexto de un TFG.

## Flujo de trabajo habitual

```bash
# Compilar todo (gramática + TypeScript + extensión + CLI)
npm run build

# Ejecutar el generador sobre un modelo
node packages/cli/bin/cli.js generate examples/miModelo.mad

# Ejecutar el generador especificando carpeta de salida
node packages/cli/bin/cli.js generate examples/miModelo.mad -d ./output
```

## Notas sobre dependencias

Durante la configuración inicial se detectaron vulnerabilidades en la dependencia `lodash` utilizada por `langium-cli`. La solución propuesta por npm (`npm audit fix --force`) fue descartada ya que implicaba una bajada de versión de `langium-cli` a una versión con cambios disruptivos. Dado que las vulnerabilidades afectan únicamente a herramientas de desarrollo y no al código generado, se optó por mantener la versión actual y no aplicar la corrección forzada.