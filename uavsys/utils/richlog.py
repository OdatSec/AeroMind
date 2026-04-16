from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
import datetime

# Custom theme for agents and events
custom_theme = Theme({
    "supervisor": "cyan",
    "agent 1": "green",
    "agent 2": "magenta",
    "system": "white dim",
    "tool": "yellow",
    "memory": "blue",
    "warning": "bold yellow",
    "error": "bold red"
})

console = Console(theme=custom_theme)

# Verbosity: 0=minimal, 1=normal, 2=debug
_verbosity = 1

def set_verbosity(level: int):
    global _verbosity
    _verbosity = level

class RichLog:
    @staticmethod
    def header(title: str):
        console.print()
        console.print(Panel(Text(title, justify="center", style="bold white"), style="blue"))
        console.print()

    @staticmethod
    def log(agent: str, message: str, style: str = None):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        if style:
            safe_style = style.lower()
            console.print(f"[{ts}] [{safe_style}]{agent}:[/] {message}")
        else:
            s = "white"
            if agent.lower() == "supervisor": s = "supervisor"
            elif "agent 1" in agent.lower(): s = "agent 1"
            elif "agent 2" in agent.lower(): s = "agent 2"
            console.print(f"[{ts}] [{s}]{agent}:[/] {message}")

    @staticmethod
    def tool_call(agent: str, tool_name: str, args: dict):
        """Only shown in debug mode."""
        if _verbosity < 2:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        console.print(f"[{ts}] [{agent}] 🛠️  [tool]{tool_name}[/] {args}")

    @staticmethod
    def memory_event(agent: str, event_type: str, details: str):
        """Memory events: show summary in normal mode, full details in debug."""
        if _verbosity == 0:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        if _verbosity == 1:
            # Compact: only show RETRIEVE_DONE with count, and WRITE with short text
            if event_type == "RETRIEVE_START":
                return  # Skip start events in normal mode
            if "WRITE" in event_type:
                # Shorten the details
                short = details[:80] + "..." if len(details) > 80 else details
                console.print(f"[{ts}] [memory]  💾 {agent} {event_type}[/]: {short}")
                return
            if event_type == "RETRIEVE_DONE":
                console.print(f"[{ts}] [memory]  🔍 {agent}[/]: {details}")
                return
        # Debug: show everything
        console.print(f"[{ts}] [{agent}] 🧠 [memory]{event_type}[/]: {details}")

    @staticmethod
    def error(agent: str, message: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        console.print(f"[{ts}] [{agent}] [error]ERROR:[/] {message}")
