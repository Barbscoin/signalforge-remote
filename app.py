"""
SignalForge - Integrated Main Application
Monitors business crisis signals and manages remote servers
"""
import logging
import threading
import time
from pathlib import Path
from datetime import datetime

from config import config, Config
from database import Database
from secure_store import secure_store, SecureStore
from collector import collect_signals
from exporter import Exporter
from ssh_client import SSHClient
from system_monitor import get_stats
from session_manager import SessionManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signalforge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SignalForge:
    """Main application class"""
    
    def __init__(self):
        self.db = Database(config.get("db_path", "signalforge.db"))
        self.exporter = Exporter(self.db)
        self.session_manager = SessionManager()
        self.running = False
        self.stats_thread = None
        self.collect_thread = None
        
        logger.info("SignalForge initialized")
    
    # ===== SIGNAL MANAGEMENT =====
    
    def collect_signals_once(self):
        """Manually trigger signal collection"""
        logger.info("Starting signal collection...")
        threshold = config.get("score_threshold", 40)
        signals = collect_signals(self.db, threshold)
        logger.info(f"Collected {len(signals)} new signals")
        return signals
    
    def get_signals(self, limit=50, offset=0):
        """Get collected signals"""
        return self.db.get_signals(limit, offset, resolved=False)
    
    def mark_signal_resolved(self, signal_id):
        """Mark a signal as resolved"""
        self.db.mark_signal_resolved(signal_id)
        logger.info(f"Marked signal {signal_id} as resolved")
    
    # ===== SERVER MANAGEMENT =====
    
    def add_server(self, name, host, user, password=None):
        """Add a new server to manage"""
        try:
            server_id = self.db.add_server(name, host, user)
            if password:
                secure_store.store_credential(f"server_{server_id}", "password", password)
            logger.info(f"Added server: {name} ({host})")
            return server_id
        except ValueError as e:
            logger.error(f"Failed to add server: {e}")
            return None
    
    def get_servers(self):
        """Get all managed servers"""
        return self.db.get_servers()
    
    def connect_ssh(self, server_id):
        """Connect to a server via SSH"""
        server = self.db.get_server(server_id)
        if not server:
            logger.error(f"Server {server_id} not found")
            return False
        
        password = secure_store.get_credential(f"server_{server_id}", "password")
        if not password:
            logger.error(f"No password stored for server {server_id}")
            return False
        
        try:
            client = SSHClient(server['host'], server['user'], password)
            client.connect()
            session_key = f"server_{server_id}"
            self.session_manager.sessions[session_key] = client
            self.db.update_server_status(server_id, "connected")
            logger.info(f"Connected to server: {server['name']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            self.db.update_server_status(server_id, "connection_failed")
            return False
    
    def disconnect_ssh(self, server_id):
        """Disconnect from a server"""
        session_key = f"server_{server_id}"
        if session_key in self.session_manager.sessions:
            self.session_manager.disconnect(session_key)
            self.db.update_server_status(server_id, "offline")
            logger.info(f"Disconnected from server {server_id}")
    
    def run_command(self, server_id, command):
        """Run a command on a server"""
        session_key = f"server_{server_id}"
        try:
            output = self.session_manager.run_command(session_key, command)
            self.db.log_command(server_id, command, output, success=True)
            logger.info(f"Executed command on server {server_id}: {command}")
            return output
        except Exception as e:
            self.db.log_command(server_id, command, str(e), success=False)
            logger.error(f"Failed to run command on server {server_id}: {e}")
            return None
    
    # ===== SYSTEM MONITORING =====
    
    def get_local_stats(self):
        """Get local system stats"""
        return get_stats()
    
    def log_server_stats(self, server_id, cpu=None, ram=None, disk=None):
        """Log server metrics"""
        if cpu is not None:
            self.db.log_system_metric(server_id, "cpu", cpu)
        if ram is not None:
            self.db.log_system_metric(server_id, "ram", ram)
        if disk is not None:
            self.db.log_system_metric(server_id, "disk", disk)
    
    def get_server_stats(self, server_id, metric=None):
        """Get server metric history"""
        return self.db.get_system_logs(server_id, metric, limit=100)
    
    # ===== EXPORT =====
    
    def export_signals(self, format="csv", resolved_only=False):
        """Export signals"""
        if format == "csv":
            return self.exporter.export_signals_csv(resolved_only=resolved_only)
        elif format == "json":
            return self.exporter.export_signals_json(resolved_only=resolved_only)
        else:
            logger.error(f"Unknown export format: {format}")
            return None
    
    def export_server_logs(self, server_id, log_type="system"):
        """Export server logs"""
        if log_type == "system":
            return self.exporter.export_system_logs_csv(server_id)
        elif log_type == "command":
            return self.exporter.export_command_logs_csv(server_id)
        else:
            logger.error(f"Unknown log type: {log_type}")
            return None
    
    # ===== BACKGROUND TASKS =====
    
    def start_collection_loop(self, interval_seconds=3600):
        """Start background signal collection loop"""
        def loop():
            while self.running:
                try:
                    self.collect_signals_once()
                except Exception as e:
                    logger.error(f"Error in collection loop: {e}")
                time.sleep(interval_seconds)
        
        self.collect_thread = threading.Thread(target=loop, daemon=True)
        self.collect_thread.start()
        logger.info(f"Started collection loop (interval: {interval_seconds}s)")
    
    def start(self):
        """Start the application"""
        self.running = True
        refresh_interval = config.get("refresh_interval", 3600)
        self.start_collection_loop(refresh_interval)
        logger.info("SignalForge started")
    
    def stop(self):
        """Stop the application"""
        self.running = False
        if self.collect_thread:
            self.collect_thread.join(timeout=5)
        logger.info("SignalForge stopped")


# Global instance
app = SignalForge()


if __name__ == "__main__":
    import sys
    
    print("SignalForge - Business Crisis Monitoring & Server Management")
    print("=" * 60)
    
    app.start()
    
    try:
        while True:
            print("\n1. Collect signals now")
            print("2. View recent signals")
            print("3. Add server")
            print("4. Connect to server")
            print("5. Run command on server")
            print("6. Export signals")
            print("7. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                signals = app.collect_signals_once()
                print(f"Collected {len(signals)} signals")
                for sig in signals[:3]:
                    print(f"  [{sig['score']}] {sig['title'][:60]}")
            
            elif choice == "2":
                signals = app.get_signals(limit=5)
                print(f"\nRecent {len(signals)} signals:")
                for sig in signals:
                    print(f"  [{sig['score']}] {sig['title'][:60]}")
            
            elif choice == "3":
                name = input("Server name: ").strip()
                host = input("Host/IP: ").strip()
                user = input("Username: ").strip()
                password = input("Password: ").strip()
                server_id = app.add_server(name, host, user, password)
                if server_id:
                    print(f"Server added with ID: {server_id}")
            
            elif choice == "4":
                servers = app.get_servers()
                for srv in servers:
                    print(f"  [{srv['id']}] {srv['name']} ({srv['host']}) - {srv['status']}")
                server_id = int(input("Server ID: "))
                if app.connect_ssh(server_id):
                    print("Connected!")
            
            elif choice == "5":
                server_id = int(input("Server ID: "))
                command = input("Command: ").strip()
                output = app.run_command(server_id, command)
                if output:
                    print("\nOutput:")
                    print(output[:500])
            
            elif choice == "6":
                fmt = input("Format (csv/json): ").strip().lower()
                filepath = app.export_signals(format=fmt)
                if filepath:
                    print(f"Exported to: {filepath}")
            
            elif choice == "7":
                break
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        app.stop()
