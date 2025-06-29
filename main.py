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
        
        # 创建主框架
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.main_frame = ttk.Frame(self.root, padding="15")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置主框架的行列权重
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_rowconfigure(3, weight=8)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)
        
        # 标题输入
        ttk.Label(self.main_frame, text="标题:", font=('Microsoft YaHei UI', 12)).grid(row=0, column=0, sticky="w", pady=(0,5))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(self.main_frame, textvariable=self.title_var, font=('Microsoft YaHei UI', 14))
        self.title_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=(0,5))
        
        # 内容输入
        ttk.Label(self.main_frame, text="内容:", font=('Microsoft YaHei UI', 12)).grid(row=1, column=0, sticky="nw", pady=(0,5))
        self.content_text = tk.Text(self.main_frame, font=('Microsoft YaHei UI', 14), wrap="word", height=5)
        self.content_text.grid(row=1, column=1, columnspan=3, sticky="nsew", pady=(0,5))
        
        # 按钮区域
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 15), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)

        # 初始化样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=('Microsoft YaHei UI', 12), padding=10)

        self.save_button = ttk.Button(button_frame, text="保存笔记", command=self.save_note)
        self.save_button.grid(row=0, column=0, sticky="ew", padx=5)

        self.clear_button = ttk.Button(button_frame, text="清空输入", command=self.clear_inputs)
        self.clear_button.grid(row=0, column=1, sticky="ew", padx=5)

        self.refresh_button = ttk.Button(button_frame, text="刷新笔记", command=self.refresh_notes)
        self.refresh_button.grid(row=0, column=2, sticky="ew", padx=5)

        self.delete_button = ttk.Button(button_frame, text="删除笔记", command=self.delete_note)
        self.delete_button.grid(row=0, column=3, sticky="ew", padx=5)
        
        # 笔记列表
        self.tree = ttk.Treeview(self.main_frame, columns=("ID", "标题", "类型", "创建时间", "更新时间"), 
                               show="headings", style="Custom.Treeview")
        self.tree.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(10,0))
        
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
        self.tree.column("ID", width=50, stretch=tk.NO, anchor="center")
        self.tree.column("标题", width=200, stretch=tk.YES, anchor="w")
        self.tree.column("类型", width=80, stretch=tk.NO, anchor="center")
        self.tree.column("创建时间", width=150, stretch=tk.NO, anchor="center")
        self.tree.column("更新时间", width=150, stretch=tk.NO, anchor="center")
        
        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=3, column=3, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 设置窗口最小尺寸
        self.root.minsize(600, 500)
        
        # 设置窗口图标
        try:
            self.root.iconbitmap("icon.png")
        except:
            pass
        
        # 初始化显示
        self.refresh_notes()
        
        # 设置关闭窗口的行为
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
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
            '<ctrl>+<alt>+3': lambda: self.handle_hotkey(self.handle_direct_input)  # 直接输入保存
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
        window_height = 150
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标题输入框
        ttk.Label(dialog, text="请输入标题：", font=('Arial', 10)).pack(pady=10)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, font=('Arial', 10), width=40)
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
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        
        self.style.configure("TButton", font=('Arial', 10), padding=8)

        save_button = ttk.Button(button_frame, text="保存", command=save)
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # 绑定回车键为保存
        dialog.bind('<Return>', lambda e: save())
        # 绑定ESC键为取消
        dialog.bind('<Escape>', lambda e: cancel())
        
        # 显示快捷键提示
        ttk.Label(dialog, text="快捷键：Enter 保存，ESC 取消", foreground='gray').pack(side=tk.BOTTOM, pady=5)
    
    def handle_screenshot(self):
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
            if selection_mask:
                canvas.delete(selection_mask)
            
            # 创建遮罩（四个矩形覆盖未选择区域）
            selection_mask = [
                canvas.create_rectangle(0, 0, screen_width, y1, fill='gray', stipple='gray50'),
                canvas.create_rectangle(0, y2, screen_width, screen_height, fill='gray', stipple='gray50'),
                canvas.create_rectangle(0, y1, x1, y2, fill='gray', stipple='gray50'),
                canvas.create_rectangle(x2, y1, screen_width, y2, fill='gray', stipple='gray50')
            ]
            
            # 创建选择框
            selection_rect = canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red', width=2
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
        
        # 绑定鼠标事件
        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        
        # 绑定ESC键取消截图
        def cancel_screenshot(event):
            hint_window.destroy()
            overlay.destroy()
        
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
        window_height = 150
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标题输入框
        ttk.Label(dialog, text="请输入标题：", font=('Arial', 10)).pack(pady=10)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, font=('Arial', 10), width=40)
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
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        
        self.style.configure("TButton", font=('Arial', 10), padding=8)

        save_button = ttk.Button(button_frame, text="保存", command=save)
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = ttk.Button(button_frame, text="取消", command=cancel)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
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
        window_height = 300
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建标题输入框
        ttk.Label(dialog, text="请输入标题：", font=('Arial', 10)).pack(pady=10)
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, font=('Arial', 10), width=40)
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
        ttk.Label(dialog, text="请输入内容：", font=('Arial', 10)).pack(pady=10)
        content_text = tk.Text(dialog, font=('Arial', 10), wrap="word", width=40, height=8)
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
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        
        self.style.configure("TButton", font=('Arial', 10), padding=8)

        save_button = ttk.Button(button_frame, text="保存", command=save)
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = ttk.Button(button_frame, text="取消", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # 绑定回车键为保存（当焦点在标题输入框时）
        title_entry.bind('<Return>', lambda e: content_text.focus())
        # 绑定Ctrl+S为保存
        dialog.bind('<Control-s>', lambda e: save())
        # 绑定ESC键为取消
        dialog.bind('<Escape>', lambda e: cancel())
        
        # 显示快捷键提示
        ttk.Label(dialog, text="快捷键：Ctrl+S 保存，ESC 取消", foreground='gray').pack(side=tk.BOTTOM, pady=5)
    
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
    
    def save_note(self):
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        
        if not title:
            messagebox.showwarning("提示", "请输入标题！")
            return
            
        self.db.add_note(title, content, note_type='text')
        self.refresh_notes()
        self.clear_inputs()
    
    def clear_inputs(self):
        self.title_var.set("")
        self.content_text.delete("1.0", tk.END)
    
    def refresh_notes(self):
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取并显示笔记
        notes = self.db.get_all_notes()
        for note in notes:
            # note 结构为 (id, title, content, created_at, updated_at, note_type)
            # Treeview 列为 ("ID", "标题", "类型", "创建时间", "更新时间")
            # 提取所需字段并按顺序插入
            display_values = (note[0], note[1], note[4], note[2], note[3])
            self.tree.insert("", tk.END, values=display_values)
    
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
            self.clear_inputs()

    def on_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        note_id = self.tree.item(item)['values'][0]
        title, content, note_type = self.db.get_note_content(note_id)
        
        if title and content:
            self.title_var.set(title)
            self.content_text.delete("1.0", tk.END)
            
            if note_type == 'image':
                # 创建新窗口显示图片
                img_window = tk.Toplevel(self.root)
                img_window.title(title)
                
                # 从二进制数据创建图片
                img = Image.open(io.BytesIO(content))
                
                # 调整图片大小以适应屏幕
                screen_width = self.root.winfo_screenwidth() - 100
                screen_height = self.root.winfo_screenheight() - 100
                img.thumbnail((screen_width, screen_height))
                
                # 转换为PhotoImage以在Tkinter中显示
                photo = ImageTk.PhotoImage(img)
                img_label = ttk.Label(img_window, image=photo)
                img_label.image = photo  # 保持引用
                img_label.pack()
            else:
                # 文本类型直接显示在文本框中
                self.content_text.insert("1.0", content)

def main():
    root = tk.Tk()
    app = NoteApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    main()
