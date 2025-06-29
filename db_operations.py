import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_file = 'notes.db'
        self.init_db()
    
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 创建表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content BLOB NOT NULL,
                    note_type TEXT DEFAULT 'text',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_connection(self):
        return sqlite3.connect(self.db_file)
    
    def add_note(self, title, content, note_type='text'):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notes (title, content, note_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, content, note_type, current_time, current_time))
            conn.commit()
    
    def get_all_notes(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, created_at, updated_at, note_type
                FROM notes
                ORDER BY updated_at DESC
            ''')
            return cursor.fetchall()
    
    def get_note_content(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, content, note_type
                FROM notes
                WHERE id = ?
            ''', (note_id,))
            result = cursor.fetchone()
            if result:
                title, content, note_type = result
                if note_type == 'text':
                    # 如果是文本类型，尝试解码为字符串
                    try:
                        if isinstance(content, bytes):
                            content = content.decode('utf-8')
                    except:
                        content = str(content)
                return title, content, note_type
            return None, None, None
    
    def update_note(self, note_id, title, content):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE notes
                SET title = ?, content = ?, updated_at = ?
                WHERE id = ?
            ''', (title, content, current_time, note_id))
            conn.commit()
    
    def delete_note(self, note_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
            conn.commit()
    
    def search_notes_by_title(self, search_text):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, created_at, updated_at, note_type
                FROM notes
                WHERE title LIKE ?
                ORDER BY updated_at DESC
            ''', (f'%{search_text}%',))
            return cursor.fetchall()