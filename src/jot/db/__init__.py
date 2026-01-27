"""Database access layer for jot.

This package contains database repositories and data access logic.
The db package MUST use only stdlib (sqlite3) and primitive types.
It MUST NOT import from core/, commands/, or monitor/ to maintain clean architecture.
"""

from jot.db.connection import get_connection
from jot.db.exceptions import DatabaseError
from jot.db.migrations import get_schema_version, migrate_schema

# Note: TaskRepository and EventRepository are not imported here to avoid
# circular imports (they depend on core.exceptions which imports db.exceptions).
# Import them directly from jot.db.repository instead.

__all__ = [
    "get_connection",
    "get_schema_version",
    "migrate_schema",
    "DatabaseError",
]
