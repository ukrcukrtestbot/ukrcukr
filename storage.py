"""SQLite-стораж для FSM: стейти переживають рестарти."""
import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey


def _key_to_str(key: StorageKey) -> str:
    return (
        f"{key.bot_id}:{key.chat_id}:{key.user_id}:"
        f"{key.thread_id or 0}:{key.business_connection_id or ''}"
    )


class SqliteStorage(BaseStorage):
    """Простий sync-sqlite стораж, обгорнутий у to_thread для не-блокування."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = asyncio.Lock()
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS fsm ("
                "  key TEXT PRIMARY KEY,"
                "  state TEXT,"
                "  data TEXT"
                ")"
            )
            conn.commit()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _sync_set_state(self, k: str, state: Optional[str]):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO fsm (key, state, data) VALUES (?, ?, '{}')"
                " ON CONFLICT(key) DO UPDATE SET state=excluded.state",
                (k, state),
            )
            conn.commit()

    def _sync_get_state(self, k: str) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute("SELECT state FROM fsm WHERE key = ?", (k,)).fetchone()
            return row[0] if row else None

    def _sync_set_data(self, k: str, data: dict):
        payload = json.dumps(data, ensure_ascii=False)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO fsm (key, state, data) VALUES (?, NULL, ?)"
                " ON CONFLICT(key) DO UPDATE SET data=excluded.data",
                (k, payload),
            )
            conn.commit()

    def _sync_get_data(self, k: str) -> dict:
        with self._conn() as conn:
            row = conn.execute("SELECT data FROM fsm WHERE key = ?", (k,)).fetchone()
            if not row or not row[0]:
                return {}
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return {}

    async def set_state(self, key: StorageKey, state: State | str | None = None) -> None:
        state_str = state.state if isinstance(state, State) else state
        async with self._lock:
            await asyncio.to_thread(self._sync_set_state, _key_to_str(key), state_str)

    async def get_state(self, key: StorageKey) -> Optional[str]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_state, _key_to_str(key))

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        async with self._lock:
            await asyncio.to_thread(self._sync_set_data, _key_to_str(key), data)

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        async with self._lock:
            return await asyncio.to_thread(self._sync_get_data, _key_to_str(key))

    async def close(self) -> None:
        pass
