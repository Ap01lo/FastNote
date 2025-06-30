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
        self.root.title('FastNote')
        self.db = DatabaseManager()
        
        # 创建搜索框架
        self.search_frame = ttk.Frame(self.root, padding="15 5")
        self.search_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        # 创建搜索框和按钮
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, font=('Microsoft YaHei UI', 12))
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_button = ttk.Button(self.search_frame, text="搜索", command=self.search_notes)
        self.search_button.grid(row=0, column=1)
        
        # 绑定回车键到搜索功能
        self.search_entry.bind('<Return>', lambda e: self.search_notes())
        
        # 添加快捷键提示标签
        ttk.Label(self.search_frame, text="搜索快捷键：Ctrl+Alt+F；截图保存：Ctrl+Alt+1；剪贴板保存：Ctrl+Alt+2；输入文本保存：Ctrl+Alt+3", foreground='gray').grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        
        # 创建主框架
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # 左侧笔记列表框架
        self.list_frame = ttk.Frame(self.root, padding="15")
        self.list_frame.grid(row=1, column=0, sticky="nsew")
        self.list_frame.grid_rowconfigure(1, weight=1)
        self.list_frame.grid_columnconfigure(0, weight=1)
        
        # 右侧预览框架
        self.preview_frame = ttk.Frame(self.root, padding="15")
        self.preview_frame.grid(row=1, column=1, sticky="nsew")
        self.preview_frame.grid_rowconfigure(1, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        # 初始化样式
        self.style = ttk.Style()

        
        # 笔记列表
        self.tree = ttk.Treeview(self.list_frame, columns=("ID", "标题", "类型", "创建时间", "更新时间"), 
                               show="headings", style="Custom.Treeview")
        self.tree.grid(row=1, column=0, sticky="nsew")
        
        # 预览区域
        self.preview_title = ttk.Label(self.preview_frame, text="", font=('Microsoft YaHei UI', 14, 'bold'))
        self.preview_title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # 创建预览内容的容器框架
        preview_container = ttk.Frame(self.preview_frame)
        preview_container.grid(row=1, column=0, sticky="nsew")
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
        
        # 预览内容和滚动条
        self.preview_content = tk.Text(preview_container, font=('Microsoft YaHei UI', 12), wrap="word", state="disabled")
        self.preview_content.grid(row=0, column=0, sticky="nsew")
        
        preview_scrollbar = ttk.Scrollbar(preview_container, orient="vertical", command=self.preview_content.yview)
        preview_scrollbar.grid(row=0, column=1, sticky="ns")
        self.preview_content.configure(yscrollcommand=preview_scrollbar.set)
        
        # 删除按钮
        self.delete_button = ttk.Button(self.list_frame, text="删除笔记", command=self.delete_note)
        self.delete_button.grid(row=0, column=0, sticky="e", pady=(0, 10))
        
        # 设置Treeview样式
        self.style.configure("Custom.Treeview", font=('Microsoft YaHei UI', 12), rowheight=30)
        self.style.configure("Custom.Treeview.Heading", font=('Microsoft YaHei UI', 12, 'bold'))
        
        # 设置列标题
        self.tree.heading("ID", text="ID", anchor="center")
        self.tree.heading("标题", text="标题", anchor="w")
        self.tree.heading("类型", text="类型", anchor="center")
        self.tree.heading("创建时间", text="创建时间", anchor="center")
        self.tree.heading("更新时间", text="更新时间", anchor="center")
        
        # 设置列宽
        self.tree.column("ID", stretch=tk.YES, anchor="center")
        self.tree.column("标题", stretch=tk.YES, anchor="w")
        self.tree.column("类型", stretch=tk.YES, anchor="center")
        self.tree.column("创建时间", stretch=tk.YES, anchor="center")
        self.tree.column("更新时间", stretch=tk.YES, anchor="center")
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定窗口大小改变事件
        self.preview_frame.bind("<Configure>", self._on_preview_resize)
        
        # 设置窗口最小尺寸
        self.root.minsize(1000, 600)
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("icon.png")
        except:
            pass
        
        # 初始化显示
        self.refresh_notes()
        
        # 设置关闭窗口的行为
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
        # 绑定ESC键最小化到托盘
        self.root.bind('<Escape>', lambda e: self.minimize_to_tray())
        
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
    
    def handle_hotkey(self, callback):
        # 确保窗口状态正确
        if self.icon is not None and self.icon._icon is not None:
            # 如果在托盘中，先停止托盘图标并显示主窗口
            self.icon.stop()
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
            '<ctrl>+<alt>+f': lambda: self.handle_hotkey(self.focus_search)  # 聚焦搜索框
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
    
    def minimize_to_tray(self):
        self.root.withdraw()  # 隐藏窗口

    
    def show_window(self):

        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 将窗口提升到最前
        self.center_window()  # 居中显示窗口
    
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
    
    def focus_search(self):
        # 聚焦到搜索框
        self.search_entry.focus_set()
        # 全选搜索框中的文本
        self.search_entry.select_range(0, tk.END)
    
    def delete_note(self):
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
            else:
                # 文本类型直接显示
                self.preview_content.insert("1.0", content)
            
            self.preview_content.config(state="disabled")

def main():
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    main()
