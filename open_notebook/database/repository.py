import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

from loguru import logger
from sblpy.connection import SurrealSyncConnection


@contextmanager
def db_connection():
    connection = SurrealSyncConnection(
        host=os.environ["SURREAL_ADDRESS"],
        port=int(os.environ["SURREAL_PORT"]),
        user=os.environ["SURREAL_USER"],
        password=os.environ["SURREAL_PASS"],
        namespace=os.environ["SURREAL_NAMESPACE"],
        database=os.environ["SURREAL_DATABASE"],
        max_size=4**20,
        open_timeout = .1,
        encrypted = os.environ["ENCRYPTED_CONNECTION"],
        max_retries = 10,
        retry_delay = 0.1
    )
    try:
        yield connection
    finally:
        connection.socket.close()


def repo_query(query_str: str, vars: Optional[Dict[str, Any]] = None):
    with db_connection() as connection:
        try:
            result = connection.query(query_str, vars)
            return result
        except Exception as e:
            logger.critical(f"Query: {query_str}")
            logger.exception(e)
            raise


def repo_create(table: str, data: Dict[str, Any]):
    query = f"CREATE {table} CONTENT {data};"
    # vars = {"table": table, "data": data}
    return repo_query(query)

def repo_upsert(table: str, data: Dict[str, Any]):
    query = f"UPSERT {table} CONTENT {data};"
    return repo_query(query)


def repo_update(id: str, data: Dict[str, Any]):
    query = "UPDATE $id CONTENT $data;"
    vars = {"id": id, "data": data}
    return repo_query(query, vars)


def repo_delete(id: str):
    query = "DELETE $id;"
    vars = {"id": id}
    return repo_query(query, vars)


def repo_relate(source: str, relationship: str, target: str):
    query = f"RELATE {source}->{relationship}->{target}"
    # CONTENT $content;"
    # vars = {
    #     "source": source,
    #     "relationship": relationship,
    #     "target": target,
    #  #   "content": {},  # You can add properties to the relation here if needed
    # }
    result = repo_query(query)
    return result
