const dbImport = 'from config import DB_URI'

// ─── Templates ──────────────────────────────────────────────────────────────

export const checkpointer = {
    Postgre: `${dbImport}
import contextlib
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row


@contextlib.asynccontextmanager
async def generate_checkpointer():
    conn = await AsyncConnection.connect(
        DB_URI,
        autocommit=True,
        row_factory=dict_row
    )
    try:
        checkpointer = AsyncPostgresSaver(conn)
        await checkpointer.setup()
        yield checkpointer
    finally:
        await conn.close()
`,
    MongoDB:`${dbImport}
import contextlib
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient


@contextlib.asynccontextmanager
async def generate_checkpointer():
    client = MongoClient(DB_URI)
    try:
        checkpointer = MongoDBSaver(client)
        yield checkpointer
    finally:
        client.close()`,

    InMemorySaver: `import contextlib
from langgraph.checkpoint.memory import InMemorySaver


@contextlib.contextmanager
def generate_checkpointer():
    checkpointer = InMemorySaver()
    yield checkpointer
`
}