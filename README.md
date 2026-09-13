# IconPilot · 桌面图标布局管理（开源版 v1.0）

> 一键保存 / 恢复你的桌面图标布局。插上外接屏、开完会、回到家里，随时把图标摆回你习惯的位置。只读取与写回图标位置，**绝不删除、移动或改名任何文件**。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

---

## ✨ 它能做什么

- 📸 **捕获当前桌面**：把每个图标的名称与坐标一次性记录下来
- 🗂 **命名布局组**：免费版最多保存 **3 组**（如「办公」「娱乐」「极简」）
- ↩️ **一键恢复**：点一下，图标回到你保存的位置
- 🛡 **撤销**：每次恢复前自动快照，恢复错了随时退回
- 📤📥 **导出 / 导入**：换机或备份，一份 JSON 带走
- 🔒 **本地优先**：所有数据只存在本机 `%LOCALAPPDATA%/IconPilot/`，**不上传任何内容**

## 🛡 安全承诺（与 CCWiper 同源）

- 不删除、不移动、不重命名任何文件，仅操作图标**位置**
- 恢复前必须二次确认，且自动生成可撤销快照
- 纯本地运行，无网络请求、无遥测
- 代码全部开源可审，MIT 许可

## 🚀 30 秒上手

```bash
pip install -r requirements.txt
python main.py
```

1. 在桌面摆好你喜欢的图标位置
2. 输入布局名称（如「办公」），点 **📸 捕获当前桌面**
3. 哪天图标乱了，选中该组点 **恢复** 即可

> 💡 提示：若恢复后位置未生效，请在桌面右键 → 查看 → 取消勾选「自动排列图标」，再试一次。

## 🌟 Pro 版（付费增强，开源版不含）

- 无限布局组
- **场景自动切换**：检测到外接屏 / 进入会议 / 回到家中，自动套用对应布局
- 壁纸联动换布局
- 定时自动保存当前布局

> 开源占领口碑，付费增强赚钱——详见[开源变现实操手册](https://github.com/aleilei-8/ccwiper)思路。
> 升级与授权请见仓库 Releases 或联系作者。

## 🗂 项目结构

```
iconpilot/
├── main.py              # CustomTkinter 主界面
├── core/
│   ├── iconlayout.py    # ctypes 读取/写回桌面图标位置（零第三方依赖）
│   ├── storage.py       # 布局组本地持久化 + 免费 3 组上限
│   └── undo.py          # 恢复前快照 + 一键撤销
├── config/
│   └── default_settings.json
├── requirements.txt
└── LICENSE
```

## 📦 打包为单文件 exe（免安装分发）

想直接把 exe 发给别人、或自己双击用？项目自带 `build_exe.py`，一键打包成免安装单文件。

```bash
# 需要带 tkinter 的 Python（如系统 Python 3.12），managed 3.13 缺 tkinter 会失败
pip install customtkinter
python build_exe.py
# 产物：dist/IconPilot.exe （双击即跑，无需 Python 环境）
```

- `build_exe.py` 会自动安装 PyInstaller，用 `--onefile --windowed` 打包
- `dist/`、`build/`、`*.spec` 已被 `.gitignore` 忽略，不会进仓库——exe 请本机生成，勿提交大文件

## 📜 许可

MIT © 2026 IconPilot
