"""Test suite for IPC protocol module."""

from __future__ import annotations

from datetime import datetime

import pytest

from jot.core.exceptions import IPCError
from jot.ipc.events import IPCEvent
from jot.ipc.protocol import deserialize_message, serialize_message


class TestIPCEvent:
    """Test IPCEvent enum."""

    def test_enum_values_exist(self) -> None:
        """Test all required enum values exist."""
        assert IPCEvent.TASK_CREATED == "TASK_CREATED"
        assert IPCEvent.TASK_COMPLETED == "TASK_COMPLETED"
        assert IPCEvent.TASK_CANCELLED == "TASK_CANCELLED"
        assert IPCEvent.TASK_DEFERRED == "TASK_DEFERRED"
        assert IPCEvent.TASK_RESUMED == "TASK_RESUMED"
        assert IPCEvent.CONFIG_CHANGED == "CONFIG_CHANGED"

    def test_enum_inherits_from_str_and_enum(self) -> None:
        """Test IPCEvent inherits from both str and Enum."""
        from enum import Enum

        assert issubclass(IPCEvent, str)
        assert issubclass(IPCEvent, Enum)

    def test_enum_values_are_strings(self) -> None:
        """Test enum values are strings."""
        assert isinstance(IPCEvent.TASK_CREATED, str)
        assert isinstance(IPCEvent.TASK_COMPLETED, str)
        assert isinstance(IPCEvent.TASK_CANCELLED, str)
        assert isinstance(IPCEvent.TASK_DEFERRED, str)
        assert isinstance(IPCEvent.TASK_RESUMED, str)
        assert isinstance(IPCEvent.CONFIG_CHANGED, str)

    def test_enum_values_use_screaming_snake_case(self) -> None:
        """Test all enum values use SCREAMING_SNAKE_CASE."""
        for event in IPCEvent:
            assert event.value.isupper()
            assert "_" in event.value or event.value.isalpha()
            # Check no lowercase letters
            assert event.value == event.value.upper()

    def test_enum_string_conversion(self) -> None:
        """Test enum can be converted to string."""
        # When Enum inherits from str, the enum member IS a string
        assert IPCEvent.TASK_CREATED == "TASK_CREATED"
        assert IPCEvent.TASK_COMPLETED == "TASK_COMPLETED"
        # Can also access via .value
        assert IPCEvent.TASK_CREATED.value == "TASK_CREATED"
        assert IPCEvent.TASK_COMPLETED.value == "TASK_COMPLETED"

    def test_enum_has_docstring(self) -> None:
        """Test IPCEvent enum has docstring."""
        assert IPCEvent.__doc__ is not None
        assert len(IPCEvent.__doc__.strip()) > 0


class TestSerializeMessage:
    """Test serialize_message function."""

    @pytest.mark.parametrize(
        "event",
        [
            IPCEvent.TASK_CREATED,
            IPCEvent.TASK_COMPLETED,
            IPCEvent.TASK_CANCELLED,
            IPCEvent.TASK_DEFERRED,
            IPCEvent.TASK_RESUMED,
            IPCEvent.CONFIG_CHANGED,
        ],
    )
    def test_serialize_with_all_event_types(self, event: IPCEvent) -> None:
        """Test serialize_message with all event types."""
        task_id = "test-task-123"
        result = serialize_message(event, task_id)

        # Should be a single line ending with \n
        assert result.endswith("\n")
        assert result.count("\n") == 1

        # Should be valid JSON
        import json

        line = result.strip()
        parsed = json.loads(line)
        assert parsed["event"] == event.value
        assert parsed["task_id"] == task_id
        assert "timestamp" in parsed

    def test_serialize_generates_timestamp_when_none(self) -> None:
        """Test serialize_message generates timestamp when None provided."""
        result = serialize_message(IPCEvent.TASK_CREATED, "test-123")

        import json

        parsed = json.loads(result.strip())
        assert "timestamp" in parsed
        # Should be ISO 8601 format
        timestamp_str = parsed["timestamp"]
        # Try to parse as ISO 8601
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    def test_serialize_uses_provided_timestamp(self) -> None:
        """Test serialize_message uses provided timestamp."""
        timestamp = "2024-01-01T12:00:00Z"
        result = serialize_message(IPCEvent.TASK_CREATED, "test-123", timestamp)

        import json

        parsed = json.loads(result.strip())
        assert parsed["timestamp"] == timestamp

    def test_serialize_format_is_ndjson(self) -> None:
        """Test serialized format is NDJSON (single JSON object per line)."""
        result = serialize_message(IPCEvent.TASK_CREATED, "test-123")

        # Should be single line ending with \n
        assert result.endswith("\n")
        lines = result.strip().split("\n")
        assert len(lines) == 1

        # Should be valid JSON
        import json

        json.loads(lines[0])

    def test_serialize_includes_required_fields(self) -> None:
        """Test serialized message includes all required fields."""
        result = serialize_message(IPCEvent.TASK_COMPLETED, "task-uuid-456")

        import json

        parsed = json.loads(result.strip())
        assert "event" in parsed
        assert "task_id" in parsed
        assert "timestamp" in parsed
        assert parsed["event"] == "TASK_COMPLETED"
        assert parsed["task_id"] == "task-uuid-456"

    def test_serialize_allows_empty_string_task_id(self) -> None:
        """Test serialize_message allows empty string task_id (validation on deserialize)."""
        result = serialize_message(IPCEvent.TASK_CREATED, "")

        import json

        parsed = json.loads(result.strip())
        assert parsed["task_id"] == ""

        # But deserializing it should fail validation
        with pytest.raises(IPCError) as exc_info:
            deserialize_message(result)
        assert "empty" in str(exc_info.value).lower()

    def test_serialize_handles_special_characters_in_task_id(self) -> None:
        """Test serialize_message handles special characters in task_id."""
        task_id = "test-task-123!@#$%^&*()"
        result = serialize_message(IPCEvent.TASK_CREATED, task_id)

        import json

        parsed = json.loads(result.strip())
        assert parsed["task_id"] == task_id


