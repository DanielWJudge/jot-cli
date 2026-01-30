"""IPC protocol for message serialization and deserialization.

This module implements the NDJSON (Newline Delimited JSON) protocol
for IPC communication between the CLI process and the monitor window process.

Message format: {"event": "EVENT_NAME", "task_id": "uuid", "timestamp": "iso8601"}
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from jot.core.exceptions import IPCError
from jot.ipc.events import IPCEvent


def serialize_message(event: IPCEvent, task_id: str, timestamp: str | None = None) -> str:
    """Serialize an IPC event message to NDJSON format.

    Args:
        event: IPC event type (from IPCEvent enum)
        task_id: Task identifier (string, typically UUID format)
        timestamp: ISO 8601 timestamp string (generated if None)

    Returns:
        Single-line JSON string ending with newline character

    Example:
        >>> serialize_message(IPCEvent.TASK_CREATED, "task-123")
        '{"event":"TASK_CREATED","task_id":"task-123","timestamp":"2024-01-01T12:00:00+00:00"}\\n'
    """
    if timestamp is None:
        # Generate timestamp in ISO 8601 format with Z suffix for consistency
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    message = {
        "event": event.value,
        "task_id": task_id,
        "timestamp": timestamp,
    }

    # Serialize to compact JSON (no extra whitespace)
    json_line = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
    return json_line + "\n"


def deserialize_message(line: str) -> dict[str, Any]:
    """Deserialize an NDJSON message line to a dictionary.

    Args:
        line: Single line containing JSON object (may include trailing newline)

    Returns:
        Dictionary with keys: event, task_id, timestamp

    Raises:
        IPCError: If message format is invalid, missing required fields,
                  contains null/empty values, invalid types, or invalid event name

    Example:
        >>> deserialize_message('{"event":"TASK_CREATED","task_id":"task-123","timestamp":"2024-01-01T12:00:00Z"}\\n')
        {'event': 'TASK_CREATED', 'task_id': 'task-123', 'timestamp': '2024-01-01T12:00:00Z'}
    """
    # Strip whitespace before parsing
    original_line = line
    line = line.strip()

    # Handle empty lines
    if not line:
        raise IPCError("Empty message line")

    # Parse JSON
    try:
        message = json.loads(line)
    except json.JSONDecodeError as e:
        # Include truncated message content for debugging
        truncated = original_line[:100]
        raise IPCError(f"Invalid JSON format in message {truncated!r}: {e}") from e

    # Validate message is a dict
    if not isinstance(message, dict):
        truncated = str(message)[:100]
        raise IPCError(
            f"Message must be a JSON object, got {type(message).__name__}: {truncated!r}"
        )

    # Validate required fields exist
    if "event" not in message:
        raise IPCError(f"Missing required field: event in message: {str(message)[:100]!r}")

    if "task_id" not in message:
        raise IPCError(f"Missing required field: task_id in message: {str(message)[:100]!r}")

    if "timestamp" not in message:
        raise IPCError(f"Missing required field: timestamp in message: {str(message)[:100]!r}")

    # Validate event field is not null and is a string
    event_value = message["event"]
    if event_value is None:
        raise IPCError("event field cannot be null")

    # Validate event name is a valid IPCEvent
    try:
        IPCEvent(event_value)
    except (ValueError, TypeError):
        valid_events = ", ".join(e.value for e in IPCEvent)
        raise IPCError(
            f"Invalid event name: {event_value!r}. Valid events: {valid_events}"
        ) from None

    # Validate task_id is not null or empty, and is a string
    task_id_value = message["task_id"]
    if task_id_value is None:
        raise IPCError("task_id field cannot be null")
    if not isinstance(task_id_value, str):
        raise IPCError(f"task_id must be a string, got {type(task_id_value).__name__}")
    if task_id_value == "":
        raise IPCError("task_id field cannot be empty")

    # Validate timestamp is not null and is a string
    timestamp_value = message["timestamp"]
    if timestamp_value is None:
        raise IPCError("timestamp field cannot be null")
    if not isinstance(timestamp_value, str):
        raise IPCError(f"timestamp must be a string, got {type(timestamp_value).__name__}")

    return message
