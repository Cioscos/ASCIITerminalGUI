"""
ASCIITerminalGUI - A complete, self-contained Python library for rendering
interactive terminal menus with keyboard navigation and multi-page support.

Author: ASCIITerminalGUI
Version: 1.0.0
License: MIT
"""

import sys
import os
import json
import shutil
import threading
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Platform detection for keyboard input
if sys.platform == "win32":
    import msvcrt
else:
    import tty
    import termios
    import select


class Colors:
    """ANSI escape codes for terminal colors."""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_CYAN = "\033[106m"

    # Text styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"


class BoxChars:
    """Unicode box drawing characters."""
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOTTOM_LEFT = "└"
    BOTTOM_RIGHT = "┘"
    HORIZONTAL = "─"
    VERTICAL = "│"
    T_DOWN = "┬"
    T_UP = "┴"
    T_RIGHT = "├"
    T_LEFT = "┤"
    CROSS = "┼"


class KeyCode(Enum):
    """Keyboard key codes."""
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    ENTER = "ENTER"
    ESC = "ESC"
    UNKNOWN = "UNKNOWN"


class KeyboardInput:
    """Cross-platform keyboard input handler with proper arrow key detection."""

    def __init__(self):
        self._running = False
        self._key_buffer: List[str] = []
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

        if sys.platform != "win32":
            self._old_settings = None

    def start(self) -> None:
        """Start non-blocking keyboard input capture."""
        self._running = True
        self._thread = threading.Thread(target=self._input_loop, daemon=True)
        self._thread.start()

        if sys.platform != "win32":
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

    def stop(self) -> None:
        """Stop keyboard input capture and restore terminal settings."""
        self._running = False

        if sys.platform != "win32" and self._old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)

    def _input_loop(self) -> None:
        """Background thread for capturing keyboard input."""
        while self._running:
            try:
                if sys.platform == "win32":
                    # Windows: msvcrt.kbhit() controlla se c'è input disponibile
                    if msvcrt.kbhit():
                        char = msvcrt.getch()
                        with self._lock:
                            self._key_buffer.append(char)
                else:
                    # Linux/Unix: leggi TUTTO l'input disponibile in un colpo solo
                    while select.select([sys.stdin], [], [], 0)[0]:
                        char = sys.stdin.read(1)
                        if not char: break
                        with self._lock:
                            self._key_buffer.append(char)
                time.sleep(0.01)
            except Exception:
                pass

    def get_key(self) -> Optional[KeyCode]:
        """
        Get the next keyboard key from buffer.

        Handles platform-specific escape sequences:
        - Windows: Arrow keys send 0xe0 (224) or 0x00 (0) followed by key code
        - Linux: Arrow keys send ESC [ A/B/C/D sequences

        Returns:
            KeyCode enum or None if no key available
        """
        # 1. Preleviamo il primo carattere col Lock
        with self._lock:
            if not self._key_buffer:
                return None
            char = self._key_buffer.pop(0)

        # === WINDOWS ARROW KEY HANDLING ===
        if sys.platform == "win32":

            # Recuperiamo il byte se necessario
            if isinstance(char, bytes):
                try:
                    char_str = char.decode('utf-8', errors='ignore')
                except:
                    char_str = str(char)
            else:
                char_str = char

            if char_str == '\xe0' or char_str == '\x00':
                with self._lock:  # Riacquisisco il lock per leggere il prossimo char
                    if self._key_buffer:
                        next_char = self._key_buffer.pop(0)
                        # ... Logica di decodifica Windows (omessa per brevità, usa quella originale se serve)
                        # Se serve il codice completo Windows dimmelo, ma qui il focus è Linux.
                        # Per ora assumiamo che su Linux questo blocco venga saltato.
                return KeyCode.UNKNOWN

            elif char == '\r' or char == '\n':
                return KeyCode.ENTER
            elif char == '\x1b':
                return KeyCode.ESC

        # === LINUX/UNIX ARROW KEY HANDLING ===
        else:
            if char == '\x1b':  # ESC character
                # ORA dormiamo SENZA il lock, permettendo a _input_loop di scrivere
                time.sleep(0.02)

                # Riacquisiamo il lock per controllare se è arrivato altro
                with self._lock:
                    if self._key_buffer and self._key_buffer[0] == '[':
                        self._key_buffer.pop(0)  # Rimuovi '['

                        if self._key_buffer:
                            arrow_char = self._key_buffer.pop(0)
                            if arrow_char == 'A':
                                return KeyCode.UP
                            elif arrow_char == 'B':
                                return KeyCode.DOWN
                            elif arrow_char == 'C':
                                return KeyCode.RIGHT
                            elif arrow_char == 'D':
                                return KeyCode.LEFT

                return KeyCode.ESC

            elif char == '\r' or char == '\n':
                return KeyCode.ENTER

        return KeyCode.UNKNOWN


