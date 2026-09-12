"""布局组的本地持久化（JSON），含免费版 3 组分上限与导出/导入。"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

FREE_GROUP_LIMIT = 3  # 免费版最多保存的布局组数量


def _default_store_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home()
    return root / "IconPilot" / "layouts.json"


class LayoutStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else _default_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                d = json.loads(self.path.read_text(encoding="utf-8"))
                d.setdefault("groups", {})
                d.setdefault("free_limit", FREE_GROUP_LIMIT)
                return d
            except Exception:
                pass
        return {"groups": {}, "free_limit": FREE_GROUP_LIMIT}

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ---- 查询 ----
    def list_groups(self) -> list[str]:
        return sorted(self.data["groups"].keys())

    def get_group(self, name: str) -> dict | None:
        return self.data["groups"].get(name)

    def count(self) -> int:
        return len(self.data["groups"])

    def free_limit(self) -> int:
        return int(self.data.get("free_limit", FREE_GROUP_LIMIT))

    # ---- 写操作 ----
    def add_group(self, name: str, items: list[dict]) -> None:
        name = (name or "").strip()
        if not name:
            raise ValueError("布局名称不能为空")
        if name in self.data["groups"]:
            raise ValueError(f"布局组「{name}」已存在")
        if len(self.data["groups"]) >= self.free_limit():
            raise PermissionError(
                f"免费版最多保存 {self.free_limit()} 个布局，升级 Pro 解锁无限分组与场景自动切换"
            )
        self.data["groups"][name] = {
            "saved_at": time.time(),
            "count": len(items),
            "items": items,
        }
        self.save()

    def remove_group(self, name: str) -> None:
        self.data["groups"].pop(name, None)
        self.save()

    # ---- 导出 / 导入（用于备份或换机迁移） ----
    def export_group(self, name: str, export_path: str) -> None:
        grp = self.get_group(name)
        if not grp:
            raise KeyError(f"布局组「{name}」不存在")
        Path(export_path).write_text(
            json.dumps({"name": name, **grp}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def import_group(self, import_path: str, name: str | None = None) -> str:
        d = json.loads(Path(import_path).read_text(encoding="utf-8"))
        gname = (name or d.get("name") or "").strip()
        if not gname:
            raise ValueError("缺少布局名称")
        if gname in self.data["groups"]:
            raise ValueError(f"布局组「{gname}」已存在")
        if len(self.data["groups"]) >= self.free_limit():
            raise PermissionError(
                f"免费版最多保存 {self.free_limit()} 个布局，升级 Pro 解锁无限分组"
            )
        grp = {k: v for k, v in d.items() if k != "name"}
        grp.setdefault("saved_at", time.time())
        self.data["groups"][gname] = grp
        self.save()
        return gname
