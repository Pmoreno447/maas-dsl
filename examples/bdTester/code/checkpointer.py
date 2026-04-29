from config import DB_URI
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
