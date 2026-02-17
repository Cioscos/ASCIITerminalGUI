"""Cross-platform non-blocking keyboard input handler."""
from __future__ import annotations

import collections
import sys
import threading
import time
from enum import Enum, auto


class KeyCode(Enum):
    """Enumeration of recognisable keyboard inputs."""
    UP     = auto()
    DOWN   = auto()
    LEFT   = auto()
    RIGHT  = auto()
    ENTER  = auto()
    ESC    = auto()
    CTRL_C = auto()
    UNKNOWN = auto()


def _decode_byte(raw: bytes | int | str) -> str:
    """Normalise a raw keyboard byte to a single character string.

    Args:
        raw: A byte, integer, or string from the input buffer.

    Returns:
        A single decoded character string.
    """
    if isinstance(raw, bytes):
        return raw.decode("latin-1", errors="ignore")
    if isinstance(raw, int):
        try:
            return chr(raw)
        except ValueError:
            return ""
    return str(raw)


class KeyboardInput:
    """Cross-platform, non-blocking keyboard input reader.

    Uses ``msvcrt`` on Windows and ``select``/``termios`` on POSIX systems.
    Keystrokes are pushed into a thread-safe :class:`collections.deque` and
    consumed via :meth:`get_key`.

    Example::

        kb = KeyboardInput()
        kb.start()
        key = kb.get_key()   # returns KeyCode or None
        kb.stop()
    """

    ESC_TIMEOUT: float = 0.03  # seconds to wait for escape-sequence completion

    def __init__(self) -> None:
        self._running: bool = False
        self._key_buffer: collections.deque[str] = collections.deque()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._old_settings: list | None = None  # POSIX only

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background input-capture thread.

        On POSIX systems the terminal is put in *cbreak* mode so individual
        keystrokes are available without pressing Enter.

        Returns:
            None
        """
        self._running = True
        if sys.platform != "win32":
            import termios
            import tty
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        self._thread = threading.Thread(target=self._input_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop input capture and restore terminal settings.

        Returns:
            None
        """
        self._running = False
        if sys.platform != "win32" and self._old_settings is not None:
            import termios
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)

    # ------------------------------------------------------------------
    # Key consumption
    # ------------------------------------------------------------------

    def get_key(self) -> KeyCode | None:
        """Consume the next key from the buffer and return its :class:`KeyCode`.

        Returns:
            A :class:`KeyCode` value, or ``None`` if the buffer is empty.
        """
        with self._lock:
            if not self._key_buffer:
                return None
            char = self._key_buffer.popleft()

        if sys.platform == "win32":
            return self._parse_windows_key(char)
        return self._parse_posix_key(char)

    # ------------------------------------------------------------------
    # Background input loops
    # ------------------------------------------------------------------

    def _input_loop(self) -> None:
        """Background thread: read raw bytes and push them to the buffer.

        Returns:
            None

        Raises:
            No exceptions are raised; errors are silently ignored to keep
            the background thread alive.
        """
        if sys.platform == "win32":
            self._windows_loop()
        else:
            self._posix_loop()

    def _windows_loop(self) -> None:
        """Input loop for Windows using ``msvcrt``.

        Returns:
            None
        """
        import msvcrt
        while self._running:
            if msvcrt.kbhit():
                raw = msvcrt.getch()
                decoded = _decode_byte(raw)
                with self._lock:
                    self._key_buffer.append(decoded)
            else:
                time.sleep(0.01)

    def _posix_loop(self) -> None:
        """Input loop for POSIX systems using ``select``.

        Returns:
            None
        """
        import os
        import select

        fd = sys.stdin.fileno()
        while self._running:
            try:
                readable, _, _ = select.select([fd], [], [], 0.05)
                if readable:
                    data = os.read(fd, 64)
                    decoded = data.decode("latin-1", errors="ignore")
                    with self._lock:
                        self._key_buffer.extend(decoded)
            except Exception:  # noqa: BLE001 — keep thread alive
                time.sleep(0.01)

    # ------------------------------------------------------------------
    # Key parsers
    # ------------------------------------------------------------------

    def _parse_windows_key(self, char: str) -> KeyCode:
        """Parse a Windows virtual key code.

        Args:
            char: First character already dequeued from the buffer.

        Returns:
            The matching :class:`KeyCode`.
        """
        if char in ("\x00", "\xe0"):
            return self._read_windows_extended()
        if char in ("\r", "\n"):
            return KeyCode.ENTER
        if char == "\x1b":
            return KeyCode.ESC
        if char == "\x03":
            return KeyCode.CTRL_C
        return KeyCode.UNKNOWN

    def _read_windows_extended(self) -> KeyCode:
        """Read the second byte of a Windows extended key sequence.

        Returns:
            The matching :class:`KeyCode`.
        """
        _WINDOWS_MAP: dict[str, KeyCode] = {
            "H": KeyCode.UP,
            "P": KeyCode.DOWN,
            "M": KeyCode.RIGHT,
            "K": KeyCode.LEFT,
        }
        deadline = time.monotonic() + self.ESC_TIMEOUT
        while time.monotonic() < deadline:
            with self._lock:
                if self._key_buffer:
                    second = self._key_buffer.popleft()
                    return _WINDOWS_MAP.get(second, KeyCode.UNKNOWN)
            time.sleep(0.001)
        return KeyCode.UNKNOWN

    def _parse_posix_key(self, char: str) -> KeyCode:
        """Parse a POSIX key, handling multi-byte ESC sequences.

        Args:
            char: First character already dequeued from the buffer.

        Returns:
            The matching :class:`KeyCode`.
        """
        if char in ("\r", "\n"):
            return KeyCode.ENTER
        if char == "\x03":
            return KeyCode.CTRL_C
        if char != "\x1b":
            return KeyCode.UNKNOWN

        # Attempt to read the rest of the escape sequence.
        prefix, arrow = self._drain_escape_sequence()
        if prefix in ("[", "O") and arrow is not None:
            _POSIX_MAP: dict[str, KeyCode] = {
                "A": KeyCode.UP,
                "B": KeyCode.DOWN,
                "C": KeyCode.RIGHT,
                "D": KeyCode.LEFT,
            }
            return _POSIX_MAP.get(arrow, KeyCode.UNKNOWN)
        return KeyCode.ESC

    def _drain_escape_sequence(self) -> tuple[str | None, str | None]:
        """Wait briefly for the remainder of a CSI/SS3 escape sequence.

        Returns:
            A tuple ``(prefix, arrow_char)`` where *prefix* is ``[`` or
            ``O``, and *arrow_char* is the final letter.  Both are ``None``
            if the timeout expires without a complete sequence.
        """
        deadline = time.monotonic() + self.ESC_TIMEOUT
        prefix: str | None = None
        arrow: str | None = None
        while time.monotonic() < deadline:
            with self._lock:
                if len(self._key_buffer) >= 2 and self._key_buffer[0] in ("[", "O"):
                    prefix = self._key_buffer.popleft()
                    arrow = self._key_buffer.popleft()
                    return prefix, arrow
            time.sleep(0.001)
        return prefix, arrow