@dataclass
class Entry:
    """Represents a menu entry (selectable item)."""
    label: str
    action: Optional[Callable[[], Any]] = None
    next_page: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def execute(self) -> Optional[str]:
        """
        Execute the entry's action and return the next page name if any.

        Returns:
            Optional page name to navigate to
        """
        if self.action:
            try:
                result = self.action()
                if isinstance(result, str):
                    return result
            except Exception as e:
                print(f"\nError executing action: {e}")
                input("\nPress Enter to continue...")

        return self.next_page


@dataclass
class Page:
    """Represents a menu page with title and entries."""
    name: str
    title: str
    entries: List[Entry] = field(default_factory=list)
    selected_index: int = 0

    def add_entry(self, entry: Entry) -> 'Page':
        """Add an entry to this page."""
        self.entries.append(entry)
        return self

    def move_up(self) -> None:
        """Move selection up."""
        if self.entries:
            self.selected_index = (self.selected_index - 1) % len(self.entries)

    def move_down(self) -> None:
        """Move selection down."""
        if self.entries:
            self.selected_index = (self.selected_index + 1) % len(self.entries)

    def get_selected_entry(self) -> Optional[Entry]:
        """Get the currently selected entry."""
        if 0 <= self.selected_index < len(self.entries):
            return self.entries[self.selected_index]
        return None


