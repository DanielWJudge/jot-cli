"""Database-specific exceptions.

This module is part of the db package. DatabaseError is defined here to maintain
clean architectural boundaries (db/ doesn't import from core/).

Note: While DatabaseError is logically part of the JotError hierarchy, it cannot
inherit from JotError directly without creating a circular dependency. Instead,
it implements the same interface (message and exit_code attributes) and is
treated as part of the exception hierarchy through duck typing.
"""


class DatabaseError(Exception):
    """Raised when database operations fail.

    This is a system error with exit code 2. It implements the same interface
    as JotError (message and exit_code attributes) but doesn't inherit from it
    to maintain clean architectural boundaries.
    """

    exit_code: int = 2

    def __init__(self, message: str) -> None:
        """Initialize database error.

        Args:
            message: Error message describing what went wrong.
        """
        self.message = message
        super().__init__(message)
