"""TerminalMenu — the public-facing façade for ASCIITerminalGUI."""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._exceptions import (
    DuplicatePageError,
    EntryActionError,
    MenuConfigurationError,
    PageNotFoundError,
    StartPageNotSetError,
)
from ._input import KeyCode, KeyboardInput
from ._models import EntryModel, MenuTheme, PageModel
from ._navigation import NavigationController
from ._renderer import MenuRenderer


class TerminalMenu:
    """High-level façade for building and running an interactive terminal menu.

    Supports programmatic construction and JSON-based configuration.
    The menu is always rendered centred in the terminal window, and the
    scrollback buffer is cleared on every frame so previous menu states
    are never revealed when scrolling upward.

    Args:
        theme_color:  ANSI color code for borders and title text.
        selected_bg:  ANSI background for the highlighted entry.
        selected_fg:  ANSI foreground for the highlighted entry.
        min_width:    Minimum menu width in characters.
        min_height:   Minimum menu height in lines.

    Example::

        menu = TerminalMenu()
        home = menu.add_page("home", "Main Menu")
        home.add_entry(EntryModel(label="Greet", action=lambda: print("Hello")))
        home.add_entry(EntryModel(label="Exit", action=sys.exit))
        menu.set_start_page("home")
        menu.run()
    """

    def __init__(
        self,
        theme_color: str = "\033[96m",
        selected_bg: str = "\033[106m",
        selected_fg: str = "\033[30m",
        min_width: int = 40,
        min_height: int = 10,
    ) -> None:
        theme = MenuTheme(
            theme_color=theme_color,
            selected_bg=selected_bg,
            selected_fg=selected_fg,
            min_width=min_width,
            min_height=min_height,
        )
        self._pages: dict[str, PageModel] = {}
        self._nav = NavigationController(self._pages)
        self._renderer = MenuRenderer(theme)
        self._keyboard = KeyboardInput()
        self._action_registry: dict[str, Callable[..., Any]] = {}

    # ------------------------------------------------------------------
    # Page & action management
    # ------------------------------------------------------------------

    def add_page(self, name: str, title: str = "") -> PageModel:
        """Create and register a new menu page.

        Args:
            name:  Unique page identifier.
            title: Display title (defaults to *name* if blank).

        Returns:
            The newly created :class:`.models.PageModel`.

        Raises:
            DuplicatePageError: If a page with *name* already exists.
        """
        if name in self._pages:
            raise DuplicatePageError(name)
        page = PageModel(name=name, title=title or name)
        self._pages[name] = page
        return page

    def set_start_page(self, page_name: str) -> TerminalMenu:
        """Designate the initial page shown when :meth:`run` is called.

        Args:
            page_name: Name of the start page.

        Returns:
            Self, for method chaining.

        Raises:
            PageNotFoundError: If *page_name* has not been added.
        """
        self._nav.set_start(page_name)
        return self

    def register_action(
        self, name: str, callback: Callable[..., Any]
    ) -> TerminalMenu:
        """Register a named callable for use in JSON-based configuration.

        Args:
            name:     Key used to reference this action in JSON.
            callback: The callable to invoke.

        Returns:
            Self, for method chaining.
        """
        self._action_registry[name] = callback
        return self

    # ------------------------------------------------------------------
    # JSON factory
    # ------------------------------------------------------------------

    @classmethod
    def from_json(
        cls,
        path: str | Path,
        action_registry: dict[str, Callable[..., Any]] | None = None,
        **menu_kwargs: Any,
    ) -> TerminalMenu:
        """Construct a :class:`TerminalMenu` from a JSON configuration file.

        The JSON format is::

            {
              "pages": {
                "<page_id>": {
                  "title": "Display Title",
                  "entries": [
                    {"label": "...", "action": "<key>", "next_page": null}
                  ]
                }
              },
              "start_page": "<page_id>"
            }

        Args:
            path:            Path to the JSON configuration file.
            action_registry: Mapping of action-name strings to callables.
            **menu_kwargs:   Forwarded to :class:`TerminalMenu.__init__`.

        Returns:
            A fully configured :class:`TerminalMenu` instance.

        Raises:
            FileNotFoundError:     If *path* does not exist.
            MenuConfigurationError: If the JSON is malformed or missing
                                    required fields.
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            raw = config_path.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MenuConfigurationError(f"Invalid JSON in {path}: {exc}") from exc

        registry = action_registry or {}
        menu = cls(**menu_kwargs)

        pages_data: dict[str, Any] = data.get("pages", {})
        if not pages_data:
            raise MenuConfigurationError(
                "JSON config must contain a non-empty 'pages' key."
            )

        for page_id, page_data in pages_data.items():
            if not isinstance(page_data, dict):
                raise MenuConfigurationError(
                    f"Page '{page_id}' must be a JSON object."
                )
            page = menu.add_page(page_id, page_data.get("title", page_id))

            for raw_entry in page_data.get("entries", []):
                action_key: str | None = raw_entry.get("action")
                action_fn: Callable[..., Any] | None = (
                    registry.get(action_key) if action_key else None
                )
                if action_key and action_fn is None:
                    raise MenuConfigurationError(
                        f"Action '{action_key}' referenced in page '{page_id}' "
                        f"is not in the action registry."
                    )
                entry = EntryModel(
                    label=raw_entry.get("label", ""),
                    action=action_fn,
                    next_page=raw_entry.get("next_page"),
                )
                page.add_entry(entry)

        start_page: str | None = data.get("start_page")
        if not start_page:
            raise MenuConfigurationError(
                "JSON config must specify a 'start_page'."
            )
        menu.set_start_page(start_page)
        return menu

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the interactive menu loop.

        Blocks until the user exits (Ctrl-C or Esc on the root page).

        Returns:
            None

        Raises:
            StartPageNotSetError: If :meth:`set_start_page` was never called.
        """
        if self._nav.current_page is None:
            raise StartPageNotSetError("Call set_start_page() before run().")

        self._keyboard.start()
        try:
            self._event_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self._keyboard.stop()
            self._renderer.restore_cursor()

    # ------------------------------------------------------------------
    # Internal event loop
    # ------------------------------------------------------------------

    def _event_loop(self) -> None:
        """Core rendering and input-dispatch loop.

        Returns:
            None
        """
        while True:
            page = self._nav.current_page
            if page is None:
                break
            self._renderer.render(page)
            key = self._wait_for_key()
            match key:
                case KeyCode.UP:
                    page.move_up()
                case KeyCode.DOWN:
                    page.move_down()
                case KeyCode.ENTER:
                    self._handle_selection(page)
                case KeyCode.ESC | KeyCode.CTRL_C:
                    if not self._nav.go_back():
                        break
                case _:
                    pass  # ignore unrecognised keys

    def _wait_for_key(self) -> KeyCode:
        """Poll the keyboard until a recognised key is available.

        Returns:
            The next :class:`.input.KeyCode` from the user.
        """
        while True:
            key = self._keyboard.get_key()
            if key is not None:
                return key
            time.sleep(0.01)

    def _handle_selection(self, page: PageModel) -> None:
        """Execute the selected entry's action and navigate if required.

        Args:
            page: The currently displayed page.

        Returns:
            None
        """
        entry = page.selected_entry
        if entry is None or not entry.enabled:
            return

        try:
            next_page = entry.execute()
        except EntryActionError as exc:
            self._renderer.restore_cursor()
            print(f"\n Error in '{exc.label}': {exc.cause}")
            input("Press Enter to continue…")
            return

        if next_page:
            try:
                self._nav.goto(next_page)
            except PageNotFoundError as exc:
                self._renderer.restore_cursor()
                print(f"\n Navigation error: {exc}")
                input("Press Enter to continue…")
