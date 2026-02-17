"""Custom exceptions for ASCIITerminalGUI."""


class TerminalMenuError(Exception):
    """Base exception for all ASCIITerminalGUI errors."""


class PageNotFoundError(TerminalMenuError):
    """Raised when a requested page does not exist in the menu.

    Args:
        page_name: The name of the page that was not found.
    """

    def __init__(self, page_name: str) -> None:
        self.page_name = page_name
        super().__init__(f"Page '{page_name}' not found in menu.")


class DuplicatePageError(TerminalMenuError):
    """Raised when attempting to add a page with an already-existing name.

    Args:
        page_name: The name of the duplicated page.
    """

    def __init__(self, page_name: str) -> None:
        self.page_name = page_name
        super().__init__(f"A page named '{page_name}' already exists.")


class EntryActionError(TerminalMenuError):
    """Raised when an entry's callback raises an unhandled exception.

    Args:
        label: The label of the entry that failed.
        cause: The original exception.
    """

    def __init__(self, label: str, cause: BaseException) -> None:
        self.label = label
        self.cause = cause
        super().__init__(f"Error executing action for entry '{label}': {cause}")


class MenuConfigurationError(TerminalMenuError):
    """Raised when the menu configuration (JSON or programmatic) is invalid."""


class StartPageNotSetError(TerminalMenuError):
    """Raised when run() is called before setting a start page."""
