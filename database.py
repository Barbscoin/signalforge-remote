import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple


class Database:
    """SQLite database for SignalForge"""
    
    def __init__(self, db_path="signalforge.db"):
        self.db_path = Path(db_path)
        self.init_schema()
    
    def _get_conn(self):
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_schema(self):
        """Initialize database schema"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                keywords TEXT,
                link TEXT,
                published TEXT,
                collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        
        # Servers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                host TEXT NOT NULL,
                user TEXT NOT NULL,
                status TEXT DEFAULT 'offline',
                last_checked TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # System logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers(id)
            )
        """)
        
        # Session logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                command TEXT NOT NULL,
                output TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1,
                FOREIGN KEY (server_id) REFERENCES servers(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ===== SIGNALS =====
    def save_signal(self, score: int, title: str, keywords: str, link: str, 
                    published: str, summary: str = None, source: str = None) -> int:
        """Save a signal to database"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signals (score, title, summary, keywords, link, published, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (score, title, summary, keywords, link, published, source))
        conn.commit()
        signal_id = cursor.lastrowid
        conn.close()
        return signal_id
    
    def get_signals(self, limit=100, offset=0, resolved=False) -> List[Dict]:
        """Get signals from database"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM signals 
            WHERE resolved = ?
            ORDER BY score DESC, collected_at DESC
            LIMIT ? OFFSET ?
        """, (1 if resolved else 0, limit, offset))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_signal_resolved(self, signal_id: int):
        """Mark signal as resolved"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("UPDATE signals SET resolved = 1 WHERE id = ?", (signal_id,))
        conn.commit()
        conn.close()
    
    # ===== SERVERS =====
    def add_server(self, name: str, host: str, user: str) -> int:
        """Add a server"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO servers (name, host, user)
                VALUES (?, ?, ?)
            """, (name, host, user))
            conn.commit()
            server_id = cursor.lastrowid
            conn.close()
            return server_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Server '{name}' already exists")
    
    def get_servers(self) -> List[Dict]:
        """Get all servers"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servers ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_server(self, server_id: int) -> Dict:
        """Get a specific server"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_server_status(self, server_id: int, status: str):
        """Update server status"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE servers 
            SET status = ?, last_checked = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, server_id))
        conn.commit()
        conn.close()
    
    # ===== SYSTEM LOGS =====
    def log_system_metric(self, server_id: int, metric: str, value: float):
        """Log a system metric"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_logs (server_id, metric, value)
            VALUES (?, ?, ?)
        """, (server_id, metric, value))
        conn.commit()
        conn.close()
    
    def get_system_logs(self, server_id: int, metric: str = None, 
                       limit=100) -> List[Dict]:
        """Get system logs"""
        conn = self._get_conn()
        cursor = conn.cursor()
        if metric:
            cursor.execute("""
                SELECT * FROM system_logs
                WHERE server_id = ? AND metric = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (server_id, metric, limit))
        else:
            cursor.execute("""
                SELECT * FROM system_logs
                WHERE server_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (server_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ===== SESSION LOGS =====
    def log_command(self, server_id: int, command: str, output: str = None, success: bool = True):
        """Log a command execution"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO session_logs (server_id, command, output, success)
            VALUES (?, ?, ?, ?)
        """, (server_id, command, output, 1 if success else 0))
        conn.commit()
        conn.close()
    
    def get_command_logs(self, server_id: int, limit=50) -> List[Dict]:
        """Get command logs"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM session_logs
            WHERE server_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (server_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
