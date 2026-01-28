-- jot-cli database schema
-- Version: 2
-- Created: 2026-01-26

-- Tasks table: current state of all tasks
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('active', 'completed', 'cancelled', 'deferred')),
    created_at TEXT NOT NULL,           -- ISO 8601 format
    updated_at TEXT NOT NULL,           -- ISO 8601 format
    completed_at TEXT,                  -- ISO 8601 format, nullable
    cancelled_at TEXT,                  -- ISO 8601 format, nullable
    cancel_reason TEXT,                 -- Reason for cancellation, nullable
    deferred_until TEXT                 -- ISO 8601 format, nullable
);

-- Task events table: audit trail of all task state changes
CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('CREATED', 'COMPLETED', 'CANCELLED', 'DEFERRED')),
    timestamp TEXT NOT NULL,            -- ISO 8601 format
    metadata TEXT,                      -- JSON string, nullable
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tasks_state ON tasks(state);
CREATE INDEX IF NOT EXISTS idx_task_events_task_id ON task_events(task_id);
