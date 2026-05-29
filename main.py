"""
SignalForge - Interactive CLI for Business Crisis Monitoring & Server Management
"""
import sys
import json
from tabulate import tabulate

from app import SignalForge
from database import Database
from config import config

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

class SignalForgeCLI:
    def __init__(self):
        self.app = SignalForge()
        self.app.start()
    
    def display_signals(self, signals):
        """Display signals in table format"""
        if not signals:
            print_warning("No signals to display")
            return
        
        table_data = []
        for sig in signals:
            score = sig['score']
            title = sig['title'][:50] + "..." if len(sig['title']) > 50 else sig['title']
            keywords = sig['keywords'][:30] + "..." if len(sig['keywords']) > 30 else sig['keywords']
            table_data.append([score, title, keywords])
        
        headers = ["Score", "Title", "Keywords"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def display_servers(self, servers):
        """Display servers in table format"""
        if not servers:
            print_warning("No servers configured")
            return
        
        table_data = []
        for srv in servers:
            status_color = Colors.GREEN if srv['status'] == 'connected' else Colors.RED
            status = f"{status_color}{srv['status']}{Colors.END}"
            table_data.append([srv['id'], srv['name'], srv['host'], srv['user'], status])
        
        headers = ["ID", "Name", "Host", "User", "Status"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    def main_menu(self):
        """Display main menu"""
        while True:
            print_header("SignalForge - Main Menu")
            print(f"{Colors.BOLD}Signals & Monitoring:{Colors.END}")
            print("  1. Collect signals now")
            print("  2. View recent signals")
            print("  3. View signal details")
            print("  4. Mark signal resolved")
            print("  5. Export signals")
            
            print(f"\n{Colors.BOLD}Server Management:{Colors.END}")
            print("  6. List configured servers")
            print("  7. Add new server")
            print("  8. Connect to server")
            print("  9. Run command on server")
            print("  10. View server logs")
            
            print(f"\n{Colors.BOLD}System:{Colors.END}")
            print("  11. View local system stats")
            print("  12. View system logs")
            print("  0. Exit")
            
            choice = input(f"\n{Colors.BOLD}Select option (0-12): {Colors.END}").strip()
            
            if choice == "0":
                self.exit_app()
            elif choice == "1":
                self.collect_signals()
            elif choice == "2":
                self.view_signals()
            elif choice == "3":
                self.signal_details()
            elif choice == "4":
                self.mark_resolved()
            elif choice == "5":
                self.export_signals()
            elif choice == "6":
                self.list_servers()
            elif choice == "7":
                self.add_server()
            elif choice == "8":
                self.connect_server()
            elif choice == "9":
                self.run_command()
            elif choice == "10":
                self.view_server_logs()
            elif choice == "11":
                self.view_local_stats()
            elif choice == "12":
                self.view_system_logs()
            else:
                print_error("Invalid option")
    
    def collect_signals(self):
        """Manually collect signals"""
        print_header("Collecting Signals")
        print("Fetching from RSS feeds...")
        signals = self.app.collect_signals_once()
        print_success(f"Collected {len(signals)} new signals")
        if signals:
            self.display_signals(signals[:5])
    
    def view_signals(self):
        """View recent signals"""
        print_header("Recent Signals")
        limit = int(input("How many signals to display? (default: 10): ") or "10")
        signals = self.app.get_signals(limit=limit)
        self.display_signals(signals)
    
    def signal_details(self):
        """View details of a specific signal"""
        print_header("Signal Details")
        signal_id = int(input("Enter signal ID: "))
        db = Database(config.get("db_path", "signalforge.db"))
        conn = db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        sig = cursor.fetchone()
        conn.close()
        
        if sig:
            sig = dict(sig)
            print(f"\n{Colors.BOLD}Title:{Colors.END} {sig['title']}")
            print(f"{Colors.BOLD}Score:{Colors.END} {sig['score']}")
            print(f"{Colors.BOLD}Keywords:{Colors.END} {sig['keywords']}")
            print(f"{Colors.BOLD}Source:{Colors.END} {sig['source']}")
            print(f"{Colors.BOLD}Published:{Colors.END} {sig['published']}")
            print(f"{Colors.BOLD}Link:{Colors.END} {sig['link']}")
            print(f"\n{Colors.BOLD}Summary:{Colors.END}")
            print(sig['summary'][:500] if sig['summary'] else "No summary")
        else:
            print_error("Signal not found")
    
    def mark_resolved(self):
        """Mark a signal as resolved"""
        print_header("Mark Signal Resolved")
        signal_id = int(input("Enter signal ID: "))
        self.app.mark_signal_resolved(signal_id)
        print_success(f"Signal {signal_id} marked as resolved")
    
    def export_signals(self):
        """Export signals to file"""
        print_header("Export Signals")
        fmt = input("Format (csv/json) [csv]: ").strip().lower() or "csv"
        filepath = self.app.export_signals(format=fmt)
        if filepath:
            print_success(f"Exported to: {filepath}")
        else:
            print_error("Export failed")
    
    def list_servers(self):
        """List configured servers"""
        print_header("Configured Servers")
        servers = self.app.get_servers()
        self.display_servers(servers)
    
    def add_server(self):
        """Add a new server"""
        print_header("Add New Server")
        name = input("Server name: ").strip()
        host = input("Host/IP address: ").strip()
        user = input("SSH username: ").strip()
        password = input("SSH password: ").strip()
        
        server_id = self.app.add_server(name, host, user, password)
        if server_id:
            print_success(f"Server added with ID: {server_id}")
        else:
            print_error("Failed to add server")
    
    def connect_server(self):
        """Connect to a server"""
        print_header("Connect to Server")
        servers = self.app.get_servers()
        self.display_servers(servers)
        server_id = int(input("\nEnter server ID: "))
        
        if self.app.connect_ssh(server_id):
            print_success("Connected successfully")
        else:
            print_error("Connection failed")
    
    def run_command(self):
        """Run a command on a server"""
        print_header("Run Command on Server")
        servers = self.app.get_servers()
        self.display_servers(servers)
        server_id = int(input("\nEnter server ID: "))
        command = input("Command to run: ").strip()
        
        output = self.app.run_command(server_id, command)
        if output:
            print(f"\n{Colors.BOLD}Output:{Colors.END}")
            print(output[:1000])
            if len(output) > 1000:
                print(f"\n[Output truncated, full output has {len(output)} characters]")
        else:
            print_error("Command execution failed")
    
    def view_server_logs(self):
        """View server command logs"""
        print_header("Server Command Logs")
        servers = self.app.get_servers()
        self.display_servers(servers)
        server_id = int(input("\nEnter server ID: "))
        
        db = Database(config.get("db_path", "signalforge.db"))
        logs = db.get_command_logs(server_id, limit=10)
        
        if logs:
            for log in logs:
                print(f"\n{Colors.BOLD}[{log['timestamp']}]{Colors.END} {log['command']}")
                print(f"Status: {Colors.GREEN if log['success'] else Colors.RED}{'Success' if log['success'] else 'Failed'}{Colors.END}")
        else:
            print_warning("No logs found")
    
    def view_local_stats(self):
        """View local system stats"""
        print_header("Local System Statistics")
        stats = self.app.get_local_stats()
        print(f"CPU Usage:  {stats['cpu']}%")
        print(f"RAM Usage:  {stats['ram']}%")
        print(f"Disk Usage: {stats['disk']}%")
    
    def view_system_logs(self):
        """View system metric logs"""
        print_header("System Metric Logs")
        servers = self.app.get_servers()
        self.display_servers(servers)
        server_id = int(input("\nEnter server ID: "))
        
        db = Database(config.get("db_path", "signalforge.db"))
        logs = db.get_system_logs(server_id, limit=20)
        
        if logs:
            print(f"\n{Colors.BOLD}Recent metrics:{Colors.END}")
            for log in logs[:10]:
                print(f"  {log['metric'].upper():5} {log['value']:6.2f}% at {log['timestamp']}")
        else:
            print_warning("No logs found")
    
    def exit_app(self):
        """Exit the application"""
        print(f"\n{Colors.CYAN}Shutting down SignalForge...{Colors.END}")
        self.app.stop()
        sys.exit(0)


if __name__ == "__main__":
    try:
        cli = SignalForgeCLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)