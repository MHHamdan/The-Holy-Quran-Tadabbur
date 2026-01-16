"""
SurrealDB async client for Knowledge Graph operations.

Provides:
- Connection management
- CRUD operations for KG entities
- Graph traversal queries
- Schema initialization
"""

import logging
from typing import Any, Dict, List, Optional, TypeVar, Type
from contextlib import asynccontextmanager
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.kg.schema import get_schema_sql, get_query, SCHEMA_VERSION

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class SurrealDBError(Exception):
    """Base exception for SurrealDB errors."""
    pass


class SurrealDBConnectionError(SurrealDBError):
    """Connection failed."""
    pass


class SurrealDBQueryError(SurrealDBError):
    """Query execution failed."""
    pass


class KGClient:
    """
    Async client for SurrealDB Knowledge Graph operations.

    Uses HTTP API for compatibility and simplicity.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        namespace: str = "tadabbur",
        database: str = "quran_kg",
        username: str = None,
        password: str = None,
    ):
        self.host = host or getattr(settings, "surreal_host", "localhost")
        self.port = port or getattr(settings, "surreal_port", 8000)
        self.namespace = namespace
        self.database = database
        self.username = username or getattr(settings, "surreal_user", "root")
        self.password = password or getattr(settings, "surreal_pass", "root")

        self.base_url = f"http://{self.host}:{self.port}"
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.username, self.password),
                headers={
                    "Accept": "application/json",
                    "NS": self.namespace,
                    "DB": self.database,
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # =========================================================================
    # RAW QUERY EXECUTION
    # =========================================================================

    async def query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a SurrealQL query.

        Args:
            sql: SurrealQL statement
            params: Optional parameters for the query

        Returns:
            List of result objects
        """
        try:
            # Substitute parameters directly into SQL
            # SurrealDB REST API expects plain text SQL
            query_sql = sql
            if params:
                for key, value in params.items():
                    placeholder = f"${key}"
                    if isinstance(value, str):
                        # Escape single quotes in strings
                        escaped = value.replace("'", "''")
                        query_sql = query_sql.replace(placeholder, f"'{escaped}'")
                    elif isinstance(value, bool):
                        query_sql = query_sql.replace(placeholder, str(value).lower())
                    elif isinstance(value, (int, float)):
                        query_sql = query_sql.replace(placeholder, str(value))
                    elif isinstance(value, (list, dict)):
                        # Format as JSON, but filter out None values for SurrealDB compatibility
                        import json

                        def remove_none(obj):
                            """Recursively remove None values from dicts."""
                            if isinstance(obj, dict):
                                return {k: remove_none(v) for k, v in obj.items() if v is not None}
                            elif isinstance(obj, list):
                                return [remove_none(item) for item in obj]
                            return obj

                        cleaned = remove_none(value)
                        query_sql = query_sql.replace(placeholder, json.dumps(cleaned))
                    elif value is None:
                        query_sql = query_sql.replace(placeholder, "NONE")
                    else:
                        query_sql = query_sql.replace(placeholder, str(value))

            response = await self.client.post(
                "/sql",
                content=query_sql,
                headers={"Content-Type": "text/plain"}
            )
            response.raise_for_status()

            data = response.json()

            # SurrealDB returns array of results (one per statement)
            results = []
            for result in data:
                if result.get("status") == "ERR":
                    raise SurrealDBQueryError(result.get("detail", "Unknown error"))
                if "result" in result:
                    results.extend(result["result"] if isinstance(result["result"], list) else [result["result"]])

            return results

        except httpx.HTTPStatusError as e:
            raise SurrealDBQueryError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise SurrealDBConnectionError(f"Connection error: {e}")

    async def execute(self, sql: str) -> bool:
        """
        Execute a SurrealQL statement (no return value expected).

        Args:
            sql: SurrealQL statement

        Returns:
            True if successful
        """
        await self.query(sql)
        return True

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """Check if SurrealDB is available."""
        try:
            response = await self.client.get("/health")
            return {
                "status": "ok" if response.status_code == 200 else "error",
                "host": self.host,
                "port": self.port,
                "namespace": self.namespace,
                "database": self.database,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "host": self.host,
                "port": self.port,
            }

    # =========================================================================
    # SCHEMA MANAGEMENT
    # =========================================================================

    async def init_schema(self) -> bool:
        """
        Initialize the Knowledge Graph schema.

        Creates all tables, indexes, and constraints.
        """
        logger.info(f"Initializing KG schema v{SCHEMA_VERSION}")

        schema_sql = get_schema_sql()

        # Split by semicolons and execute each statement
        statements = [s.strip() for s in schema_sql.split(";") if s.strip() and not s.strip().startswith("--")]

        for stmt in statements:
            if stmt:
                try:
                    await self.execute(stmt + ";")
                except SurrealDBQueryError as e:
                    # Skip "already exists" errors
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Schema statement warning: {e}")

        logger.info("KG schema initialized successfully")
        return True

    async def get_schema_version(self) -> Optional[str]:
        """Get the current schema version from metadata."""
        try:
            results = await self.query(
                "SELECT * FROM schema_meta WHERE id = 'schema_meta:version';"
            )
            if results:
                return results[0].get("version")
            return None
        except SurrealDBQueryError:
            return None

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    async def create(self, table: str, data: Dict[str, Any], record_id: str = None) -> Dict[str, Any]:
        """
        Create a new record.

        Args:
            table: Table name
            data: Record data
            record_id: Optional specific record ID

        Returns:
            Created record
        """
        if record_id:
            sql = f"CREATE {table}:{record_id} CONTENT $data;"
        else:
            sql = f"CREATE {table} CONTENT $data;"

        results = await self.query(sql, {"data": data})
        return results[0] if results else {}

    async def get(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.

        Args:
            record_id: Full record ID (e.g., "ayah:18:83")

        Returns:
            Record data or None
        """
        results = await self.query(f"SELECT * FROM {record_id};")
        return results[0] if results else None

    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a record.

        Args:
            record_id: Full record ID
            data: Fields to update

        Returns:
            Updated record
        """
        results = await self.query(f"UPDATE {record_id} MERGE $data;", {"data": data})
        return results[0] if results else {}

    async def upsert(self, table: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert a record (create or update).

        For SurrealDB 1.x, uses UPDATE with MERGE which:
        - Creates record if it doesn't exist
        - Merges with existing data if it does exist
        - Preserves schema defaults like _created_at

        Args:
            table: Table name
            record_id: Record ID within table
            data: Record data

        Returns:
            Upserted record
        """
        full_id = f"{table}:{record_id}"
        # SurrealDB 1.x: UPDATE MERGE creates if not exists, merges if exists
        results = await self.query(
            f"UPDATE {full_id} MERGE $data;",
            {"data": data}
        )
        return results[0] if results else {}

    async def delete(self, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            record_id: Full record ID

        Returns:
            True if deleted
        """
        await self.query(f"DELETE {record_id};")
        return True

    async def select(
        self,
        table: str,
        where: str = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Select records from a table.

        Args:
            table: Table name
            where: Optional WHERE clause
            order_by: Optional ORDER BY clause
            limit: Optional limit
            offset: Optional offset

        Returns:
            List of records
        """
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" START {offset}"
        sql += ";"

        return await self.query(sql)

    # =========================================================================
    # EDGE OPERATIONS
    # =========================================================================

    async def create_edge(
        self,
        edge_type: str,
        from_id: str,
        to_id: str,
        data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Create a graph edge between two records.

        Args:
            edge_type: Edge table name (e.g., "next", "explains")
            from_id: Source record ID
            to_id: Target record ID
            data: Optional edge attributes

        Returns:
            Created edge
        """
        content = data or {}
        sql = f"RELATE {from_id}->{edge_type}->{to_id} CONTENT $content;"
        results = await self.query(sql, {"content": content})
        return results[0] if results else {}

    async def get_edges(
        self,
        from_id: str = None,
        to_id: str = None,
        edge_type: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Get edges matching criteria.

        Args:
            from_id: Optional source record ID
            to_id: Optional target record ID
            edge_type: Optional edge type

        Returns:
            List of edges
        """
        if from_id and to_id:
            sql = f"SELECT * FROM {edge_type or '*'} WHERE in = {from_id} AND out = {to_id};"
        elif from_id:
            sql = f"SELECT * FROM {edge_type or '*'} WHERE in = {from_id};"
        elif to_id:
            sql = f"SELECT * FROM {edge_type or '*'} WHERE out = {to_id};"
        else:
            sql = f"SELECT * FROM {edge_type};" if edge_type else "SELECT * FROM *;"

        return await self.query(sql)

    async def delete_edge(self, from_id: str, edge_type: str, to_id: str) -> bool:
        """
        Delete a specific edge.

        Args:
            from_id: Source record ID
            edge_type: Edge table name
            to_id: Target record ID

        Returns:
            True if deleted
        """
        await self.query(f"DELETE {edge_type} WHERE in = {from_id} AND out = {to_id};")
        return True

    # =========================================================================
    # GRAPH TRAVERSAL
    # =========================================================================

    async def traverse(
        self,
        start_id: str,
        edge_type: str,
        direction: str = "out",
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Traverse graph from a starting node.

        Args:
            start_id: Starting record ID
            edge_type: Edge type to follow
            direction: "out" (follow outgoing) or "in" (follow incoming)
            depth: How many hops to traverse

        Returns:
            List of reached nodes
        """
        arrow = "->" if direction == "out" else "<-"
        path = f"{arrow}{edge_type}{arrow}" * depth

        sql = f"SELECT * FROM {start_id}{path}*;"
        return await self.query(sql)

    async def get_neighbors(
        self,
        record_id: str,
        edge_types: List[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all neighbors of a node.

        Args:
            record_id: Record ID
            edge_types: Optional list of edge types to follow

        Returns:
            Dict mapping direction+edge_type to neighbor records
        """
        neighbors = {}

        types = edge_types or ["next", "thematic_link", "explains", "supported_by", "involves", "located_in", "tagged_with"]

        for edge_type in types:
            # Outgoing
            out_results = await self.query(f"SELECT out.* FROM {edge_type} WHERE in = {record_id};")
            if out_results:
                neighbors[f"out_{edge_type}"] = out_results

            # Incoming
            in_results = await self.query(f"SELECT in.* FROM {edge_type} WHERE out = {record_id};")
            if in_results:
                neighbors[f"in_{edge_type}"] = in_results

        return neighbors

    # =========================================================================
    # NAMED QUERIES
    # =========================================================================

    async def run_named_query(self, query_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run a predefined named query.

        Args:
            query_name: Name of the query (from schema.py)
            params: Query parameters

        Returns:
            Query results
        """
        sql = get_query(query_name)

        # Replace parameter placeholders
        for key, value in params.items():
            if isinstance(value, str):
                sql = sql.replace(f"${key}", f'"{value}"')
            elif isinstance(value, list):
                sql = sql.replace(f"${key}", str(value))
            else:
                sql = sql.replace(f"${key}", str(value))

        return await self.query(sql)

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    async def bulk_create(self, table: str, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple records in a single transaction.

        Args:
            table: Table name
            records: List of record data

        Returns:
            List of created records
        """
        results = []
        # Use transaction for atomicity
        await self.execute("BEGIN TRANSACTION;")
        try:
            for record in records:
                record_id = record.pop("id", None)
                if record_id:
                    result = await self.create(table, record, record_id.split(":")[-1])
                else:
                    result = await self.create(table, record)
                results.append(result)
            await self.execute("COMMIT TRANSACTION;")
        except Exception as e:
            await self.execute("CANCEL TRANSACTION;")
            raise e

        return results

    async def bulk_upsert(self, table: str, records: List[Dict[str, Any]], id_field: str = "id") -> int:
        """
        Upsert multiple records.

        Args:
            table: Table name
            records: List of record data (must include id_field)
            id_field: Field containing the record ID

        Returns:
            Number of records processed
        """
        count = 0
        await self.execute("BEGIN TRANSACTION;")
        try:
            for record in records:
                record_id = record.get(id_field)
                if record_id:
                    # Extract just the ID part after the colon
                    id_part = record_id.split(":")[-1] if ":" in record_id else record_id
                    await self.upsert(table, id_part, record)
                    count += 1
            await self.execute("COMMIT TRANSACTION;")
        except Exception as e:
            await self.execute("CANCEL TRANSACTION;")
            raise e

        return count


# =============================================================================
# SINGLETON CLIENT
# =============================================================================

_kg_client: Optional[KGClient] = None


def get_kg_client() -> KGClient:
    """Get or create the KG client singleton."""
    global _kg_client
    if _kg_client is None:
        _kg_client = KGClient()
    return _kg_client


async def close_kg_client():
    """Close the KG client."""
    global _kg_client
    if _kg_client:
        await _kg_client.close()
        _kg_client = None


@asynccontextmanager
async def kg_session():
    """Context manager for KG client session."""
    client = get_kg_client()
    try:
        yield client
    finally:
        pass  # Don't close singleton