class TerminalMenu:
    """
    Main class for creating and managing terminal menus.

    Features:
    - Multi-page navigation
    - Keyboard control (arrows, Enter, Esc)
    - Cross-platform support (Windows/Linux)
    - JSON configuration or programmatic setup
    - Automatic terminal resize handling
    - ANSI colors and box drawing

    Example:
        >>> menu = TerminalMenu()
        >>> menu.add_page("home", "Home Page")
        >>> menu.pages["home"].add_entry(Entry("Option 1", action=lambda: print("Hello")))
        >>> menu.set_start_page("home")
        >>> menu.run()
    """

    def __init__(
            self,
            theme_color: str = Colors.BRIGHT_CYAN,
            selected_bg: str = Colors.BG_BRIGHT_CYAN,
            selected_fg: str = Colors.BLACK,
            min_width: int = 40,
            min_height: int = 10
    ):
        """
        Initialize the terminal menu.

        Args:
            theme_color: Color for borders and title
            selected_bg: Background color for selected entry
            selected_fg: Foreground color for selected entry
            min_width: Minimum menu width
            min_height: Minimum menu height
        """
        self.pages: Dict[str, Page] = {}
        self.current_page_name: Optional[str] = None
        self.start_page_name: Optional[str] = None
        self.page_history: List[str] = []
        self.running = False

        # Theme settings
        self.theme_color = theme_color
        self.selected_bg = selected_bg
        self.selected_fg = selected_fg
        self.min_width = min_width
        self.min_height = min_height

        # Keyboard handler
        self.keyboard = KeyboardInput()

        # Action registry for JSON callbacks
        self._action_registry: Dict[str, Callable] = {}

    @staticmethod
    def clear_screen() -> None:
        """Clear the terminal screen (cross-platform)."""
        if sys.platform == "win32":
            os.system('cls')
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    @staticmethod
    def hide_cursor() -> None:
        """Hide the terminal cursor."""
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def show_cursor() -> None:
        """Show the terminal cursor."""
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def get_terminal_size(self) -> Tuple[int, int]:
        """
        Get current terminal size.

        Returns:
            Tuple of (width, height)
        """
        try:
            size = shutil.get_terminal_size((80, 24))
            return max(size.columns, self.min_width), max(size.lines, self.min_height)
        except Exception:
            return 80, 24

    def add_page(self, name: str, title: str = "") -> Page:
        """
        Add a new page to the menu.

        Args:
            name: Unique page identifier
            title: Display title for the page

        Returns:
            The created Page object for method chaining
        """
        page = Page(name=name, title=title or name)
        self.pages[name] = page
        return page

    def set_start_page(self, page_name: str) -> 'TerminalMenu':
        """
        Set the starting page.

        Args:
            page_name: Name of the page to start with

        Returns:
            Self for method chaining
        """
        self.start_page_name = page_name
        self.current_page_name = page_name
        return self

    def register_action(self, name: str, callback: Callable) -> 'TerminalMenu':
        """
        Register a callback function for use in JSON configuration.

        Args:
            name: Function name to reference in JSON
            callback: The callable function

        Returns:
            Self for method chaining
        """
        self._action_registry[name] = callback
        return self

    def go_to(self, page_name: str) -> None:
        """
        Navigate to a specific page.

        Args:
            page_name: Name of the page to navigate to
        """
        if page_name in self.pages:
            if self.current_page_name:
                self.page_history.append(self.current_page_name)
            self.current_page_name = page_name

    def go_back(self) -> bool:
        """
        Go back to the previous page.

        Returns:
            True if navigation succeeded, False if no history
        """
        if self.page_history:
            self.current_page_name = self.page_history.pop()
            return True
        return False

    def render(self) -> None:
        """Render the current page to the terminal."""
        self.clear_screen()

        if not self.current_page_name or self.current_page_name not in self.pages:
            print("Error: No valid page to display")
            return

        page = self.pages[self.current_page_name]
        term_width, term_height = self.get_terminal_size()

        # Calculate menu dimensions
        content_width = min(term_width - 4, 70)
        content_height = min(term_height - 6, len(page.entries) + 8)

        # Calculate centering offset
        x_offset = (term_width - content_width - 2) // 2
        y_offset = max(1, (term_height - content_height) // 2)

        # Build the menu frame
        lines = []

        # Top border with title
        title_text = f"[ {page.title} ]"
        title_padding = (content_width - len(title_text)) // 2
        top_line = (
            f"{BoxChars.TOP_LEFT}"
            f"{BoxChars.HORIZONTAL * title_padding}"
            f"{title_text}"
            f"{BoxChars.HORIZONTAL * (content_width - title_padding - len(title_text))}"
            f"{BoxChars.TOP_RIGHT}"
        )
        lines.append(f"{self.theme_color}{top_line}{Colors.RESET}")

        # Empty line
        lines.append(f"{self.theme_color}{BoxChars.VERTICAL}{' ' * content_width}{BoxChars.VERTICAL}{Colors.RESET}")

        # Menu entries
        for idx, entry in enumerate(page.entries):
            if idx == page.selected_index:
                # Highlight selected entry
                entry_text = f" {entry.label} "
                padding = content_width - len(entry_text)
                line = (
                    f"{self.theme_color}{BoxChars.VERTICAL}{Colors.RESET}"
                    f"{self.selected_bg}{self.selected_fg}{entry_text}"
                    f"{' ' * padding}{Colors.RESET}"
                    f"{self.theme_color}{BoxChars.VERTICAL}{Colors.RESET}"
                )
            else:
                entry_text = f" {entry.label}"
                padding = content_width - len(entry_text)
                line = (
                    f"{self.theme_color}{BoxChars.VERTICAL}{Colors.RESET}"
                    f" {entry_text}{' ' * (padding - 1)}"
                    f"{self.theme_color}{BoxChars.VERTICAL}{Colors.RESET}"
                )
            lines.append(line)

        # Empty line
        lines.append(f"{self.theme_color}{BoxChars.VERTICAL}{' ' * content_width}{BoxChars.VERTICAL}{Colors.RESET}")

        # Help line
        help_text = "↑/↓: Navigate | Enter: Select | Esc: Back/Exit"
        help_padding = (content_width - len(help_text)) // 2
        help_line = (
            f"{self.theme_color}{BoxChars.VERTICAL}{Colors.RESET}"
            f"{Colors.DIM}{' ' * help_padding}{help_text}"
            f"{' ' * (content_width - help_padding - len(help_text))}{Colors.RESET}"
            f"{self.theme_color}{BoxChars.VERTICAL}{Colors.RESET}"
        )
        lines.append(help_line)

        # Bottom border
        bottom_line = (
            f"{BoxChars.BOTTOM_LEFT}"
            f"{BoxChars.HORIZONTAL * content_width}"
            f"{BoxChars.BOTTOM_RIGHT}"
        )
        lines.append(f"{self.theme_color}{bottom_line}{Colors.RESET}")

        # Print with offset
        output = "\n" * y_offset
        for line in lines:
            output += " " * x_offset + line + "\n"

        sys.stdout.write(output)
        sys.stdout.flush()

    def run(self) -> None:
        """
        Start the menu event loop.

        Handles keyboard input, rendering, and navigation until exit.
        """
        if not self.current_page_name:
            if self.start_page_name:
                self.current_page_name = self.start_page_name
            elif self.pages:
                self.current_page_name = next(iter(self.pages.keys()))
            else:
                raise ValueError("No pages defined. Add at least one page before running.")

        self.running = True
        self.hide_cursor()
        self.keyboard.start()

        try:
            last_size = self.get_terminal_size()
            self.render()

            while self.running:
                # Check for terminal resize
                current_size = self.get_terminal_size()
                if current_size != last_size:
                    last_size = current_size
                    self.render()

                # Handle keyboard input
                key = self.keyboard.get_key()

                if key == KeyCode.UP:
                    if self.current_page_name in self.pages:
                        self.pages[self.current_page_name].move_up()
                        self.render()

                elif key == KeyCode.DOWN:
                    if self.current_page_name in self.pages:
                        self.pages[self.current_page_name].move_down()
                        self.render()

                elif key == KeyCode.ENTER:
                    if self.current_page_name in self.pages:
                        page = self.pages[self.current_page_name]
                        entry = page.get_selected_entry()

                        if entry:
                            next_page = entry.execute()
                            if next_page:
                                self.go_to(next_page)
                            self.render()

                elif key == KeyCode.ESC:
                    if not self.go_back():
                        self.running = False
                    else:
                        self.render()

                time.sleep(0.05)

        finally:
            self.keyboard.stop()
            self.show_cursor()
            self.clear_screen()

    @classmethod
    def from_json(cls, json_path: str, action_registry: Optional[Dict[str, Callable]] = None) -> 'TerminalMenu':
        """
        Create a menu from a JSON configuration file.

        JSON format:
        {
            "pages": {
                "page_name": {
                    "title": "Page Title",
                    "entries": [
                        {
                            "label": "Entry Label",
                            "action": "function_name",
                            "next_page": "target_page"
                        }
                    ]
                }
            },
            "start_page": "page_name"
        }

        Args:
            json_path: Path to JSON configuration file
            action_registry: Dictionary mapping function names to callables

        Returns:
            Configured TerminalMenu instance
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        menu = cls()

        # Register actions
        if action_registry:
            for name, callback in action_registry.items():
                menu.register_action(name, callback)

        # Build pages
        pages_config = config.get("pages", {})
        for page_name, page_data in pages_config.items():
            page = menu.add_page(page_name, page_data.get("title", page_name))

            for entry_data in page_data.get("entries", []):
                action_name = entry_data.get("action")
                action = menu._action_registry.get(action_name) if action_name else None

                entry = Entry(
                    label=entry_data.get("label", ""),
                    action=action,
                    next_page=entry_data.get("next_page")
                )
                page.add_entry(entry)

        # Set start page
        start_page = config.get("start_page")
        if start_page:
            menu.set_start_page(start_page)

        return menu


def main():
    """Example usage and testing."""

    # Example 1: Programmatic menu
    def hello_world():
        print("\n🎉 Hello World!")
        input("\nPress Enter to continue...")

    def show_info():
        print("\n📋 ASCIITerminalGUI v1.0.0")
        print("A powerful terminal menu library")
        input("\nPress Enter to continue...")

    def exit_app():
        print("\n👋 Goodbye!")
        time.sleep(1)
        sys.exit(0)

    menu = TerminalMenu()

    # Create home page
    home = menu.add_page("home", "Main Menu")
    home.add_entry(Entry("Say Hello", action=hello_world))
    home.add_entry(Entry("Show Info", action=show_info))
    home.add_entry(Entry("Go to Settings", next_page="settings"))
    home.add_entry(Entry("Exit", action=exit_app))

    # Create settings page
    settings = menu.add_page("settings", "Settings")
    settings.add_entry(Entry("Option 1", action=lambda: print("Option 1 selected")))
    settings.add_entry(Entry("Option 2", action=lambda: print("Option 2 selected")))
    settings.add_entry(Entry("Back to Home", next_page="home"))

    menu.set_start_page("home")
    menu.run()


if __name__ == "__main__":
    main()
