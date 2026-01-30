"""Test suite for core.theme module."""

import os
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from jot.core.task import Task, TaskState
from jot.core.theme import (
    TaskColors,
    TaskEmoji,
    TextStyles,
    format_task_state,
    get_color_for_capability,
    get_emoji,
    get_textual_style_for_state,
    should_use_color,
)


class TestTaskColors:
    """Test TaskColors constants."""

    def test_active_color_is_cyan(self):
        """Test ACTIVE color is cyan."""
        assert TaskColors.ACTIVE == "cyan"

    def test_completed_color_is_green(self):
        """Test COMPLETED color is green."""
        assert TaskColors.COMPLETED == "green"

    def test_cancelled_color_is_red(self):
        """Test CANCELLED color is red."""
        assert TaskColors.CANCELLED == "red"

    def test_deferred_color_is_yellow(self):
        """Test DEFERRED color is yellow."""
        assert TaskColors.DEFERRED == "yellow"

    def test_muted_color_is_dim(self):
        """Test MUTED color is dim."""
        assert TaskColors.MUTED == "dim"


class TestTaskEmoji:
    """Test TaskEmoji constants."""

    def test_active_emoji_is_target(self):
        """Test ACTIVE emoji is target."""
        assert TaskEmoji.ACTIVE == "🎯"

    def test_completed_emoji_is_checkmark(self):
        """Test COMPLETED emoji is checkmark."""
        assert TaskEmoji.COMPLETED == "✅"

    def test_cancelled_emoji_is_cross(self):
        """Test CANCELLED emoji is cross."""
        assert TaskEmoji.CANCELLED == "❌"

    def test_deferred_emoji_is_pause(self):
        """Test DEFERRED emoji is pause."""
        assert TaskEmoji.DEFERRED == "⏸️"

    def test_streak_emoji_is_fire(self):
        """Test STREAK emoji is fire."""
        assert TaskEmoji.STREAK == "🔥"

    def test_date_emoji_is_calendar(self):
        """Test DATE emoji is calendar."""
        assert TaskEmoji.DATE == "📅"

    def test_celebrate_emoji_is_party(self):
        """Test CELEBRATE emoji is party."""
        assert TaskEmoji.CELEBRATE == "🎉"


class TestTextStyles:
    """Test TextStyles constants."""

    def test_heading_style_is_bold(self):
        """Test heading style is bold."""
        assert TextStyles.heading == "bold"

    def test_task_current_style_is_bold_cyan(self):
        """Test task_current style is bold cyan."""
        assert TextStyles.task_current == "bold cyan"

    def test_task_completed_style_is_strike_green(self):
        """Test task_completed style is strike green."""
        assert TextStyles.task_completed == "strike green"

    def test_task_cancelled_style_is_dim_red(self):
        """Test task_cancelled style is dim red."""
        assert TextStyles.task_cancelled == "dim red"

    def test_task_deferred_style_is_dim_yellow(self):
        """Test task_deferred style is dim yellow."""
        assert TextStyles.task_deferred == "dim yellow"

    def test_metadata_style_is_dim(self):
        """Test metadata style is dim."""
        assert TextStyles.metadata == "dim"

    def test_styles_produce_valid_rich_markup(self):
        """Test styles produce valid Rich markup."""
        console = Console()
        # Should not raise exception when rendering
        console.print(f"[{TextStyles.heading}]Heading[/]")
        console.print(f"[{TextStyles.task_current}]Current Task[/]")
        console.print(f"[{TextStyles.task_completed}]Completed Task[/]")
        console.print(f"[{TextStyles.task_cancelled}]Cancelled Task[/]")
        console.print(f"[{TextStyles.metadata}]Metadata[/]")


