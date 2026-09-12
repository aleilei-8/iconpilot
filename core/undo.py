"""一键撤销：在恢复布局前自动快照当前桌面状态，支持回退。"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .iconlayout import read_layout


def _snapshot_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home()
    return root / "IconPilot" / "last_snapshot.json"


class UndoManager:
    def __init__(self):
        self.path = _snapshot_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last: dict | None = None

    def capture_before_restore(self) -> dict:
        """恢复前调用：快照当前桌面布局并返回，同时落盘。"""
        snap = {"captured_at": time.time(), "items": read_layout()}
        self._last = snap
        self.path.write_text(
            json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return snap

    def has_undo(self) -> bool:
        if self._last is not None:
            return True
        if self.path.exists():
            try:
                return bool(json.loads(self.path.read_text(encoding="utf-8")).get("items"))
            except Exception:
                return False
        return False

    def get_snapshot(self) -> dict | None:
        if self._last:
            return self._last
        if self.path.exists():
            try:
                self._last = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._last = None
        return self._last

    def clear(self) -> None:
        self._last = None
        if self.path.exists():
            self.path.unlink()
