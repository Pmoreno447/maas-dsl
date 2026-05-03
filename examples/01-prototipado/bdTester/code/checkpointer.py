import contextlib
from langgraph.checkpoint.memory import InMemorySaver


@contextlib.contextmanager
def generate_checkpointer():
    checkpointer = InMemorySaver()
    yield checkpointer
