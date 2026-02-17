"""Navigation controller — manages page history and transitions."""
from __future__ import annotations

from ._exceptions import PageNotFoundError
from ._models import PageModel


class NavigationController:
    """Manages multi-page navigation with a history stack.

    Args:
        pages: A mapping of page names to :class:`.models.PageModel`.

    Example::

        nav = NavigationController(pages)
        nav.set_start("home")
        nav.goto("settings")
        nav.go_back()
    """

    def __init__(self, pages: dict[str, PageModel]) -> None:
        self._pages = pages
        self._current: str | None = None
        self._history: list[str] = []

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_page(self) -> PageModel | None:
        """Return the currently active :class:`.models.PageModel`.

        Returns:
            The active page, or ``None`` if no start page has been set.
        """
        if self._current is None:
            return None
        return self._pages.get(self._current)

    @property
    def can_go_back(self) -> bool:
        """Whether there is a page to navigate back to.

        Returns:
            ``True`` if the history stack is non-empty.
        """
        return bool(self._history)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def set_start(self, page_name: str) -> None:
        """Set and activate the starting page.

        Args:
            page_name: Name of the page to start from.

        Returns:
            None

        Raises:
            PageNotFoundError: If *page_name* is not in the pages registry.
        """
        self._validate_page(page_name)
        self._current = page_name
        self._history.clear()

    def goto(self, page_name: str) -> None:
        """Navigate to *page_name*, pushing the current page onto history.

        Args:
            page_name: Name of the target page.

        Returns:
            None

        Raises:
            PageNotFoundError: If *page_name* does not exist.
        """
        self._validate_page(page_name)
        if self._current is not None:
            self._history.append(self._current)
        self._current = page_name

    def go_back(self) -> bool:
        """Pop the previous page from history and make it current.

        Returns:
            ``True`` if navigation succeeded; ``False`` if the stack was empty.
        """
        if not self._history:
            return False
        self._current = self._history.pop()
        return True

    def reset(self) -> None:
        """Clear history and return to the start page.

        Returns:
            None
        """
        start = self._history[0] if self._history else self._current
        self._history.clear()
        self._current = start

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_page(self, page_name: str) -> None:
        """Raise if *page_name* is not registered.

        Args:
            page_name: Page name to check.

        Returns:
            None

        Raises:
            PageNotFoundError: If the page is absent from the registry.
        """
        if page_name not in self._pages:
            raise PageNotFoundError(page_name)
