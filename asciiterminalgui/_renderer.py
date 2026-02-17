"""ANSI/ASCII renderer for the terminal menu UI."""

from __future__ import annotations

import shutil
import sys

from ._models import MenuTheme, PageModel


class BoxChars:
    """Unicode box-drawing character constants."""

    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL = "═"
    VERTICAL = "║"
    T_DOWN = "╦"
    T_UP = "╩"
    T_RIGHT = "╠"
    T_LEFT = "╣"
    CROSS = "╬"


class Styles:
    """ANSI text style escape codes."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


class MenuRenderer:
    """Renders a :class:`~._models.PageModel` to the terminal.

    All I/O is directed to ``sys.stdout`` via a single buffered write per
    frame to minimise flicker.

    Args:
        theme: A :class:`~._models.MenuTheme` instance controlling colours.

    Example:
        renderer = MenuRenderer(theme=MenuTheme())
        renderer.render(page)
    """

    def __init__(self, theme: MenuTheme) -> None:
        self._theme = theme

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, page: PageModel) -> None:
        """Render *page* to the terminal.

        Args:
            page: The :class:`~._models.PageModel` to render.

        Returns:
            None
        """
        self._clear_screen()
        self._hide_cursor()
        term_w, term_h = self._terminal_size()
        content_w = min(term_w - 4, 70)
        content_h = min(term_h - 6, len(page.entries) + 8)

        frame = self._build_frame(page, content_w, content_h)
        sys.stdout.write(frame)
        sys.stdout.flush()

    def restore_cursor(self) -> None:
        """Make the terminal cursor visible again.

        Returns:
            None
        """
        self._show_cursor()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _terminal_size(self) -> tuple[int, int]:
        """Return ``(width, height)`` of the terminal, applying minimums.

        Returns:
            A tuple of ``(width, height)`` both at least as large as the
            theme's ``min_width`` / ``min_height``.
        """
        size = shutil.get_terminal_size((80, 24))
        return (
            max(size.columns, self._theme.min_width),
            max(size.lines, self._theme.min_height),
        )

    def _build_frame(self, page: PageModel, width: int, height: int) -> str:
        """Compose the full menu frame as a single string.

        Args:
            page: The page to render.
            width: Inner content width in characters.
            height: Total frame height in lines.

        Returns:
            The complete ANSI-escaped string representing one menu frame.
        """
        t = self._theme
        h_line = BoxChars.HORIZONTAL * (width + 2)
        lines: list[str] = []

        # ── Top border ──────────────────────────────────────────────
        lines.append(
            f"{t.theme_color}{BoxChars.TOP_LEFT}{h_line}{BoxChars.TOP_RIGHT}{Styles.RESET}"
        )

        # ── Title ────────────────────────────────────────────────────
        title = page.title.center(width)
        lines.append(
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
            f" {Styles.BOLD}{title}{Styles.RESET} "
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
        )

        # ── Divider ──────────────────────────────────────────────────
        lines.append(
            f"{t.theme_color}"
            f"{BoxChars.T_RIGHT}{h_line}{BoxChars.T_LEFT}"
            f"{Styles.RESET}"
        )

        # ── Entries ──────────────────────────────────────────────────
        for idx, entry in enumerate(page.entries):
            label = entry.label[:width].ljust(width)
            is_selected = idx == page.selected_index

            if is_selected:
                row = (
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                    f"{t.selected_bg}{t.selected_fg} ▶ {label} {Styles.RESET}"
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                )
            else:
                dim = Styles.DIM if not entry.enabled else ""
                row = (
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                    f"{dim}   {label} {Styles.RESET}"
                    f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
                )
            lines.append(row)

        # ── Padding ──────────────────────────────────────────────────
        rendered_entries = len(page.entries)
        padding_rows = max(0, height - rendered_entries - 5)
        empty_row = (
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
            f"{' ' * (width + 2)}"
            f"{t.theme_color}{BoxChars.VERTICAL}{Styles.RESET}"
        )
        lines.extend([empty_row] * padding_rows)

        # ── Bottom border ────────────────────────────────────────────
        lines.append(
            f"{t.theme_color}"
            f"{BoxChars.BOTTOM_LEFT}{h_line}{BoxChars.BOTTOM_RIGHT}"
            f"{Styles.RESET}"
        )

        # ── Footer hint ──────────────────────────────────────────────
        hint = "↑↓ Navigate   Enter Select   Esc Back"
        lines.append(f"{Styles.DIM}{hint.center(width + 4)}{Styles.RESET}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _clear_screen() -> None:
        """Clear the terminal screen using ANSI escape codes.

        Returns:
            None
        """
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    @staticmethod
    def _hide_cursor() -> None:
        """Hide the terminal cursor.

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
