# Input Latency Bottlenecks Analysis

This file documents the identified latency bottlenecks in the current input handling implementation and provides platform‑specific optimization steps.

## 1. Identified Bottlenecks

| Location | Current Behaviour | Likely Impact | Reason |
|----------|------------------|--------------|--------|
| `TerminalMenu.run` (line 628) | `time.sleep(0.05)` after each key handling | ~50 ms round‑trip delay between key press and UI update | Polling loop sleeps, preventing immediate response |
| `_input_loop` (line 136, 138) | `time.sleep(0.01)` per iteration | ~10 ms latency before a key is queued, especially on Linux when multiple keys are pressed | Sleeping in the background thread unnecessarily delays reading |
| Linux input read | `select([fd], [], [], 0.01)` | 10 ms polling window | Same as above; could be tighter |
| Windows key buffer handling | `self._key_buffer.append(char)` and lock acquisition | Lock contention minimal but list append/ pop can be slower than deque | For high‑frequency key streams, a deque offers O(1) pop from left |
| Escape sequence parsing | `time.sleep(0.001)` inside sequence detection | Small delay when parsing multi‑byte sequences | Could be removed or replaced with a non‑blocking check |

## 2. Platform‑Specific Optimization Steps

### Windows (`sys.platform == "win32"`)
1. **Remove unnecessary sleep** in `_input_loop`. The `msvcrt.kbhit()` call is already non‑blocking. Replace `time.sleep(0.01)` with a very short sleep or no sleep if CPU usage is acceptable.
2. Use `collections.deque` for `self._key_buffer` to improve pop/append performance and reduce lock contention.
3. Consider using `msvcrt.getch()` in a loop without sleeping to immediately capture keys, then push them into the deque.

### Linux / Unix (`else` block)
1. **Tighten polling timeout**: Change `select([fd], [], [], 0.01)` to `select([fd], [], [], 0.001)` or use a non‑blocking read by setting the file descriptor to non‑blocking mode with `fcntl`. This reduces the 10 ms polling window.
2. **Eliminate the `time.sleep(0.01)`**: After a key is read, the thread can immediately loop to the next poll, only sleeping if no data was read to avoid busy‑waiting.
3. Replace the `list` buffer with a `deque` for efficient pop‑left operations.
4. For escape sequence detection, replace the 1 ms `time.sleep(0.001)` with a simple non‑blocking check of the buffer size. If the buffer has at least two characters, process the sequence immediately.

## 3. Validation Checklist

- [ ] Replace list with `deque` for `self._key_buffer` on both platforms.
- [ ] Remove or reduce `time.sleep` calls in `_input_loop` and in the main event loop.
- [ ] Tighten `select` timeout to 1 ms or use non‑blocking read.
- [ ] Verify that the UI still renders correctly and that key handling remains responsive.
- [ ] Run benchmarks (e.g., press keys in rapid succession) to confirm latency drop to < 10 ms.

**Note:** Implement these changes incrementally and run regression tests to ensure no side effects.

---

**Prepared by**: Claude Code
