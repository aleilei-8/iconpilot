"""Windows 桌面图标位置读取与写入（ctypes 实现，零第三方依赖）。

参考 DesktopOK 等公开思路：桌面图标位于 Progman / WorkerW 下的
SysListView32 列表控件中，通过 SendMessage 调用 ListView 消息接口。

本模块只「读取 / 写回位置」，绝不删除、移动、改名任何文件——与 CCWiper
同源的安全哲学。
"""
from __future__ import annotations

import ctypes
import logging
from ctypes import wintypes

logger = logging.getLogger(__name__)

try:
    user32 = ctypes.windll.user32
    _HAS_WIN32 = True
except AttributeError:
    user32 = None
    _HAS_WIN32 = False


# ---- ListView 消息常量 ----
LVM_FIRST = 0x1000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_GETITEMTEXTW = LVM_FIRST + 115      # 0x1073
LVM_GETITEMPOSITION = LVM_FIRST + 16    # 0x1010
LVM_SETITEMPOSITION = LVM_FIRST + 15    # 0x100F

LVIF_TEXT = 0x0001


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class LVITEMW(ctypes.Structure):
    _fields_ = [
        ("mask", ctypes.c_uint),
        ("iItem", ctypes.c_int),
        ("iSubItem", ctypes.c_int),
        ("state", ctypes.c_uint),
        ("stateMask", ctypes.c_uint),
        ("pszText", ctypes.c_wchar_p),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("lParam", ctypes.c_void_p),
        ("iIndent", ctypes.c_int),
        ("iGroupId", ctypes.c_int),
        ("cColumns", ctypes.c_uint),
        ("puColumns", ctypes.c_void_p),
        ("piColFmt", ctypes.c_void_p),
        ("iGroup", ctypes.c_int),
    ]


if _HAS_WIN32:
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowExW.argtypes = [
        wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR
    ]
    user32.FindWindowExW.restype = wintypes.HWND
    user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, ctypes.c_void_p]
    user32.SendMessageW.restype = ctypes.c_longlong
    _ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [_ENUM_PROC, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL


def _find_desktop_listview() -> int | None:
    """定位桌面图标所在的 SysListView32 句柄。兼容 Win10/11。"""
    if not _HAS_WIN32:
        return None

    # 方法 1：Progman -> SHELLDLL_DefView -> SysListView32（部分系统）
    progman = user32.FindWindowW("Progman", None)
    if progman:
        shell = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
        if shell:
            lv = user32.FindWindowExW(shell, None, "SysListView32", None)
            if lv:
                return lv

    # 方法 2：遍历 WorkerW 树（Win10/11 常见）
    result = {"hwnd": None}

    def _enum(hwnd, _lparam):
        shell = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
        if shell:
            lv = user32.FindWindowExW(shell, None, "SysListView32", None)
            if lv:
                result["hwnd"] = lv
                return False  # 停止枚举
        return True

    user32.EnumWindows(_ENUM_PROC(_enum), 0)
    return result["hwnd"]


def is_supported() -> bool:
    return _HAS_WIN32 and _find_desktop_listview() is not None


def read_layout() -> list[dict]:
    """读取当前桌面所有图标的名称与坐标。

    返回 [{name, x, y}, ...]，顺序即桌面内部顺序。
    任何异常都向上抛，由调用方决定如何提示用户。
    """
    if not _HAS_WIN32:
        raise RuntimeError("仅支持 Windows 系统")

    lv = _find_desktop_listview()
    if not lv:
        raise RuntimeError("找不到桌面图标列表控件（请确认处于桌面且未被全屏遮挡）")

    count = user32.SendMessageW(lv, LVM_GETITEMCOUNT, 0, 0)
    if count <= 0:
        return []

    buf = ctypes.create_unicode_buffer(512)
    item = LVITEMW()
    item.mask = LVIF_TEXT
    item.iSubItem = 0
    item.pszText = ctypes.cast(buf, ctypes.c_wchar_p)
    item.cchTextMax = 512
    pt = POINT()
    items: list[dict] = []

    for i in range(count):
        item.iItem = i
        user32.SendMessageW(lv, LVM_GETITEMTEXTW, i, ctypes.byref(item))
        user32.SendMessageW(lv, LVM_GETITEMPOSITION, i, ctypes.byref(pt))
        name = buf.value or ""
        if not name:
            continue
        items.append({"name": name, "x": int(pt.x), "y": int(pt.y)})

    return items


def apply_layout(layout: list[dict]) -> int:
    """按名称把图标恢复到指定坐标。返回成功设置的图标数量。

    注意：桌面若开启了「自动排列」会覆盖手动位置，恢复前建议在桌面
    右键 → 查看 中取消「自动排列图标」。
    """
    if not _HAS_WIN32:
        raise RuntimeError("仅支持 Windows 系统")

    lv = _find_desktop_listview()
    if not lv:
        raise RuntimeError("找不到桌面图标列表控件")

    current = read_layout()
    index_by_name = {c["name"]: i for i, c in enumerate(current)}

    applied = 0
    for entry in layout:
        name = entry.get("name")
        idx = index_by_name.get(name)
        if idx is None:
            logger.warning("桌面不存在图标 %s，已跳过", name)
            continue
        x = int(entry.get("x", 0)) & 0xFFFF
        y = int(entry.get("y", 0)) & 0xFFFF
        lparam = ctypes.c_long((y << 16) | x)
        user32.SendMessageW(lv, LVM_SETITEMPOSITION, idx, lparam)
        applied += 1

    # 通知 Shell 刷新图标缓存，提高落盘概率
    try:
        shell32 = ctypes.windll.shell32
        shell32.SHChangeNotify(0x8000000, 0x1000, None, None)  # SHCNE_ASSOCCHANGED
    except Exception:
        pass

    return applied
