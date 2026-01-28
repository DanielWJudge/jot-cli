"""Task domain models and business logic.

This module defines the core domain models for tasks and task events,
providing Pydantic-based validation and type safety for the application layer.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TaskState(str, Enum):
    """Task state enumeration.

    A task can be in one of four states:
    - ACTIVE: Currently being worked on
    - COMPLETED: Finished successfully
    - CANCELLED: Abandoned or decided not to do
    - DEFERRED: Postponed for later
    """

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DEFERRED = "deferred"


class Task(BaseModel):
    """Task domain model.

    Represents a single task with its current state and metadata.

    Attributes:
        id: Unique task identifier (UUID)
        description: Task description (what needs to be done)
        state: Current task state
        created_at: When task was created (UTC)
        updated_at: When task was last updated (UTC)
        completed_at: When task was completed (optional)
        cancelled_at: When task was cancelled (optional)
        cancel_reason: Reason for cancellation (optional)
        deferred_until: When deferred task should be revisited (optional)
    """

    id: str = Field(description="Unique task identifier")
    description: str = Field(min_length=1, max_length=2000, description="Task description")
    state: TaskState = Field(description="Current task state")
    created_at: datetime = Field(description="Creation timestamp (UTC)")
    updated_at: datetime = Field(description="Last update timestamp (UTC)")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp (UTC)")
    cancelled_at: datetime | None = Field(default=None, description="Cancellation timestamp (UTC)")
    cancel_reason: str | None = Field(default=None, description="Reason for cancellation")
    deferred_until: datetime | None = Field(
        default=None, description="When to revisit deferred task"
    )

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Validate description is not empty or whitespace-only.

        Args:
            v: Description value to validate

        Returns:
            Stripped description string

        Raises:
            ValueError: If description is empty or whitespace-only
        """
        if not v or v.strip() == "":
            raise ValueError("Description cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "description": "Review PR for authentication feature",
                    "state": "active",
                    "created_at": "2026-01-27T10:00:00Z",
                    "updated_at": "2026-01-27T10:00:00Z",
                    "completed_at": None,
                    "cancelled_at": None,
                    "cancel_reason": None,
                    "deferred_until": None,
                }
            ]
        }
    }


class TaskEvent(BaseModel):
    """Task event for audit trail.

    Represents a state change or other significant event in a task's lifecycle.

    Attributes:
        id: Event ID (auto-increment in database)
        task_id: Task this event relates to
        event_type: Type of event (CREATED, COMPLETED, CANCELLED, DEFERRED)
        timestamp: When event occurred (UTC)
        metadata: Optional JSON metadata (e.g., reason for cancellation)
    """

    id: int = Field(description="Event ID")
    task_id: str = Field(description="Task ID this event relates to")
    event_type: Literal["CREATED", "COMPLETED", "CANCELLED", "DEFERRED"] = Field(
        description="Event type (CREATED, COMPLETED, CANCELLED, DEFERRED)"
    )
    timestamp: datetime = Field(description="Event timestamp (UTC)")
    metadata: str | None = Field(default=None, description="Optional JSON metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "event_type": "CREATED",
                    "timestamp": "2026-01-27T10:00:00Z",
                    "metadata": None,
                }
            ]
        }
    }
