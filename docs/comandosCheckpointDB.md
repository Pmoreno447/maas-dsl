# Comandos para inspeccionar checkpoints

Notas rápidas para comprobar que LangGraph está persistiendo bien en los contenedores Docker.

## Contenedores

- **`langgraph-mongo`** — usuario `mongo`, password `password`. DB de checkpoints: `checkpointing_db`.
  - Colecciones (versión sync `MongoDBSaver`): `checkpoints`, `checkpoint_writes`.
  - Colecciones (versión async `AsyncMongoDBSaver`): `checkpoints_aio`, `checkpoint_writes_aio`.
- **`langgraph-postgres`** — Postgres 16, usuario `postgres`, password `password`, DB `langgraph`.
  - Tablas que crea `AsyncPostgresSaver.setup()`: `checkpoints`, `checkpoint_writes`, `checkpoint_blobs`, `checkpoint_migrations`.

## MongoDB

Listar bases de datos:

```bash
docker exec -it langgraph-mongo mongosh -u mongo -p password \
  --eval "db.adminCommand('listDatabases')"
```

Listar colecciones de `checkpointing_db`:

```bash
docker exec -it langgraph-mongo mongosh -u mongo -p password \
  --eval "db.getSiblingDB('checkpointing_db').getCollectionNames()"
```

Contar documentos de cada colección:

```bash
docker exec -it langgraph-mongo mongosh -u mongo -p password \
  --eval "db.getSiblingDB('checkpointing_db').getCollectionNames().forEach(c => print(c, db.getSiblingDB('checkpointing_db')[c].countDocuments()))"
```

Ver un checkpoint de ejemplo:

```bash
docker exec -it langgraph-mongo mongosh -u mongo -p password \
  --eval "db.getSiblingDB('checkpointing_db').checkpoints.findOne({}, {thread_id:1, checkpoint_id:1, metadata:1})"
```

Borrar todo y empezar limpio (al reiniciar el grafo, `setup()` recrea las colecciones):

```bash
docker exec -it langgraph-mongo mongosh -u mongo -p password \
  --eval "db.getSiblingDB('checkpointing_db').dropDatabase()"
```

## Postgres

Listar tablas:

```bash
docker exec -it langgraph-postgres psql -U postgres -d langgraph -c "\dt"
```

Contar checkpoints:

```bash
docker exec -it langgraph-postgres psql -U postgres -d langgraph -c "SELECT COUNT(*) FROM checkpoints;"
```

Contar todas las tablas relevantes de una vez:

```bash
docker exec -it langgraph-postgres psql -U postgres -d langgraph -c \
  "SELECT 'checkpoints' AS tabla, COUNT(*) FROM checkpoints
   UNION ALL SELECT 'checkpoint_writes', COUNT(*) FROM checkpoint_writes
   UNION ALL SELECT 'checkpoint_blobs', COUNT(*) FROM checkpoint_blobs;"
```

Sesión interactiva de `psql`:

```bash
docker exec -it langgraph-postgres psql -U postgres -d langgraph
```

## Notas

- Si cambias de grafo y reusas la misma DB, **no pasa nada** mientras los `thread_id` sean distintos: el esquema es genérico (blobs serializados).
- Si reusas un mismo `thread_id` con un `State` incompatible al anterior, ese thread fallará al reanudar — solución: nuevo `thread_id` o `dropDatabase()`.
