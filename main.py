"""IconPilot — 桌面图标布局管理工具（开源版 v1.0）。

功能：捕获当前桌面图标坐标 → 存为命名布局组（免费 3 组）→ 一键恢复
→ 撤销 → 导出/导入。全程本地运行，不上传任何数据，不删除/移动文件。
"""
from __future__ import annotations

import tkinter.messagebox as tkmsg
from pathlib import Path

import customtkinter as ctk

from core.iconlayout import apply_layout, is_supported, read_layout
from core.storage import LayoutStore
from core.undo import UndoManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_TITLE = "IconPilot · 桌面图标布局管理"
REPO_URL = "https://github.com/aleilei-8/iconpilot"


class IconPilotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x560")
        self.store = LayoutStore()
        self.undo = UndoManager()

        self._build_ui()
        self._refresh_groups()
        self._log("就绪。点击「捕获当前桌面」开始。" if is_supported()
                  else "警告：当前系统未检测到桌面图标控件（仅 Windows 10/11 支持）。")

    # ---------------- UI ----------------
    def _build_ui(self):
        # 顶部信息条
        info = ctk.CTkLabel(
            self,
            text="🛡 只读取/写回图标位置，绝不删除或移动任何文件 · 数据仅存本地",
            text_color="#2a7", anchor="w",
        )
        info.pack(fill="x", padx=12, pady=(10, 2))

        # 捕获区
        cap_frame = ctk.CTkFrame(self)
        cap_frame.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(cap_frame, text="布局名称：").pack(side="left", padx=(10, 4))
        self.name_var = ctk.StringVar(value="我的布局 1")
        ctk.CTkEntry(cap_frame, textvariable=self.name_var, width=200).pack(side="left", padx=4)
        ctk.CTkButton(cap_frame, text="📸 捕获当前桌面", command=self._capture).pack(side="left", padx=4)
        self.limit_var = ctk.StringVar()
        ctk.CTkLabel(cap_frame, textvariable=self.limit_var, text_color="#888").pack(side="left", padx=10)

        # 列表
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.group_box = ctk.CTkScrollableFrame(list_frame, label_text="已保存布局组")
        self.group_box.pack(fill="both", expand=True, padx=8, pady=8)

        # 操作按钮
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(btn_frame, text="↩ 撤销上次恢复", command=self._undo).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="📤 导出…", command=self._export).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="📥 导入…", command=self._import).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="🌟 升级 Pro", command=self._open_pro).pack(side="right", padx=4)

        # 日志
        self.log_box = ctk.CTkTextbox(self, height=110)
        self.log_box.pack(fill="x", padx=12, pady=(2, 10))

    # ---------------- 行为 ----------------
    def _log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def _refresh_groups(self):
        for w in self.group_box.winfo_children():
            w.destroy()
        groups = self.store.list_groups()
        self.limit_var.set(f"已用 {self.store.count()}/{self.store.free_limit()} 组（免费）")
        if not groups:
            ctk.CTkLabel(self.group_box, text="（暂无布局，先捕获一个吧）", text_color="#999").pack(pady=10)
            return
        for name in groups:
            grp = self.store.get_group(name)
            row = ctk.CTkFrame(self.group_box)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"🗂 {name}  ({grp.get('count', 0)} 个图标)").pack(side="left", padx=8)
            ctk.CTkButton(row, text="恢复", width=70, command=lambda n=name: self._restore(n)).pack(side="right", padx=4)
            ctk.CTkButton(row, text="删除", width=70, fg_color="#c44", hover_color="#a33",
                          command=lambda n=name: self._remove(n)).pack(side="right", padx=4)

    def _capture(self):
        try:
            items = read_layout()
        except Exception as e:
            tkmsg.showerror("读取失败", str(e))
            self._log(f"❌ 捕获失败：{e}")
            return
        if not items:
            tkmsg.showwarning("空桌面", "未读取到任何图标，请确认处于桌面。")
            return
        name = self.name_var.get().strip()
        try:
            self.store.add_group(name, items)
        except PermissionError as e:
            tkmsg.showinfo("已达免费上限", str(e) + "\n\n升级 Pro 解锁无限分组。")
            self._log(f"⚠ {e}")
            return
        except ValueError as e:
            tkmsg.showerror("名称错误", str(e))
            return
        self._log(f"✅ 已保存「{name}」，共 {len(items)} 个图标坐标。")
        self._refresh_groups()

    def _restore(self, name: str):
        grp = self.store.get_group(name)
        if not grp:
            return
        if not tkmsg.askyesno("确认恢复", f"将把桌面图标恢复到「{name}」的位置？\n恢复前会自动快照当前布局，可随时撤销。"):
            return
        try:
            self.undo.capture_before_restore()
            applied = apply_layout(grp["items"])
        except Exception as e:
            tkmsg.showerror("恢复失败", str(e))
            self._log(f"❌ 恢复失败：{e}")
            return
        self._log(f"✅ 已恢复「{name}」，成功定位 {applied} 个图标。若位置未生效，请取消桌面「自动排列图标」后重试。")

    def _remove(self, name: str):
        if not tkmsg.askyesno("确认删除", f"删除布局组「{name}」？此操作不可撤销。"):
            return
        self.store.remove_group(name)
        self._log(f"🗑 已删除「{name}」。")
        self._refresh_groups()

    def _undo(self):
        if not self.undo.has_undo():
            tkmsg.showinfo("无撤销", "没有可撤销的恢复操作。")
            return
        snap = self.undo.get_snapshot()
        try:
            apply_layout(snap["items"])
        except Exception as e:
            tkmsg.showerror("撤销失败", str(e))
            return
        self.undo.clear()
        self._log(f"↩ 已撤销，恢复至恢复前的布局（{len(snap['items'])} 个图标）。")

    def _export(self):
        name = self.name_var.get().strip()
        groups = self.store.list_groups()
        if name not in groups and groups:
            name = groups[0]
        if name not in groups:
            tkmsg.showwarning("无布局", "没有可导出的布局。")
            return
        path = tkmsg.asksaveasfilename(defaultextension=".json",
                                       initialfile=f"{name}.layout.json",
                                       filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self.store.export_group(name, path)
            self._log(f"📤 已导出「{name}」到 {path}")
        except Exception as e:
            tkmsg.showerror("导出失败", str(e))

    def _import(self):
        path = tkmsg.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            added = self.store.import_group(path)
            self._log(f"📥 已导入布局「{added}」。")
            self._refresh_groups()
        except Exception as e:
            tkmsg.showerror("导入失败", str(e))

    def _open_pro(self):
        import webbrowser
        webbrowser.open(REPO_URL)
        self._log("🌟 Pro 功能说明见仓库 README（无限分组 / 场景自动切换 / 壁纸联动）。")


if __name__ == "__main__":
    if not is_supported():
        tkmsg.showwarning(
            "系统不支持",
            "IconPilot 需要 Windows 10/11 桌面环境。\n"
            "核心引擎仍可导入使用，但 GUI 的捕获/恢复功能需真实桌面。",
        )
    app = IconPilotApp()
    app.mainloop()