class TestDeserializeMessage:
    """Test deserialize_message function."""

    def test_deserialize_valid_message(self) -> None:
        """Test deserialize_message with valid message."""
        line = '{"event": "TASK_CREATED", "task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z"}\n'
        result = deserialize_message(line)

        assert result["event"] == "TASK_CREATED"
        assert result["task_id"] == "test-123"
        assert result["timestamp"] == "2024-01-01T12:00:00Z"

    def test_deserialize_strips_whitespace(self) -> None:
        """Test deserialize_message strips whitespace before parsing."""
        line = '   {"event": "TASK_COMPLETED", "task_id": "test-456", "timestamp": "2024-01-01T12:00:00Z"}   \n'
        result = deserialize_message(line)

        assert result["event"] == "TASK_COMPLETED"
        assert result["task_id"] == "test-456"

    def test_deserialize_returns_dict_with_required_keys(self) -> None:
        """Test deserialize_message returns dict with required keys."""
        line = '{"event": "TASK_CANCELLED", "task_id": "test-789", "timestamp": "2024-01-01T12:00:00Z"}\n'
        result = deserialize_message(line)

        assert isinstance(result, dict)
        assert "event" in result
        assert "task_id" in result
        assert "timestamp" in result

    def test_deserialize_raises_on_invalid_json(self) -> None:
        """Test deserialize_message raises IPCError on invalid JSON."""
        line = '{"event": "TASK_CREATED", invalid json}\n'

        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)

        assert "Invalid message format" in str(exc_info.value) or "JSON" in str(exc_info.value)

    def test_deserialize_raises_on_missing_event_field(self) -> None:
        """Test deserialize_message raises IPCError on missing event field."""
        line = '{"task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z"}\n'

        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)

        assert "event" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_deserialize_raises_on_missing_task_id_field(self) -> None:
        """Test deserialize_message raises IPCError on missing task_id field."""
        line = '{"event": "TASK_CREATED", "timestamp": "2024-01-01T12:00:00Z"}\n'

        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)

        assert "task_id" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()

    def test_deserialize_raises_on_missing_timestamp_field(self) -> None:
        """Test deserialize_message raises IPCError on missing timestamp field."""
        line = '{"event": "TASK_CREATED", "task_id": "test-123"}\n'

        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)

        assert (
            "timestamp" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()
        )

    def test_deserialize_raises_on_invalid_event_name(self) -> None:
        """Test deserialize_message raises IPCError on invalid event name."""
        line = '{"event": "INVALID_EVENT", "task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z"}\n'

        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)

        assert "event" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_deserialize_handles_empty_line(self) -> None:
        """Test deserialize_message handles empty line."""
        line = "\n"

        with pytest.raises(IPCError):
            deserialize_message(line)

    def test_deserialize_round_trip(self) -> None:
        """Test round-trip serialization/deserialization."""
        event = IPCEvent.TASK_DEFERRED
        task_id = "round-trip-test-123"

        serialized = serialize_message(event, task_id)
        deserialized = deserialize_message(serialized)

        assert deserialized["event"] == event.value
        assert deserialized["task_id"] == task_id
        assert "timestamp" in deserialized

    def test_deserialize_raises_on_non_dict_json(self) -> None:
        """Test deserialize_message raises IPCError when JSON is not an object."""
        # Test with JSON array
        with pytest.raises(IPCError) as exc_info:
            deserialize_message('[{"event": "TASK_CREATED"}]\n')
        assert "JSON object" in str(exc_info.value)

        # Test with JSON string
        with pytest.raises(IPCError) as exc_info:
            deserialize_message('"just a string"\n')
        assert "JSON object" in str(exc_info.value)

        # Test with JSON number
        with pytest.raises(IPCError) as exc_info:
            deserialize_message("123\n")
        assert "JSON object" in str(exc_info.value)

        # Test with JSON boolean
        with pytest.raises(IPCError) as exc_info:
            deserialize_message("true\n")
        assert "JSON object" in str(exc_info.value)

        # Test with JSON null
        with pytest.raises(IPCError) as exc_info:
            deserialize_message("null\n")
        assert "JSON object" in str(exc_info.value)

    def test_deserialize_handles_unicode_characters(self) -> None:
        """Test deserialize_message handles Unicode characters in task_id."""
        task_id = "task-测试-123-🚀"
        line = f'{{"event": "TASK_CREATED", "task_id": "{task_id}", "timestamp": "2024-01-01T12:00:00Z"}}\n'
        result = deserialize_message(line)
        assert result["task_id"] == task_id

    def test_serialize_handles_unicode_characters(self) -> None:
        """Test serialize_message handles Unicode characters in task_id."""
        task_id = "task-测试-123-🚀"
        result = serialize_message(IPCEvent.TASK_CREATED, task_id)
        import json

        parsed = json.loads(result.strip())
        assert parsed["task_id"] == task_id

    def test_deserialize_preserves_extra_fields(self) -> None:
        """Test deserialize_message preserves extra fields in JSON."""
        line = '{"event": "TASK_CREATED", "task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z", "extra": "field", "another": 42}\n'
        result = deserialize_message(line)
        assert result["event"] == "TASK_CREATED"
        assert result["task_id"] == "test-123"
        assert result["timestamp"] == "2024-01-01T12:00:00Z"
        assert result["extra"] == "field"
        assert result["another"] == 42

    def test_deserialize_handles_crlf_line_endings(self) -> None:
        """Test deserialize_message handles Windows CRLF line endings."""
        line = '{"event": "TASK_CREATED", "task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z"}\r\n'
        result = deserialize_message(line)
        assert result["event"] == "TASK_CREATED"
        assert result["task_id"] == "test-123"

    def test_deserialize_raises_on_non_string_event(self) -> None:
        """Test deserialize_message raises IPCError when event is not a string."""
        # Event as number
        line = '{"event": 123, "task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z"}\n'
        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)
        # Should fail when trying to validate event name
        assert "event" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_deserialize_rejects_non_string_task_id(self) -> None:
        """Test deserialize_message rejects non-string task_id."""
        # task_id as number - should be rejected
        line = '{"event": "TASK_CREATED", "task_id": 12345, "timestamp": "2024-01-01T12:00:00Z"}\n'
        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)
        assert "string" in str(exc_info.value).lower()

    def test_deserialize_rejects_null_values(self) -> None:
        """Test deserialize_message rejects null values in required fields."""
        # Null event should fail validation
        line = '{"event": null, "task_id": "test-123", "timestamp": "2024-01-01T12:00:00Z"}\n'
        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)
        assert "null" in str(exc_info.value).lower()

        # Null task_id should fail validation
        line = '{"event": "TASK_CREATED", "task_id": null, "timestamp": "2024-01-01T12:00:00Z"}\n'
        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)
        assert "null" in str(exc_info.value).lower()

        # Null timestamp should fail validation
        line = '{"event": "TASK_CREATED", "task_id": "test-123", "timestamp": null}\n'
        with pytest.raises(IPCError) as exc_info:
            deserialize_message(line)
        assert "null" in str(exc_info.value).lower()
