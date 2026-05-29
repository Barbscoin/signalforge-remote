"""
Export signals and system data to various formats
"""
import csv
import json
from pathlib import Path
from datetime import datetime
from database import Database


class Exporter:
    """Export database contents to various formats"""
    
    def __init__(self, db: Database, export_dir="exports"):
        self.db = db
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_signals_csv(self, filename: str = None, resolved_only: bool = False) -> str:
        """Export signals to CSV"""
        if filename is None:
            filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        signals = self.db.get_signals(limit=10000, resolved=resolved_only)
        
        if not signals:
            return None
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=signals[0].keys())
            writer.writeheader()
            writer.writerows(signals)
        
        return str(filepath)
    
    def export_signals_json(self, filename: str = None, resolved_only: bool = False) -> str:
        """Export signals to JSON"""
        if filename is None:
            filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.export_dir / filename
        signals = self.db.get_signals(limit=10000, resolved=resolved_only)
        
        with open(filepath, 'w') as f:
            json.dump(signals, f, indent=2, default=str)
        
        return str(filepath)
    
    def export_system_logs_csv(self, server_id: int, filename: str = None) -> str:
        """Export system logs to CSV"""
        if filename is None:
            server = self.db.get_server(server_id)
            name = server['name'] if server else f"server_{server_id}"
            filename = f"system_logs_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        logs = self.db.get_system_logs(server_id, limit=10000)
        
        if not logs:
            return None
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)
        
        return str(filepath)
    
    def export_command_logs_csv(self, server_id: int, filename: str = None) -> str:
        """Export command logs to CSV"""
        if filename is None:
            server = self.db.get_server(server_id)
            name = server['name'] if server else f"server_{server_id}"
            filename = f"command_logs_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_dir / filename
        logs = self.db.get_command_logs(server_id, limit=10000)
        
        if not logs:
            return None
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)
        
        return str(filepath)
