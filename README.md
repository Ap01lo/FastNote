# FastNote 笔记应用

一个自用的快速笔记知识库，因为感觉市面上的笔记软件很难满足我的这种需求，就是随手一记，可能看到重要的东西截图下来，或者文本的话复制下来然后当成笔记，然后用的时候用快捷键快速检索，整个过程越简单越好，可是我还没遇到这种即轻量化又简单的应用，索性自己写一个吧。

主要宗旨就是快捷，除了截图之外，基本不需要鼠标操作，几个快捷键随手就能记录，随手就能打开，快捷键的设置目前是按照我的使用习惯设置的，后续可能会看心情加入自定义快捷键吧。

> 项目是根据需求用trae写的。

主要支持快捷键操作，截图，剪切板和文本输入三种模式。

## 功能特点

- **现代化用户界面 (v2.0 改进)**
  - 更柔和的配色方案
  - 改进的卡片式布局
  - 更直观的焦点指示
  - 优化的响应式设计
- 支持多种快捷笔记操作：
  - **Ctrl+Alt+1：多屏幕截图保存笔记 (v2.0 新增)**
  - Ctrl+Alt+2：复制文本保存笔记（需要先复制到剪贴板）
  - Ctrl+Alt+3：直接输入文本保存笔记
  - Ctrl+Alt+F：搜索笔记
  - **Ctrl+D：删除笔记 (v2.0 改进：仅在主界面焦点激活时可用)**
  - Esc：最小化至托盘
  - j/k：在搜索结果中上下选择笔记
  - Tab: 切换工作焦点，在笔记选择和预览区切换
- 支持多种笔记类型：
  - 文本笔记
  - 截图笔记
  - 剪贴板文本
- 笔记列表实时更新
- SQLite 数据库存储
- 系统托盘后台运行

## 系统要求

- Python 3.6 或更高版本
- Windows 操作系统
- 依赖包：见 requirements.txt

## 安装步骤

1. 克隆或下载项目代码
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行程序：
   ```bash
   python FastNote.py
   ```

2. 快捷键操作：
   - **Ctrl+Alt+1**：截图保存笔记。按下快捷键后会出现截图框，鼠标点击拖动框选想要保存的区域，松开后弹出保存对话框，输入标题后按下回车[Enter]保存，按下[ESC]取消。
   - **Ctrl+Alt+2**：剪贴板保存笔记。首先选中需要保存的文本，将其复制到剪贴板，按下快捷键弹出保存对话框，输入标题后按下回车[Enter]保存，按下[ESC]取消。
   - **Ctrl+Alt+3**：直接输入文本保存笔记。直接按下快捷键后弹出输入框，输入标题后按下回车[Enter]输入内容，按[Ctrl+S]保存，按下[ESC]取消。
   - **Ctrl+Alt+F**：搜索笔记。按下快捷键弹出搜索框，输入标题关键字进行模糊匹配，按下回车[Enter]弹出搜索结果，按[ESC]取消。
   - **Ctrl+D**：删除笔记。选中需要删除的笔记（用鼠标选中或者在搜索结果界面用j/k上下选中皆可），按下快捷键即可删除。
   - **Esc**：最小化至托盘。在主界面按下此键可将应用最小化到系统托盘。
   - **j/k**：在搜索结果界面内选择笔记。在搜索结果列表获得焦点后，按 `j` 键选择下一个笔记，按 `k` 键选择上一个笔记。
   - **Tab**: 在笔记选择区和笔记预览区切换。在主界面内，按 `Tab` 键可以在笔记选择列表和笔记预览区域之间切换焦点。
3. 系统托盘功能：
   - 鼠标右键点击托盘图标可以显示菜单。
   - 选择"显示"可以重新打开主窗口。
   - 选择"退出"可以完全退出程序。

## 文件结构

- `FastNote.py`: 主程序文件，包含GUI界面和程序逻辑
- `db_operations.py`: 数据库操作类
- `requirements.txt`: 项目依赖列表

## 技术特点

- **使用 Tkinter 和 ttk 构建现代化界面 (v2.0 改进)**
  - 采用clam主题作为基础
  - 自定义样式和颜色方案
  - 改进的布局和间距
- 采用面向对象方式组织代码
- 使用 SQLite 数据库实现数据持久化
- 支持二进制数据存储（图片等）
- 集成 pystray 实现系统托盘功能
- 使用 pynput 实现全局快捷键
- **使用 pywin32 实现多屏幕截图和系统剪贴板访问 (v2.0 改进)**

## 注意事项

- 首次运行时会自动创建数据库文件
- 关闭窗口时程序会自动最小化到系统托盘
- 要完全退出程序，请使用托盘菜单中的"退出"选项
- 使用快捷键功能时需要保持程序在后台运行
- 选中文本保存功能依赖系统剪贴板