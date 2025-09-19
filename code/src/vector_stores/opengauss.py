from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from langchain_core.documents import Document
from langchain_opengauss import OpenGauss
from langchain_opengauss.config import OpenGaussSettings
from psycopg2 import sql

from .base import VectorDbBase

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

    from ..models import OpengaussIntegration


class OpenGaussDatabase(OpenGauss, VectorDbBase):

    def __init__(self, actor_input: OpengaussIntegration, embeddings: Embeddings) -> None:
        try:
            db_host = actor_input.opengaussHost
            db_port = actor_input.opengaussPort
            db_user = actor_input.opengaussUser
            db_password = actor_input.opengaussPassword
            db_name = actor_input.opengaussDBname or "postgres"

        except (ValueError, IndexError) as e:
            raise ValueError(
                "Could not construct openGauss connection parameters from actor_input. "
                "Ensure fields follow opengauss_input_model.py."
            ) from e


        dummy_vector = embeddings.embed_query("get dimension")
        embedding_dim = len(dummy_vector)
        settings = OpenGaussSettings(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            table_name=actor_input.opengaussTableName,
            embedding_dimension=embedding_dim,
        )

        super().__init__(embedding=embeddings, config=settings)

        self._dummy_vector: list[float] = dummy_vector

    @property
    def dummy_vector(self) -> list[float]:
        if not self._dummy_vector and self.embeddings:
            self._dummy_vector = self.embeddings.embed_query("dummy")
        return self._dummy_vector

    async def is_connected(self) -> bool:
        try:
            with self._get_cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
        except Exception:
            return False

    def get_by_item_id(self, item_id: str) -> list[Document]:
        """
        Get all document chunks associated with a specific item_id from the metadata.
        """
        if not item_id:
            return []

        query = sql.SQL("""
            SELECT id, metadata FROM {table}
            WHERE metadata ->> 'item_id' = %s
        """).format(table=sql.Identifier(self.config.table_name))
        docs = []
        with self._get_cursor() as cur:
            cur.execute(query, (item_id,))
            for row in cur.fetchall():
                doc_id, metadata = row
                metadata["chunk_id"] = doc_id
                docs.append(Document(page_content="", metadata=metadata))
        return docs

    def update_last_seen_at(self, ids: list[str], last_seen_at: int | None = None) -> None:
        """Update last_seen_at field in the database."""
        if not ids:
            return

        last_seen_at = last_seen_at or int(datetime.now(timezone.utc).timestamp())

        new_value_jsonb = json.dumps(last_seen_at)

        update_sql = sql.SQL("""
            UPDATE {table}
            SET metadata = jsonb_set(
                metadata,
                '{{last_seen_at}}',
                %s::jsonb,
                true
            )
            WHERE id = ANY(%s)
        """).format(table=sql.Identifier(self.config.table_name))

        with self._get_cursor() as cur:
            cur.execute(update_sql, (new_value_jsonb, ids))

    def delete_by_item_id(self, item_id: str) -> None:
        """Delete object by item_id."""
        if not item_id:
            return

        query = sql.SQL("""
            DELETE FROM {table}
            WHERE metadata ->> 'item_id' = %s
        """).format(table=sql.Identifier(self.config.table_name))
        with self._get_cursor() as cur:
            cur.execute(query, (item_id,))

    def delete_expired(self, expired_ts: int) -> None:
        """Delete objects from the index that are expired."""
        query = sql.SQL("""
            DELETE FROM {table}
            WHERE (metadata ->> 'last_seen_at')::bigint < %s
        """).format(table=sql.Identifier(self.config.table_name))
        with self._get_cursor() as cur:
            cur.execute(query, (expired_ts,))

    def get_by_id(self, id_: str) -> Document | None:
        """Get a document by id from the database.

        Used only for testing purposes.
        """
        results = self.get_by_ids([id_])
        return results[0] if results else None

    def get_all_ids(self) -> list[str]:
        """Get all document ids from the database.

        Used only for testing purposes.
        """
        query = sql.SQL("SELECT id FROM {table}").format(
            table=sql.Identifier(self.config.table_name)
        )
        with self._get_cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]

    def delete_all(self) -> None:
        """Delete all documents from the database.

        Used only for testing purposes.
        """
        self.delete(ids=None)

    def search_by_vector(
        self,
        vector: list[float],
        k: int = 4,
        filter_: dict | None = None
    ) -> list[Document]:
        """Search by vector and return the results."""
        return self.similarity_search_by_vector(embedding=vector, k=k, filter=filter_)
