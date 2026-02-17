"""Pydantic V2 models for ASCIITerminalGUI data structures."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from ._exceptions import EntryActionError


class EntryModel(BaseModel):
    """Represents a single selectable entry in a menu page.

    Attributes:
        label:     The text displayed for this entry.
        action:    Optional callable invoked when the entry is selected.
        next_page: Optional name of the page to navigate to after selection.
        enabled:   Whether the entry can be selected.
        metadata:  Arbitrary extra data attached to the entry.
    """

    model_config = {"arbitrary_types_allowed": True}

    label: str = Field(..., min_length=1, description="Display text for the entry.")
    action: Callable[..., Any] | None = Field(
        default=None, description="Callback invoked on selection."
    )
    next_page: str | None = Field(
        default=None, description="Page name to navigate to after execution."
    )
    enabled: bool = Field(default=True, description="Whether the entry is selectable.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("label")
    @classmethod
    def label_must_not_be_blank(cls, value: str) -> str:
        """Ensure *label* is not just whitespace.

        Args:
            value: The raw label string.

        Returns:
            The stripped label.

        Raises:
            ValueError: If the label is blank after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("Entry label must not be blank.")
        return stripped

    def execute(self) -> str | None:
        """Execute the entry's action and return the next page name, if any.

        Returns:
            The next page name to navigate to, or ``None``.

        Raises:
            EntryActionError: If the action callback raises an exception.
        """
        if self.action is not None:
            try:
                result = self.action()
                if isinstance(result, str):
                    return result
            except Exception as exc:
                raise EntryActionError(label=self.label, cause=exc) from exc
        return self.next_page


class PageModel(BaseModel):
    """Represents a menu page composed of multiple entries.

    Attributes:
        name:           Unique identifier for this page.
        title:          Display title shown in the menu header.
        entries:        Ordered list of selectable entries.
        selected_index: Index of the currently highlighted entry.
    """

    name: str = Field(..., min_length=1)
    title: str = Field(default="")
    entries: list[EntryModel] = Field(default_factory=list)
    selected_index: int = Field(default=0)

    @model_validator(mode="after")
    def title_defaults_to_name(self) -> PageModel:
        """Fall back to *name* if *title* is empty.

        Returns:
            The validated ``PageModel`` instance.
        """
        if not self.title:
            self.title = self.name
        return self

    def add_entry(self, entry: EntryModel) -> PageModel:
        """Append *entry* to this page.

        Args:
            entry: The :class:`EntryModel` to add.

        Returns:
            Self, for method chaining.
        """
        self.entries.append(entry)
        return self

    @property
    def active_entries(self) -> list[EntryModel]:
        """Return only enabled entries.

        Returns:
            Filtered list of enabled :class:`EntryModel` objects.
        """
        return [e for e in self.entries if e.enabled]

    def move_up(self) -> None:
        """Move the selection index up, wrapping around.

        Returns:
            None
        """
        if self.entries:
            self.selected_index = (self.selected_index - 1) % len(self.entries)

    def move_down(self) -> None:
        """Move the selection index down, wrapping around.

        Returns:
            None
        """
        if self.entries:
            self.selected_index = (self.selected_index + 1) % len(self.entries)

    @property
    def selected_entry(self) -> EntryModel | None:
        """Return the currently selected entry.

        Returns:
            The selected :class:`EntryModel`, or ``None`` if no entries exist.
        """
        if 0 <= self.selected_index < len(self.entries):
            return self.entries[self.selected_index]
        return None


class MenuTheme(BaseModel):
    """Visual theme configuration for the terminal menu.

    Attributes:
        theme_color:  ANSI color code for borders and title.
        selected_bg:  ANSI background code for the selected item.
        selected_fg:  ANSI foreground code for selected item text.
        min_width:    Minimum menu width in characters.
        min_height:   Minimum menu height in lines.
    """

    theme_color: str = Field(default="\033[96m")
    selected_bg: str = Field(default="\033[106m")
    selected_fg: str = Field(default="\033[30m")
    min_width: int = Field(default=40, ge=20)
    min_height: int = Field(default=10, ge=5)
