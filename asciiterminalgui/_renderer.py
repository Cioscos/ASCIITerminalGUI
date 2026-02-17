"""ANSI/ASCII renderer for the terminal menu UI — centred and flicker-free."""
from __future__ import annotations

import shutil
import sys

from ._models import MenuTheme, PageModel


class BoxChars:
    """Unicode box-drawing character constants."""
    TOP_LEFT     = "╔"
    TOP_RIGHT    = "╗"
    BOTTOM_LEFT  = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL   = "═"
    VERTICAL     = "║"
    T_DOWN       = "╦"
    T_UP         = "╩"
    T_RIGHT      = "╠"
    T_LEFT       = "╣"
    CROSS        = "╬"


class Styles:
    """ANSI text-style escape codes."""
    RESET = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"


class MenuRenderer:
    """Renders a :class:`.models.PageModel` to the terminal.

    The menu is always centred both horizontally and vertically within
    the current terminal window.  A single buffered write per frame is
    used to minimise flicker, and the *scrollback* buffer is cleared on
    every frame so previous menu states are never visible when scrolling
    upward.

    Args:
        theme: A :class:`.models.MenuTheme` instance controlling colours.

    Example::

        renderer = MenuRenderer(theme=MenuTheme())
        renderer.render(page)
    """

    # ANSI sequences
    _CLEAR_ALL    = "\033[3J"   # erase display **and** scrollback buffer
    _CURSOR_HOME  = "\033[H"    # move cursor to (1, 1)
    _HIDE_CURSOR  = "\033[?25l"
    _SHOW_CURSOR  = "\033[?25h"
    _MOVE_CURSOR  = "\033[{row};{col}H"  # template — formatted at runtime

    def __init__(self, theme: MenuTheme) -> None:
        self.theme = theme

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, page: PageModel) -> None:
        """Render *page* centred in the current terminal window.

        The scrollback buffer is erased on every call so no previous menu
        state is visible when the user scrolls upward.

        Args:
            page: The :class:`.models.PageModel` to render.

        Returns:
            None
        """
        self._full_clear()
        self._hide_cursor()

        term_w, term_h = self._terminal_size()
        content_w = min(term_w - 4, 70)
        content_h = min(term_h - 6, len(page.entries) + 8)

        frame_lines = self._build_frame(page, content_w, content_h)

        # Centre the frame: compute top-left origin.
        frame_h = len(frame_lines)
        frame_w = content_w + 4  # 2 border chars + 2 padding spaces each side

        start_row = max(1, (term_h - frame_h) // 2 + 1)
        start_col = max(1, (term_w - frame_w) // 2 + 1)

        buffer_parts: list[str] = []
        for idx, line in enumerate(frame_lines):
            row = start_row + idx
            col = start_col
            buffer_parts.append(f"\033[{row};{col}H{line}")

        sys.stdout.write("".join(buffer_parts))
        sys.stdout.flush()

    def restore_cursor(self) -> None:
        """Make the terminal cursor visible again.

        Returns:
            None
        """
        self._show_cursor()

    # ------------------------------------------------------------------
    # Frame construction
    # ------------------------------------------------------------------

    def _build_frame(
        self,
        page: PageModel,
        width: int,
        height: int,
    ) -> list[str]:
        """Compose the full menu frame as a list of ANSI-escaped strings.

        Each element represents one rendered terminal line (no newline
        characters are included — the caller positions the cursor).

        Args:
            page:   The page to render.
            width:  Inner content width in characters.
            height: Total frame height in lines.

        Returns:
            A list of strings, one per terminal line.
        """
        t = self.theme
        h_line = BoxChars.HORIZONTAL * (width + 2)
        lines: list[str] = []

        # Top border
        lines.append(
            f"{t.theme_color}{BoxChars.TOP_LEFT}{h_line}"
            f"{BoxChars.TOP_RIGHT}{Styles.RESET}"
        )

        # Title row
        title = page.title.center(width)
        lines.append(
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET} "
            f"{Styles.BOLD}{title}{Styles.RESET} "
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
        )

        # Divider
        lines.append(
            f"{t.theme_color}"
            f"{BoxChars.T_RIGHT}{h_line}{BoxChars.T_LEFT}"
            f"{Styles.RESET}"
        )

        # Entry rows
        for idx, entry in enumerate(page.entries):
            label = entry.label[: width].ljust(width)
            is_selected = idx == page.selected_index
            dim_prefix = Styles.DIM if not entry.enabled else ""

            if is_selected:
                row = (
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                    f"{t.selected_bg}{t.selected_fg} {label} {Styles.RESET}"
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                )
            else:
                row = (
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                    f" {dim_prefix}{label}{Styles.RESET} "
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                )
            lines.append(row)

        # Padding rows to reach desired height
        padding_rows = max(0, height - len(page.entries) - 5)
        empty_row = (
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
            f" {' ' * width} "
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
        )
        lines.extend([empty_row] * padding_rows)

        # Bottom border
        lines.append(
            f"{t.theme_color}"
            f"{BoxChars.BOTTOM_LEFT}{h_line}{BoxChars.BOTTOM_RIGHT}"
            f"{Styles.RESET}"
        )

        # Navigation hint (centred beneath the box)
        hint = "↑↓ Navigate  Enter Select  Esc Back"
        lines.append(f"{Styles.DIM}{hint.center(width + 4)}{Styles.RESET}")

        return lines

    # ------------------------------------------------------------------
    # Terminal helpers
    # ------------------------------------------------------------------

    def _terminal_size(self) -> tuple[int, int]:
        """Return (width, height) of the terminal, applying theme minimums.

        Returns:
            A tuple ``(width, height)`` both at least as large as the
            theme's ``min_width`` / ``min_height``.
        """
        size = shutil.get_terminal_size((80, 24))
        return (
            max(size.columns, self.theme.min_width),
            max(size.lines, self.theme.min_height),
        )

    @staticmethod
    def _full_clear() -> None:
        """Erase the terminal display and the scrollback buffer.

        Sequence order matters:
          1. ``\\033[?25l`` — hide cursor before any write (no flicker)
          2. ``\\033[3J``   — erase scrollback buffer (iTerm2, Windows Terminal)
          3. ``\\033[2J``   — erase visible display
          4. ``\\033[H``    — move cursor to (1,1)

        On non-TTY outputs (e.g. IDE consoles) falls back to the OS
        ``cls`` / ``clear`` system call.

        Returns:
            None
        """
        if sys.stdout.isatty():
            sys.stdout.write("\033[?25l\033[3J\033[2J\033[H")
            sys.stdout.flush()
        else:
            import os
            os.system("cls" if sys.platform == "win32" else "clear")

    @staticmethod
    def _hide_cursor() -> None:
        """Hide the terminal cursor to prevent flicker during rendering.

        Returns:
            None
        """
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def _show_cursor() -> None:
        """Restore the terminal cursor visibility.

        Returns:
            None
        """
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