class TestFormatTaskState:
    """Test format_task_state function."""

    def test_format_active_task(self):
        """Test formatting active task."""
        from datetime import UTC, datetime

        task = Task(
            id="test-id",
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        result = format_task_state(task)
        assert TaskEmoji.ACTIVE in result
        assert task.description in result
        assert "cyan" in result.lower() or "bold" in result.lower()

    def test_format_completed_task(self):
        """Test formatting completed task."""
        from datetime import UTC, datetime

        task = Task(
            id="test-id",
            description="Completed task",
            state=TaskState.COMPLETED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        result = format_task_state(task)
        assert TaskEmoji.COMPLETED in result
        assert task.description in result
        assert "green" in result.lower() or "strike" in result.lower()

    def test_format_cancelled_task(self):
        """Test formatting cancelled task."""
        from datetime import UTC, datetime

        task = Task(
            id="test-id",
            description="Cancelled task",
            state=TaskState.CANCELLED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            cancelled_at=datetime.now(UTC),
        )
        result = format_task_state(task)
        assert TaskEmoji.CANCELLED in result
        assert task.description in result
        assert "red" in result.lower()

    def test_format_deferred_task(self):
        """Test formatting deferred task."""
        from datetime import UTC, datetime

        task = Task(
            id="test-id",
            description="Deferred task",
            state=TaskState.DEFERRED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            deferred_at=datetime.now(UTC),
        )
        result = format_task_state(task)
        assert TaskEmoji.DEFERRED in result
        assert task.description in result
        assert "yellow" in result.lower()

    def test_format_task_state_with_ascii_only(self):
        """Test format_task_state with ASCII-only mode."""
        from datetime import UTC, datetime

        task = Task(
            id="test-id",
            description="Test task",
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        result = format_task_state(task, ascii_only=True)
        assert TaskEmoji.ACTIVE not in result
        assert "[ACTIVE]" in result or "ACTIVE" in result
        assert task.description in result


class TestGetEmoji:
    """Test get_emoji function."""

    def test_get_emoji_active(self):
        """Test get_emoji returns correct emoji for active state."""
        assert get_emoji("active") == TaskEmoji.ACTIVE

    def test_get_emoji_completed(self):
        """Test get_emoji returns correct emoji for completed state."""
        assert get_emoji("completed") == TaskEmoji.COMPLETED

    def test_get_emoji_cancelled(self):
        """Test get_emoji returns correct emoji for cancelled state."""
        assert get_emoji("cancelled") == TaskEmoji.CANCELLED

    def test_get_emoji_deferred(self):
        """Test get_emoji returns correct emoji for deferred state."""
        assert get_emoji("deferred") == TaskEmoji.DEFERRED

    def test_get_emoji_unknown_state_defaults_to_active(self):
        """Test get_emoji defaults to ACTIVE for unknown states."""
        assert get_emoji("unknown") == TaskEmoji.ACTIVE

    def test_get_emoji_ascii_only_active(self):
        """Test get_emoji returns ASCII fallback for active state."""
        result = get_emoji("active", ascii_only=True)
        assert result == "[ACTIVE]"
        assert TaskEmoji.ACTIVE not in result

    def test_get_emoji_ascii_only_completed(self):
        """Test get_emoji returns ASCII fallback for completed state."""
        result = get_emoji("completed", ascii_only=True)
        assert result == "[DONE]"
        assert TaskEmoji.COMPLETED not in result

    def test_get_emoji_ascii_only_cancelled(self):
        """Test get_emoji returns ASCII fallback for cancelled state."""
        result = get_emoji("cancelled", ascii_only=True)
        assert result == "[CANCELLED]"
        assert TaskEmoji.CANCELLED not in result

    def test_get_emoji_ascii_only_deferred(self):
        """Test get_emoji returns ASCII fallback for deferred state."""
        result = get_emoji("deferred", ascii_only=True)
        assert result == "[DEFERRED]"
        assert TaskEmoji.DEFERRED not in result

    def test_get_emoji_ascii_only_unknown_state(self):
        """Test get_emoji returns ASCII fallback for unknown state when ASCII-only."""
        # Unknown states default to ACTIVE emoji, which then gets converted to ASCII
        result = get_emoji("unknown", ascii_only=True)
        # Should return the ASCII fallback for ACTIVE since unknown maps to ACTIVE
        assert result == "[ACTIVE]"


class TestTerminalCapabilityDetection:
    """Test terminal capability detection."""

    def test_no_color_environment_variable(self):
        """Test NO_COLOR environment variable is respected."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            console = Console()
            assert should_use_color(console) is False

    def test_no_color_unset_allows_color(self):
        """Test colors are allowed when NO_COLOR is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove NO_COLOR if it exists
            os.environ.pop("NO_COLOR", None)
            console = Console()
            # Should return True if terminal supports colors
            result = should_use_color(console)
            # Result depends on actual terminal, but should be boolean
            assert isinstance(result, bool)

    def test_should_use_color_with_none_console(self):
        """Test should_use_color creates Console when None is passed."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NO_COLOR", None)
            # Pass None to trigger Console creation
            result = should_use_color(None)
            # Result depends on actual terminal, but should be boolean
            assert isinstance(result, bool)

    def test_terminal_capability_detection(self):
        """Test terminal capability detection."""
        console = Console()
        # Rich Console provides color_system attribute
        assert hasattr(console, "color_system")
        assert console.color_system in (None, "standard", "256", "truecolor")

    def test_get_color_for_capability_no_color(self):
        """Test get_color_for_capability respects NO_COLOR."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            console = Console()
            result = get_color_for_capability(console, TaskColors.ACTIVE)
            assert result is None

    def test_get_color_for_capability_8color(self):
        """Test get_color_for_capability with 8-color terminal."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NO_COLOR", None)
            console = MagicMock(spec=Console)
            console.color_system = "standard"
            result = get_color_for_capability(console, TaskColors.ACTIVE)
            # Cyan should fallback to blue in 8-color
            assert result == "blue"

    def test_get_color_for_capability_256color(self):
        """Test get_color_for_capability with 256-color terminal."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NO_COLOR", None)
            console = MagicMock(spec=Console)
            console.color_system = "256"
            result = get_color_for_capability(console, TaskColors.ACTIVE)
            assert result == TaskColors.ACTIVE

    def test_get_color_for_capability_truecolor(self):
        """Test get_color_for_capability with truecolor terminal."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NO_COLOR", None)
            console = MagicMock(spec=Console)
            console.color_system = "truecolor"
            result = get_color_for_capability(console, TaskColors.ACTIVE)
            assert result == TaskColors.ACTIVE

    def test_get_color_for_capability_monochrome(self):
        """Test get_color_for_capability with monochrome terminal."""
        console = MagicMock(spec=Console)
        console.color_system = None
        result = get_color_for_capability(console, TaskColors.ACTIVE)
        assert result is None

    def test_get_color_for_capability_8color_fallback_mapping(self):
        """Test get_color_for_capability fallback mapping for all colors in 8-color."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NO_COLOR", None)
            console = MagicMock(spec=Console)
            console.color_system = "standard"
            # Test all colors that have fallbacks
            assert get_color_for_capability(console, "cyan") == "blue"
            assert get_color_for_capability(console, "yellow") == "yellow"
            assert get_color_for_capability(console, "green") == "green"
            assert get_color_for_capability(console, "red") == "red"
            # Test color not in fallback map (should return as-is)
            assert get_color_for_capability(console, "magenta") == "magenta"

    def test_get_color_for_capability_unknown_color_system(self):
        """Test get_color_for_capability with unknown color system."""
        console = MagicMock(spec=Console)
        console.color_system = "unknown_system"  # Not standard, 256, or truecolor
        result = get_color_for_capability(console, TaskColors.ACTIVE)
        # Should return None for unknown color systems
        assert result is None


class TestTextualCompatibility:
    """Test Textual compatibility."""

    def test_colors_work_with_textual_style(self):
        """Test colors work with Textual Style objects."""
        try:
            from textual.style import Style

            # Textual Style uses foreground parameter for color
            style = Style(foreground=TaskColors.ACTIVE)
            assert style.foreground == TaskColors.ACTIVE

            style = Style(foreground=TaskColors.COMPLETED)
            assert style.foreground == TaskColors.COMPLETED
        except ImportError:
            pytest.skip("Textual not installed - skipping Textual compatibility test")

    def test_get_textual_style_for_state_active(self):
        """Test get_textual_style_for_state for active state."""
        style_dict = get_textual_style_for_state("active")
        assert style_dict["foreground"] == TaskColors.ACTIVE
        assert style_dict["bold"] is True
        assert isinstance(style_dict["bold"], bool)

    def test_get_textual_style_for_state_completed(self):
        """Test get_textual_style_for_state for completed state."""
        style_dict = get_textual_style_for_state("completed")
        assert style_dict["foreground"] == TaskColors.COMPLETED
        assert style_dict["strike"] is True
        assert isinstance(style_dict["strike"], bool)

    def test_get_textual_style_for_state_cancelled(self):
        """Test get_textual_style_for_state for cancelled state."""
        style_dict = get_textual_style_for_state("cancelled")
        assert style_dict["foreground"] == TaskColors.CANCELLED
        assert style_dict["dim"] is True
        assert isinstance(style_dict["dim"], bool)

    def test_get_textual_style_for_state_deferred(self):
        """Test get_textual_style_for_state for deferred state."""
        style_dict = get_textual_style_for_state("deferred")
        assert style_dict["foreground"] == TaskColors.DEFERRED
        assert style_dict["dim"] is True
        assert isinstance(style_dict["dim"], bool)

    def test_get_textual_style_for_state_unknown(self):
        """Test get_textual_style_for_state for unknown state."""
        style_dict = get_textual_style_for_state("unknown")
        assert style_dict["foreground"] == TaskColors.MUTED

    def test_get_textual_style_for_state_with_textual_style_object(self):
        """Test get_textual_style_for_state works with actual Textual Style objects."""
        try:
            from textual.style import Style

            # Test all states create valid Textual Style objects
            for state in ["active", "completed", "cancelled", "deferred"]:
                style_dict = get_textual_style_for_state(state)
                style = Style(**style_dict)
                assert style is not None
                assert style.foreground == style_dict["foreground"]
        except ImportError:
            pytest.skip("Textual not installed - skipping Textual Style object test")

    def test_get_textual_style_for_state_with_taskstate_enum(self):
        """Test get_textual_style_for_state accepts TaskState enum."""
        style_dict = get_textual_style_for_state(TaskState.ACTIVE)
        assert style_dict["foreground"] == TaskColors.ACTIVE
        assert style_dict["bold"] is True

        style_dict = get_textual_style_for_state(TaskState.COMPLETED)
        assert style_dict["foreground"] == TaskColors.COMPLETED
        assert style_dict["strike"] is True

    def test_get_emoji_with_taskstate_enum(self):
        """Test get_emoji accepts TaskState enum."""
        assert get_emoji(TaskState.ACTIVE) == TaskEmoji.ACTIVE
        assert get_emoji(TaskState.COMPLETED) == TaskEmoji.COMPLETED
        assert get_emoji(TaskState.CANCELLED) == TaskEmoji.CANCELLED
        assert get_emoji(TaskState.DEFERRED) == TaskEmoji.DEFERRED

    def test_get_emoji_with_taskstate_enum_ascii_only(self):
        """Test get_emoji with TaskState enum and ASCII-only mode."""
        assert get_emoji(TaskState.ACTIVE, ascii_only=True) == "[ACTIVE]"
        assert get_emoji(TaskState.COMPLETED, ascii_only=True) == "[DONE]"
        assert get_emoji(TaskState.CANCELLED, ascii_only=True) == "[CANCELLED]"
        assert get_emoji(TaskState.DEFERRED, ascii_only=True) == "[DEFERRED]"

    def test_format_task_state_with_minimal_description(self):
        """Test format_task_state handles minimal valid description."""
        from datetime import UTC, datetime

        # Task model validation prevents empty descriptions, so test with minimal valid description
        task = Task(
            id="test-id",
            description="x",  # Minimal valid description (single character)
            state=TaskState.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        result = format_task_state(task)
        assert result is not None
        assert len(result) > 0
        assert TaskEmoji.ACTIVE in result
        assert task.description in result
