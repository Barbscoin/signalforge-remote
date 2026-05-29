"""
SignalForge - Advanced Textual TUI
Full-featured terminal user interface with real-time monitoring
"""
from textual.app import App, ComposeResult, on
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Label, Input, Select, DataTable, TextArea
)
from textual.binding import Binding
from textual.reactive import reactive
from datetime import datetime
import asyncio
from app import SignalForge
from config import config
from database import Database


class StatsPanel(Static):
    """Real-time system statistics display"""
    
    cpu = reactive(0)
    ram = reactive(0)
    disk = reactive(0)
    
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.border_title = "📊 System Stats"
    
    def render(self) -> str:
        stats = self.app_instance.get_local_stats()
        self.cpu = stats['cpu']
        self.ram = stats['ram']
        self.disk = stats['disk']
        
        cpu_bar = self._make_bar(self.cpu)
        ram_bar = self._make_bar(self.ram)
        disk_bar = self._make_bar(self.disk)
        
        return f"""
[bold cyan]Local System Metrics[/]

CPU:  {cpu_bar} {self.cpu:5.1f}%
RAM:  {ram_bar} {self.ram:5.1f}%
Disk: {disk_bar} {self.disk:5.1f}%

[dim]Updates: Real-time[/]
"""
    
    def _make_bar(self, value: float, width: int = 20) -> str:
        """Create a text-based progress bar"""
        filled = int((value / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        color = "[green]" if value < 50 else "[yellow]" if value < 80 else "[red]"
        return f"{color}{bar}[/]"


class SignalListPanel(Static):
    """Display collected signals"""
    
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.border_title = "🚨 Signals"
        self.signals = []
        self.selected_index = 0
    
    def on_mount(self):
        self.set_interval(5, self.refresh_signals)
        self.refresh_signals()
    
    def refresh_signals(self):
        self.signals = self.app_instance.get_signals(limit=10)
        self.refresh()
    
    def render(self) -> str:
        if not self.signals:
            return "[dim]No signals collected yet. Use 'Collect' to fetch from RSS feeds.[/dim]"
        
        lines = []
        for i, sig in enumerate(self.signals):
            prefix = "❯ " if i == self.selected_index else "  "
            score_color = "[green]" if sig['score'] < 50 else "[yellow]" if sig['score'] < 70 else "[red]"
            title = sig['title'][:50] + "..." if len(sig['title']) > 50 else sig['title']
            lines.append(f"{prefix}{score_color}[{sig['score']:3d}][/] {title}")
        
        return "\n".join(lines) + f"\n[dim]Total: {len(self.signals)} signals[/dim]"


class ServerListPanel(Static):
    """Display configured servers"""
    
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.border_title = "🖥️  Servers"
        self.servers = []
    
    def on_mount(self):
        self.refresh_servers()
    
    def refresh_servers(self):
        self.servers = self.app_instance.get_servers()
        self.refresh()
    
    def render(self) -> str:
        if not self.servers:
            return "[dim]No servers configured. Use 'Add Server' button.[/dim]"
        
        lines = []
        for srv in self.servers:
            status_icon = "✓" if srv['status'] == 'connected' else "✗"
            status_color = "[green]" if srv['status'] == 'connected' else "[red]"
            lines.append(
                f"  {status_icon} {status_color}{srv['name']:20}[/] {srv['host']:15} ({srv['user']})"
            )
        
        return "\n".join(lines) + f"\n[dim]Total: {len(self.servers)} servers[/dim]"


class SignalDetailModal(Static):
    """Modal to show detailed signal information"""
    
    def __init__(self, signal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signal = signal
        self.border_title = "Signal Details"
    
    def render(self) -> str:
        return f"""[bold cyan]{self.signal['title']}[/]

[bold]Score:[/] {self.signal['score']}
[bold]Keywords:[/] {self.signal['keywords']}
[bold]Source:[/] {self.signal['source']}
[bold]Published:[/] {self.signal['published']}
[bold]Link:[/] {self.signal['link']}

[bold]Summary:[/]
{self.signal['summary'][:300] if self.signal['summary'] else 'N/A'}...
"""


class ControlPanel(Static):
    """Control buttons and commands"""
    
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.border_title = "⌘ Controls"
    
    def compose(self) -> ComposeResult:
        yield Button("📥 Collect Now", id="btn_collect", variant="primary")
        yield Button("➕ Add Server", id="btn_add_server", variant="success")
        yield Button("🔌 Connect", id="btn_connect", variant="warning")
        yield Button("📤 Export", id="btn_export", variant="secondary")
        yield Button("🔄 Refresh", id="btn_refresh")
        yield Button("ℹ️  Details", id="btn_details")


class SignalForgeUI(App):
    """Main Textual Application"""
    
    TITLE = "SignalForge"
    SUB_TITLE = "Business Crisis Monitoring & Server Management"
    
    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }
    
    #panels {
        height: 1fr;
        layout: horizontal;
    }
    
    #left_panel {
        width: 35%;
        border: solid $primary;
        background: $panel;
    }
    
    #middle_panel {
        width: 35%;
        border: solid $primary;
        background: $panel;
    }
    
    #right_panel {
        width: 30%;
        border: solid $primary;
        background: $panel;
    }
    
    #control_panel {
        height: auto;
        border: solid $accent;
        background: $boost;
    }
    
    Button {
        margin: 0 1;
    }
    
    StatsPanel {
        border: solid $success;
        padding: 1;
    }
    
    SignalListPanel {
        border: solid $warning;
        padding: 1;
        overflow: auto;
    }
    
    ServerListPanel {
        border: solid $accent;
        padding: 1;
        overflow: auto;
    }
    
    Static {
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("c", "collect", "Collect", show=True),
        Binding("s", "add_server", "Server", show=True),
        Binding("e", "export", "Export", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = SignalForge()
        self.app.start()
        self.selected_signal = None
        self.selected_server = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app"""
        yield Header()
        
        with Horizontal(id="panels"):
            # Left Panel - Signals
            with Vertical(id="left_panel"):
                yield Label("[bold cyan]Recent Signals[/bold cyan]")
                yield SignalListPanel(self.app)
            
            # Middle Panel - Servers
            with Vertical(id="middle_panel"):
                yield Label("[bold cyan]Managed Servers[/bold cyan]")
                yield ServerListPanel(self.app)
            
            # Right Panel - Stats
            with Vertical(id="right_panel"):
                yield StatsPanel(self.app)
        
        # Control Panel
        yield ControlPanel(self.app)
        yield Footer()
    
    def on_mount(self) -> None:
        """Application startup"""
        self.title = "SignalForge - Business Crisis Monitor"
        self.set_interval(2, self.update_display)
    
    def update_display(self) -> None:
        """Update display panels"""
        for widget in self.query("StatsPanel"):
            widget.refresh()
        for widget in self.query("SignalListPanel"):
            widget.refresh_signals()
        for widget in self.query("ServerListPanel"):
            widget.refresh_servers()
    
    def action_collect(self) -> None:
        """Collect signals from RSS feeds"""
        self.notify("🔄 Collecting signals...", title="Status", timeout=2)
        signals = self.app.collect_signals_once()
        self.notify(f"✓ Collected {len(signals)} signals", title="Success", timeout=3)
        self.update_display()
    
    def action_add_server(self) -> None:
        """Add a new server"""
        self.notify("Add server: Use CLI or main.py for full input", timeout=3)
    
    def action_export(self) -> None:
        """Export data"""
        csv = self.app.export_signals(format="csv")
        json_file = self.app.export_signals(format="json")
        self.notify(f"✓ Exported to:\nCSV: {csv}\nJSON: {json_file}", timeout=4)
    
    def action_refresh(self) -> None:
        """Refresh all panels"""
        self.update_display()
        self.notify("✓ Refreshed", timeout=1)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "btn_collect":
            self.action_collect()
        elif button_id == "btn_export":
            self.action_export()
        elif button_id == "btn_refresh":
            self.action_refresh()
        elif button_id == "btn_add_server":
            self.notify("Switch to main.py CLI for full server management", timeout=3)
        elif button_id == "btn_connect":
            self.notify("Switch to main.py CLI to connect to server", timeout=3)
        elif button_id == "btn_details":
            self.notify("Select signal with ↑↓, press Enter for details", timeout=3)
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.app.stop()
        self.exit()


if __name__ == "__main__":
    app = SignalForgeUI()
    app.run()
