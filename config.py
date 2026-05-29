import json
import os
from pathlib import Path


class Config:
    """Configuration management for SignalForge"""
    
    DEFAULT_CONFIG = {
        "servers": [],
        "rss_feeds": [
            "https://news.google.com/rss/search?q=small+business+website+hacked",
            "https://news.google.com/rss/search?q=business+email+compromised",
            "https://news.google.com/rss/search?q=restaurant+website+down",
            "https://news.google.com/rss/search?q=wordpress+hacked+small+business",
            "https://news.google.com/rss/search?q=dns+issue+business",
        ],
        "score_threshold": 40,
        "refresh_interval": 3600,
        "db_path": "signalforge.db"
    }
    
    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)
        self.data = self.load()
    
    def load(self):
        """Load config from file, or create default if missing"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save config to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key, default=None):
        """Get config value"""
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Set config value"""
        self.data[key] = value
        self.save()
    
    def add_server(self, name, host, user, password=None):
        """Add a server to config"""
        if "servers" not in self.data:
            self.data["servers"] = []
        self.data["servers"].append({
            "name": name,
            "host": host,
            "user": user,
            "password": password
        })
        self.save()
    
    def get_servers(self):
        """Get all configured servers"""
        return self.data.get("servers", [])


# Global instance
config = Config()
