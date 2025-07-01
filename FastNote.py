import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from db_operations import DatabaseManager
import pystray
from PIL import Image, ImageGrab, ImageTk
import io
from pynput import keyboard
import win32clipboard
import pyperclip
import threading

class NoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FastNote - 快速笔记")
        self.root.geometry("1000x700")
        self.root.minsize(900, 650)
        self.root.configure(bg='#F8F9FA')  # 更柔和的背景色
        
        # 设置图标
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 初始化数据库
        self.db = DatabaseManager()
        
        # 创建系统托盘图标变量
        self.icon = None
        
        # 创建样式
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用clam主题作为基础
        
        # 基础样式
        self.style.configure('TFrame', background='#F8F9FA')
        self.style.configure('TLabel', background='#F8F9FA', font=('Microsoft YaHei UI', 10))
        self.style.configure('TButton', font=('Microsoft YaHei UI', 10), padding=6)
        
        # 创建焦点边框样式
        self.style.configure('Focused.TFrame', background='#4CAF50')  # 绿色边框
        self.style.configure('Normal.TFrame', background='#E0E0E0')   # 浅灰色边框
        
        # 创建内容框架样式
        self.style.configure('Content.TFrame', background='white')
        
        # 创建卡片样式
        self.style.configure('Card.TFrame', background='white', relief='flat')
        
        # 创建标题样式
        self.style.configure('Title.TLabel', 
                            font=('Microsoft YaHei UI', 12, 'bold'), 
                            background='white', 
                            foreground='#333333')
        
        # 创建自定义Treeview样式
        self.style.configure('Custom.Treeview', 
                            background='white', 
                            fieldbackground='white', 
                            borderwidth=0,
                            font=('Microsoft YaHei UI', 11),
                            rowheight=32)
        self.style.map('Custom.Treeview', 
                      background=[('selected', '#E8F5E9')],  # 浅绿色选中背景
                      foreground=[('selected', '#333333')])  # 深灰色选中文字
        
        self.style.configure('Custom.Treeview.Heading', 
                            font=('Microsoft YaHei UI', 11, 'bold'),
                            relief='flat',
                            borderwidth=0,
                            background='#F5F5F5',
                            foreground='#333333')
        
        # 创建主布局
        main_container = ttk.Frame(self.root, style='TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 创建顶部区域
        top_frame = ttk.Frame(main_container, style='TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 创建应用标题
        app_title = ttk.Label(top_frame, text="FastNote", 
                             font=('Microsoft YaHei UI', 18, 'bold'), 
                             foreground='#4CAF50')
        app_title.pack(side=tk.LEFT)
        
        # 创建搜索区域容器（包含搜索框和快捷键提示）
        search_area = ttk.Frame(top_frame, style='TFrame')
        search_area.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))
        
        # 创建搜索框
        search_container = ttk.Frame(search_area, style='Card.TFrame', padding=5)
        search_container.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_container, textvariable=self.search_var, 
                                     font=('Microsoft YaHei UI', 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        
        self.search_button = ttk.Button(search_container, text="搜索", 
                                       command=self.search_notes, width=6)
        self.search_button.pack(side=tk.RIGHT, padx=(0, 5))
        
        # 创建快捷键提示标签（放在搜索框下方）
        shortcut_text = "快捷键： Ctrl+Alt+1 截图 | Ctrl+Alt+2 剪切文本 | Ctrl+Alt+3 输入 | Ctrl+Alt+F 搜索 | Ctrl+D 删除 | Ctrl+S 保存 | Tab 切换工作区域 | ESC 取消选择"
        self.shortcut_label = ttk.Label(search_area, text=shortcut_text, 
                                      font=('Microsoft YaHei UI', 9), 
                                      foreground='#666666')
        self.shortcut_label.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))
        
        # 绑定回车键到搜索功能
        self.search_entry.bind('<Return>', lambda e: self.search_notes())
        
        # 创建主内容区域
        content_frame = ttk.Frame(main_container, style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧笔记列表区域（占比35%）
        self.list_frame = ttk.Frame(content_frame, style='Normal.TFrame')
        self.list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10), pady=0, ipadx=0, ipady=0)
        self.list_frame.configure(width=350)  # 固定宽度
        
        # 创建内容容器
        self.list_content = ttk.Frame(self.list_frame, style='Card.TFrame')
        self.list_content.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 创建笔记列表标题区域
        list_header = ttk.Frame(self.list_content, style='Card.TFrame')
        list_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        list_title = ttk.Label(list_header, text="笔记列表", style='Title.TLabel')
        list_title.pack(side=tk.LEFT)
        
        # 添加删除按钮
        self.delete_button = ttk.Button(list_header, text="删除", 
                                      command=self.delete_note, width=6)
        self.delete_button.pack(side=tk.RIGHT)
        
        # 创建分隔线
        separator1 = ttk.Separator(self.list_content, orient='horizontal')
        separator1.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # 创建笔记列表容器
        tree_container = ttk.Frame(self.list_content, style='Card.TFrame')
        tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 创建笔记列表
        self.tree = ttk.Treeview(tree_container, 
                               columns=("ID", "标题", "类型", "创建时间", "更新时间"), 
                               show="headings", 
                               style='Custom.Treeview')
        
        # 设置列标题
        self.tree.heading("ID", text="ID")
        self.tree.heading("标题", text="标题")
        self.tree.heading("类型", text="类型")
        self.tree.heading("创建时间", text="创建时间")
        self.tree.heading("更新时间", text="更新时间")
        
        # 设置列宽和隐藏某些列
        self.tree.column("ID", width=0, stretch=tk.NO, minwidth=0)
        self.tree.column("标题", width=240, minwidth=150)
        self.tree.column("类型", width=60, minwidth=50)
        self.tree.column("创建时间", width=0, stretch=tk.NO, minwidth=0)
        self.tree.column("更新时间", width=0, stretch=tk.NO, minwidth=0)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建右侧预览区域（占比65%）
        self.preview_frame = ttk.Frame(content_frame, style='Normal.TFrame')
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=0)
        
        # 创建预览内容容器
        self.preview_content_frame = ttk.Frame(self.preview_frame, style='Card.TFrame')
        self.preview_content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 创建预览标题
        self.preview_title = ttk.Label(self.preview_content_frame, text="", 
                                     font=('Microsoft YaHei UI', 16, 'bold'), 
                                     background='white',
                                     foreground='#333333')
        self.preview_title.pack(fill=tk.X, padx=20, pady=(20, 15))
        
        # 创建分隔线
        separator2 = ttk.Separator(self.preview_content_frame, orient='horizontal')
        separator2.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # 创建预览内容容器
        preview_container = ttk.Frame(self.preview_content_frame, style='Card.TFrame')
        preview_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 创建预览内容文本框
        self.preview_content = tk.Text(preview_container, 
                                     wrap=tk.WORD, 
                                     font=('Microsoft YaHei UI', 12), 
                                     background='white', 
                                     relief='flat', 
                                     borderwidth=0, 
                                     padx=5, 
                                     pady=5,
                                     state="disabled")
        self.preview_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加预览内容滚动条
        preview_scrollbar = ttk.Scrollbar(preview_container, orient="vertical", 
                                        command=self.preview_content.yview)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_content.configure(yscrollcommand=preview_scrollbar.set)
        
        # 创建底部状态栏
        status_bar = ttk.Frame(main_container, style='TFrame')
        status_bar.pack(fill=tk.X, pady=(15, 0))
        
        # 创建焦点提示标签
        self.focus_label = ttk.Label(status_bar, text="当前焦点：笔记列表", 
                                   font=('Microsoft YaHei UI', 9), 
                                   foreground='#666666')
        self.focus_label.pack(side=tk.LEFT)
        
        # 底部状态栏不再需要快捷键提示标签，已移至搜索框下方
        
        # 绑定选择事件和焦点事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('j', self.select_next_note)
        self.tree.bind('k', self.select_prev_note)
        self.tree.bind('<Return>', self.focus_preview)
        self.tree.bind('<Tab>', self.focus_preview)
        self.tree.bind('<FocusOut>', lambda e: self.check_focus_widget())
        
        # 绑定预览区域的ESC键、Tab键和焦点事件
        self.preview_content.bind('<Tab>', self.focus_list)
        self.preview_content.bind('<Escape>', self.clear_selection)  # 添加ESC键取消选中功能
        self.preview_content.bind('<FocusOut>', lambda e: self.check_focus_widget())
        
        # 绑定窗口大小改变事件
        self.preview_frame.bind("<Configure>", self._on_preview_resize)
        
        # 初始化显示
        self.refresh_notes()
        
        # 设置关闭窗口的行为
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
        # 绑定ESC键处理
        self.root.bind('<Escape>', self.handle_escape_key)
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 启动托盘图标线程
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()
        
        # 启动快捷键监听线程
        self.hotkey_thread = threading.Thread(target=self.start_hotkey_listener, daemon=True)
        self.hotkey_thread.start()
    
    def create_tray_icon(self):
        # 创建一个简单的图标
        icon_data = '''
            <svg width="64" height="64" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" fill="#4CAF50"/>
                <text x="32" y="42" font-family="Arial" font-size="40" fill="white" text-anchor="middle">N</text>
            </svg>
        '''
        image = Image.open("icon.png")
        # 创建菜单项
        menu = (pystray.MenuItem('显示', self.show_window),
                pystray.MenuItem('退出', self.quit_window))
        
        # 创建图标
        self.icon = pystray.Icon('fastnote', image, 'FastNote', menu)
    
    def handle_hotkey(self, callback, require_focus=False):
        # 如果需要焦点但窗口没有显示或没有焦点，则不执行操作
        if require_focus:
            # 检查窗口是否可见且有焦点
            if not self.root.winfo_viewable() or not self.root.focus_displayof():
                return
        # 如果窗口被隐藏，则显示窗口
        elif not self.root.winfo_viewable():
            self.root.deiconify()
            # 将窗口移到屏幕中央
            self.center_window()
        # 使用after确保在主线程中执行回调
        self.root.after(10, callback)
    
    def center_window(self):
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 获取窗口尺寸
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        # 计算窗口位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        # 设置窗口位置
        self.root.geometry(f"+{x}+{y}")
    
    def start_hotkey_listener(self):
        # 设置快捷键监听
        with keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+1': lambda: self.handle_hotkey(self.handle_screenshot),  # 截图保存
            '<ctrl>+<alt>+2': lambda: self.handle_hotkey(self.handle_selected_text),  # 选中文本保存
            '<ctrl>+<alt>+3': lambda: self.handle_hotkey(self.handle_direct_input),  # 直接输入保存
            '<ctrl>+<alt>+f': lambda: self.handle_hotkey(self.focus_search),  # 聚焦搜索框
            '<ctrl>+d': lambda: self.handle_hotkey(self.delete_note, require_focus=True)  # 删除笔记（需要窗口有焦点）
        }) as h:
            h.join()
    
    def create_save_dialog(self, screenshot):
        # 确保主窗口可见并在最前
        self.root.deiconify()
        self.root.lift()
        
        # 创建独立的保存对话框窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("保存截图")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)  # 设置为主窗口的临时窗口
        dialog.grab_set()  # 设置为模态窗口
        
        # 获取屏幕尺寸
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # 设置窗口大小和位置
        window_width = 400
        window_height = 180
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标题输入框
        ttk.Label(dialog, text="请输入标题：", font=('Microsoft YaHei UI', 12)).pack(pady=10)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, font=('Microsoft YaHei UI', 12), width=40)
        title_entry.pack(pady=5)
        # 确保对话框显示后立即获得焦点
        dialog.lift()
        dialog.focus_force()
        title_entry.focus_set()
        
        # 等待窗口显示后再次设置焦点
        def ensure_focus():
            dialog.lift()
            dialog.focus_force()
            title_entry.focus_set()
        dialog.after(100, ensure_focus)
        
        def save():
            title = title_var.get().strip()
            if title:
                # 保存截图到临时文件
                temp_path = "temp_screenshot.png"
                screenshot.save(temp_path)
                
                # 读取图片内容
                with open(temp_path, 'rb') as f:
                    content = f.read()
                
                # 保存到数据库
                self.db.add_note(title, content, note_type='image')
                self.refresh_notes()
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请输入标题！", parent=dialog)
        
        def cancel():
            dialog.destroy()
        
        # 显示快捷键提示
        ttk.Label(dialog, text="快捷键：Enter 保存，ESC 取消", foreground='gray').pack(side=tk.BOTTOM, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        save_button = ttk.Button(button_frame, text="保存", command=save)
        save_button.pack(side=tk.LEFT, padx=20)

        cancel_button = ttk.Button(button_frame, text="取消", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=20)
        
        # 绑定回车键为保存
        dialog.bind('<Return>', lambda e: save())
        # 绑定ESC键为取消
        dialog.bind('<Escape>', lambda e: cancel())
    
    def handle_screenshot(self):
        # 隐藏主窗口
        self.root.withdraw()

        # 创建提示窗口
        hint_window = tk.Toplevel()
        hint_window.attributes('-topmost', True)
        hint_window.overrideredirect(True)
        hint_label = ttk.Label(hint_window, text="请按住鼠标左键选择截图区域，松开完成截图")
        hint_label.pack(padx=10, pady=5)
        
        # 获取屏幕尺寸
        screen_width = hint_window.winfo_screenwidth()
        screen_height = hint_window.winfo_screenheight()
        
        # 将提示窗口放在屏幕中央
        hint_window.geometry(f"+{screen_width//2-150}+{screen_height//2-25}")
        
        # 创建全屏遮罩窗口
        overlay = tk.Toplevel()
        overlay.attributes('-alpha', 0.3, '-topmost', True)
        overlay.geometry(f"{screen_width}x{screen_height}+0+0")
        overlay.overrideredirect(True)
        
        # 创建全屏画布
        canvas = tk.Canvas(overlay, width=screen_width, height=screen_height, 
                          highlightthickness=0, bg='gray')
        canvas.pack()
        
        start_x = start_y = 0
        end_x = end_y = 0
        is_drawing = False
        selection_rect = None
        selection_mask = None
        
        def draw_selection(x1, y1, x2, y2):
            nonlocal selection_rect, selection_mask
            if selection_rect:
                canvas.delete(selection_rect)

            
            # 创建选择框
            selection_rect = canvas.create_rectangle(
                x1, y1, x2, y2, outline="#00FF00", width=5, dash=(2, 2)
            )
        
        def on_mouse_down(event):
            nonlocal start_x, start_y, is_drawing
            start_x, start_y = event.x, event.y
            is_drawing = True
        
        def on_mouse_move(event):
            nonlocal end_x, end_y
            if is_drawing:
                end_x, end_y = event.x, event.y
                draw_selection(start_x, start_y, end_x, end_y)
        
        def on_mouse_up(event):
            nonlocal is_drawing, start_x, start_y, end_x, end_y
            if is_drawing:
                is_drawing = False
                end_x, end_y = event.x, event.y
                
                # 确保坐标正确（处理反向拖动的情况）
                if end_x < start_x:
                    start_x, end_x = end_x, start_x
                if end_y < start_y:
                    start_y, end_y = end_y, start_y
                
                # 关闭提示窗口和遮罩窗口
                hint_window.destroy()
                overlay.destroy()
                
                # 获取选定区域的截图
                screenshot = ImageGrab.grab(bbox=(start_x, start_y, end_x, end_y))
                
                # 显示保存对话框
                self.create_save_dialog(screenshot)

                # 恢复主窗口
                self.root.deiconify()
        
        # 绑定鼠标事件
        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        
        # 绑定ESC键取消截图
        def cancel_screenshot(event):
            hint_window.destroy()
            overlay.destroy()
            self.root.deiconify() # 恢复主窗口
        
        overlay.bind('<Escape>', cancel_screenshot)
    
    def create_text_save_dialog(self, text):
        # 确保主窗口可见并在最前
        self.root.deiconify()
        self.root.lift()
        
        # 创建独立的保存对话框窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("保存选中文本")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)  # 设置为主窗口的临时窗口
        dialog.grab_set()  # 设置为模态窗口
        
        # 获取屏幕尺寸
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # 设置窗口大小和位置
        window_width = 400
        window_height = 180
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标题输入框
        ttk.Label(dialog, text="请输入标题：", font=('Microsoft YaHei UI', 12)).pack(pady=10)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, font=('Microsoft YaHei UI', 12), width=40)
        title_entry.pack(pady=5)
        # 确保对话框显示后立即获得焦点
        dialog.lift()
        dialog.focus_force()
        title_entry.focus_set()
        
        # 等待窗口显示后再次设置焦点
        def ensure_focus():
            dialog.lift()
            dialog.focus_force()
            title_entry.focus_set()
        dialog.after(100, ensure_focus)
        
        def save():
            title = title_var.get().strip()
            if title:
                self.db.add_note(title, text, note_type='text')
                self.refresh_notes()
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请输入标题！", parent=dialog)
        
        def cancel():
            dialog.destroy()
        
        # 显示快捷键提示
        ttk.Label(dialog, text="快捷键：Enter 保存，ESC 取消", foreground='gray').pack(side=tk.BOTTOM, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        save_button = ttk.Button(button_frame, text="保存", command=save)
        save_button.pack(side=tk.LEFT, padx=20)

        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.LEFT, padx=20)
        
        # 绑定回车键为保存
        dialog.bind('<Return>', lambda e: save())
        # 绑定ESC键为取消
        dialog.bind('<Escape>', lambda e: cancel())
    
    def handle_selected_text(self):
        # 尝试使用 pyperclip 获取剪贴板内容
        try:
            text = pyperclip.paste()
        except pyperclip.PyperclipException:
            # 如果 pyperclip 失败，回退到 win32clipboard
            try:
                win32clipboard.OpenClipboard()
                text = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                if isinstance(text, bytes):
                    text = text.decode('gbk')
            except:
                text = ""
            finally:
                win32clipboard.CloseClipboard()
        
        if text:
            # 显示保存对话框
            self.create_text_save_dialog(text)
    
    def create_direct_input_dialog(self):
        # 确保主窗口可见并在最前
        self.root.deiconify()
        self.root.lift()
        
        # 创建独立的输入对话框窗口
        dialog = tk.Toplevel(self.root)
        dialog.title("新建笔记")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)  # 设置为主窗口的临时窗口
        dialog.grab_set()  # 设置为模态窗口
        
        # 获取屏幕尺寸
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        # 设置窗口大小和位置
        window_width = 400
        window_height = 390
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标题输入框
        ttk.Label(dialog, text="请输入标题：", font=('Microsoft YaHei UI', 12)).pack(pady=10)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, font=('Microsoft YaHei UI', 12), width=40)
        title_entry.pack(pady=5)
        # 确保对话框显示后立即获得焦点
        dialog.lift()
        dialog.focus_force()
        title_entry.focus_set()
        
        # 等待窗口显示后再次设置焦点
        def ensure_focus():
            dialog.lift()
            dialog.focus_force()
            title_entry.focus_set()
        dialog.after(100, ensure_focus)
        
        # 创建内容输入框
        ttk.Label(dialog, text="请输入内容：", font=('Microsoft YaHei UI', 12)).pack(pady=10)
        content_text = tk.Text(dialog, font=('Microsoft YaHei UI', 12), wrap="word", width=40, height=8)
        content_text.pack(pady=5)
        
        def save():
            title = title_var.get().strip()
            content = content_text.get("1.0", tk.END).strip()
            if title and content:
                self.db.add_note(title, content, note_type='text')
                self.refresh_notes()
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "标题和内容不能为空！", parent=dialog)
        
        def cancel():
            dialog.destroy()
        
        # 显示快捷键提示
        ttk.Label(dialog, text="快捷键：Ctrl+S 保存，ESC 取消", foreground='gray').pack(side=tk.BOTTOM, pady=5)

        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        save_button = ttk.Button(button_frame, text="保存", command=save)
        save_button.pack(side=tk.LEFT, padx=20)

        cancel_button = ttk.Button(button_frame, text="取消", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=20)
        
        # 绑定回车键为保存（当焦点在标题输入框时）
        title_entry.bind('<Return>', lambda e: content_text.focus())
        # 绑定Ctrl+S为保存
        dialog.bind('<Control-s>', lambda e: save())
        # 绑定ESC键为取消
        dialog.bind('<Escape>', lambda e: cancel())
    
    def handle_direct_input(self):
        # 显示输入对话框
        self.create_direct_input_dialog()
    
    def handle_escape_key(self, event=None):
        """处理ESC键：取消选中笔记并最小化到托盘"""
        # 如果有选中的笔记，先取消选中
        if self.tree.selection():
            self.clear_selection(event)
        # 然后最小化到托盘
        self.minimize_to_tray()
        return 'break'  # 阻止事件继续传播
    
    def minimize_to_tray(self):
        self.root.withdraw()  # 隐藏窗口
        self.focus_label.config(text="")  # 清空焦点提示
        # 重置边框样式
        self.list_frame.configure(style='Normal.TFrame')
        self.preview_frame.configure(style='Normal.TFrame')

    
    def show_window(self):
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 将窗口提升到最前
        self.center_window()  # 居中显示窗口
        # 恢复焦点到笔记列表并更新提示
        self.tree.focus_set()
        self.focus_label.config(text="当前焦点：笔记列表")
        # 更新边框样式
        self.list_frame.configure(style='Focused.TFrame')
        self.preview_frame.configure(style='Normal.TFrame')
    
    def quit_window(self):
        if self.icon:
            self.icon.stop()
        self.root.quit()
    
    def refresh_notes(self, search_text=None):
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 从数据库获取笔记
        if search_text:
            notes = self.db.search_notes_by_title(search_text)
        else:
            notes = self.db.get_all_notes()
        
        # 添加笔记到列表
        for note in notes:
            display_values = (note[0], note[1], note[4], note[2], note[3])
            self.tree.insert("", tk.END, values=display_values)
    
    def search_notes(self):
        search_text = self.search_var.get().strip()
        self.refresh_notes(search_text)
        # 搜索完成后，如果存在结果，则选中第一个
        if self.tree.get_children():
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
            self.tree.see(first_item) # 确保第一个项目可见
            self.tree.focus_set() # 将焦点设置到Treeview上
            self.focus_label.config(text="当前焦点：笔记列表")
    
    def select_next_note(self, event=None):
        current_selection = self.tree.selection()
        if not current_selection:
            # 如果没有选中任何项，选中第一个
            if self.tree.get_children():
                first_item = self.tree.get_children()[0]
                self.tree.selection_set(first_item)
                self.tree.focus(first_item)
                self.tree.see(first_item)
            return

        current_item = current_selection[0]
        next_item = self.tree.next(current_item)
        if next_item:
            self.tree.selection_set(next_item)
            self.tree.focus(next_item)
            self.tree.see(next_item)

    def select_prev_note(self, event=None):
        current_selection = self.tree.selection()
        if not current_selection:
            # 如果没有选中任何项，选中最后一个
            if self.tree.get_children():
                last_item = self.tree.get_children()[-1]
                self.tree.selection_set(last_item)
                self.tree.focus(last_item)
                self.tree.see(last_item)
            return

        current_item = current_selection[0]
        prev_item = self.tree.prev(current_item)
        if prev_item:
            self.tree.selection_set(prev_item)
            self.tree.focus(prev_item)
            self.tree.see(prev_item)

    def focus_search(self):
        # 聚焦到搜索框
        self.search_entry.focus_set()
        # 全选搜索框中的文本
        self.search_entry.select_range(0, tk.END)
        # 更新焦点提示
        self.focus_label.config(text="当前焦点：搜索框")
        # 重置边框样式
        self.list_frame.configure(style='Normal.TFrame')
        self.preview_frame.configure(style='Normal.TFrame')
    
    def focus_preview(self, event=None):
        # 聚焦到预览区域
        self.preview_content.focus_set()
        self.focus_label.config(text="当前焦点：预览区域")
        # 更新边框样式
        self.preview_frame.configure(style='Focused.TFrame')
        self.list_frame.configure(style='Normal.TFrame')
        if event and event.keysym == 'Tab':
            return 'break'  # 阻止默认的Tab键行为
    
    def focus_list(self, event=None):
        # 聚焦到笔记列表
        self.tree.focus_set()
        self.focus_label.config(text="当前焦点：笔记列表")
        # 更新边框样式
        self.list_frame.configure(style='Focused.TFrame')
        self.preview_frame.configure(style='Normal.TFrame')
        if event and event.keysym == 'Tab':
            return 'break'  # 阻止默认的Tab键行为
    
    def check_focus_widget(self):
        # 检查当前焦点所在的控件
        focused = self.root.focus_get()
        if focused == self.search_entry:
            self.focus_label.config(text="当前焦点：搜索框")
            self.list_frame.configure(style='Normal.TFrame')
            self.preview_frame.configure(style='Normal.TFrame')
        elif focused == self.tree:
            self.focus_label.config(text="当前焦点：笔记列表")
            self.list_frame.configure(style='Focused.TFrame')
            self.preview_frame.configure(style='Normal.TFrame')
        elif focused == self.preview_content:
            self.focus_label.config(text="当前焦点：预览区域")
            self.list_frame.configure(style='Normal.TFrame')
            self.preview_frame.configure(style='Focused.TFrame')
        else:
            self.focus_label.config(text="")  # 当焦点在其他控件时清空提示
            self.list_frame.configure(style='Normal.TFrame')
            self.preview_frame.configure(style='Normal.TFrame')
    
    def clear_selection(self, event=None):
        """取消选中当前笔记"""
        # 清除当前选中项
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        # 清空预览区域
        self.preview_title.config(text="")
        self.preview_content.config(state="normal")
        self.preview_content.delete(1.0, tk.END)
        self.preview_content.config(state="disabled")
        return 'break'  # 阻止事件继续传播
    
    def delete_note(self):
        # 如果窗口没有显示或没有焦点，则不执行删除操作
        if not self.root.winfo_viewable() or not self.root.focus_displayof():
            return
        
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要删除的笔记！")
            return

        if messagebox.askyesno("确认删除", "确定要删除选中的笔记吗？"):
            for item in selected_items:
                note_id = self.tree.item(item)['values'][0]
                self.db.delete_note(note_id)
            self.refresh_notes()
            # 清空预览区域
            self.preview_title.config(text="")
            self.preview_content.config(state="normal")
            self.preview_content.delete("1.0", tk.END)
            self.preview_content.config(state="disabled")

    def _on_preview_resize(self, event):
        # 只有当有图片显示时才重新调整大小
        if hasattr(self, 'current_image_data') and self.current_image_data:
            self.preview_content.config(state="normal")
            self.preview_content.delete("1.0", tk.END)
            
            img = Image.open(io.BytesIO(self.current_image_data))
            
            # 获取新的预览区域大小
            preview_width = self.preview_content.winfo_width()
            preview_height = self.preview_content.winfo_height()
            
            img = self._resize_image(img, preview_width, preview_height)
            self.current_image_photo = ImageTk.PhotoImage(img)
            
            self.preview_content.image_create("1.0", image=self.current_image_photo)
            self.preview_content.insert("1.0", "\n\n")
            self.preview_content.config(state="disabled")

    def _resize_image(self, img, width, height):
        if width <= 1 or height <= 1: # 避免除以零或负数
            return img
        
        original_width, original_height = img.size
        
        # 计算缩放比例
        ratio_w = width / original_width
        ratio_h = height / original_height
        
        # 选择较小的比例以确保图片完全显示
        ratio = min(ratio_w, ratio_h)
        
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        return img.resize((new_width, new_height), Image.LANCZOS)

    def on_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            # 清空预览区域
            self.preview_title.config(text="")
            self.preview_content.config(state="normal")
            self.preview_content.delete("1.0", tk.END)
            self.preview_content.config(state="disabled")
            return
            
        item = selected_items[0]
        note_id = self.tree.item(item)['values'][0]
        self.current_note_id = note_id  # 存储当前笔记ID
        title, content, note_type = self.db.get_note_content(note_id)
        
        if title and content:
            # 更新预览标题
            self.preview_title.config(text=title)
            
            # 清空并更新预览内容
            self.preview_content.config(state="normal")
            self.preview_content.delete("1.0", tk.END)
            
            if note_type == 'image':
                # 从二进制数据创建图片
                img = Image.open(io.BytesIO(content))
                
                # 调整图片大小以适应预览区域
                preview_width = self.preview_content.winfo_width()
                preview_height = self.preview_content.winfo_height()
                # 调整图片大小以适应预览区域
                img = self._resize_image(img, preview_width, preview_height)
                
                # 转换为PhotoImage以在Tkinter中显示
                self.current_image_data = content # 存储原始图片数据
                self.current_image_photo = ImageTk.PhotoImage(img) # 存储PhotoImage引用
                
                # 在文本框中插入图片
                self.preview_content.image_create("1.0", image=self.current_image_photo)
                self.preview_content.insert("1.0", "\n\n")  # 添加一些空行
                self.preview_content.config(state="disabled")
                
                # 绑定复制图片快捷键
                self.preview_content.bind('<Control-c>', self.copy_image_to_clipboard)
            else:
                # 文本类型直接显示并允许编辑
                self.preview_content.insert("1.0", content)
                self.preview_content.config(state="normal")
                
                # 绑定保存和复制快捷键
                self.preview_content.bind('<Control-s>', self.save_text_content)
                self.preview_content.bind('<Control-c>', self.copy_text_to_clipboard)

    def copy_text_to_clipboard(self, event=None):
        try:
            # 获取选中的文本
            selected_text = self.preview_content.get(tk.SEL_FIRST, tk.SEL_LAST)
            pyperclip.copy(selected_text)
            messagebox.showinfo("提示", "文本已复制到剪贴板")
        except tk.TclError:  # 如果没有选中文本
            try:
                # 复制全部文本
                all_text = self.preview_content.get("1.0", tk.END).strip()
                pyperclip.copy(all_text)
                messagebox.showinfo("提示", "全部文本已复制到剪贴板")
            except:
                messagebox.showerror("错误", "复制文本失败")
    
    def copy_image_to_clipboard(self, event=None):
        if hasattr(self, 'current_image_data') and self.current_image_data:
            # 将图片数据转换为PIL Image对象
            img = Image.open(io.BytesIO(self.current_image_data))
            
            try:
                # 将图片转换为BMP格式
                output = io.BytesIO()
                if img.mode == 'RGBA':
                    # 如果图片有透明通道，先将其转换为RGB
                    img = img.convert('RGB')
                img.save(output, 'BMP')
                data = output.getvalue()[14:]  # 跳过BMP文件头
                output.close()
                
                # 确保剪贴板已关闭
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                
                # 打开剪贴板并写入数据
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            except Exception as e:
                messagebox.showerror("错误", f"复制图片失败: {str(e)}")
                return
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
            
            messagebox.showinfo("提示", "图片已复制到剪贴板")
    
    def save_text_content(self, event=None):
        if hasattr(self, 'current_note_id'):
            # 获取当前文本内容
            content = self.preview_content.get("1.0", tk.END).strip()
            # 获取当前笔记标题
            title = self.preview_title.cget("text")
            
            # 更新数据库
            self.db.update_note(self.current_note_id, title, content)
            
            # 刷新笔记列表
            self.refresh_notes()
            
            messagebox.showinfo("提示", "笔记已保存")

def main():
    root = tk.Tk()
    app = NoteApp(root)   
    root.mainloop()

if __name__ == "__main__":
    main()
