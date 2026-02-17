"""ASCIITerminalGUI — interactive terminal menus for Python 3.10+.

Public API:
    - TerminalMenu: main entry point for building and running menus.
    - EntryModel: model for a single menu entry.
    - PageModel: model for a menu page.
    - MenuTheme: theme/colour configuration.
    - Colors: convenience ANSI colour constants.

Exceptions:
    TerminalMenuError, PageNotFoundError, DuplicatePageError,
    EntryActionError, MenuConfigurationError, StartPageNotSetError.
"""

from ._exceptions import (
    DuplicatePageError,
    EntryActionError,
    MenuConfigurationError,
    PageNotFoundError,
    StartPageNotSetError,
    TerminalMenuError,
)
from ._menu import TerminalMenu
from ._models import EntryModel, MenuTheme, PageModel
from ._renderer import Styles as Colors  # Convenience colour constants

__all__ = [
    # Core
    "TerminalMenu",
    "EntryModel",
    "PageModel",
    "MenuTheme",
    "Colors",
    # Exceptions
    "TerminalMenuError",
    "PageNotFoundError",
    "DuplicatePageError",
    "EntryActionError",
    "MenuConfigurationError",
    "StartPageNotSetError",
]

__version__ = "2.1.0"
__author__ = "Cioscos"
