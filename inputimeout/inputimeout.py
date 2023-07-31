"""# Usage example:

```python
try:
    userInput = inputimeout(prompt='>>', timeout=5.0)
except TimeoutError as e:
    userInput = ''

print(userInput)
```
"""

import sys
from typing import Optional


DEFAULT_TIMEOUT = 30.0
"""Default timeout used when not passed by the caller [s]"""

WIN_INTERVAL = 0.05
"""Windows only: checking interval [s]"""

SP = " "
"""Space character."""

CR = "\r"
"""Carriage Return character."""

LF = "\n"
"""Line Feed character."""

CRLF = CR + LF
"""Carriage Return followed by Line Feed."""


def _echo(s: str) -> None:
    """Uses standard output stream to print `s`.

    Args:
    * `s` (str): String to be printed out.
    """
    sys.stdout.write(s)
    sys.stdout.flush()


def _posix_inputimeout(
    prompt: str = "", timeout: Optional[float] = DEFAULT_TIMEOUT
) -> str:
    """Linux version - can wait for user input for the specified amount of time.

    **NOTE:** See example call.

    Args:
    * `prompt` (str, optional): Text to be printed encouraging user input. Defaults to empty string.
    * `timeout` (Optional[float], optional): If it is
        * positive numerical value, time in seconds that the function will wait for the user input (interaction). If input is not registered within that time budget `TimeoutError` is raised.
        * `None` the function will block forever until user input is registered. Defaults to DEFAULT_TIMEOUT = 30 [s].

    Raises:
    * `TimeoutError`: If wait time exceeds `timeout` (possible only if `timeout is not None`)
    * `OSError`: If there is an OS-based error eg. `Too many open files`

    Returns:
    `str`: Characters entered by the user.
    """

    def cleanup(sel: selectors.DefaultSelector) -> None:
        """Safety measure in Linux environment. Ensures that file associated with that
        selector will be closed and resource will be freed.

        Args:
        * `sel` (selectors.DefaultSelector): Selector object to release.
        """
        sel.unregister(sys.stdin)
        sel.close()

    _echo(prompt)

    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)
    events = sel.select(timeout)

    if events:
        key, _ = events[0]
        data = key.fileobj.readline().rstrip(LF)

        cleanup(sel)  # FIX: Critical!

        return data

    else:
        _echo(LF)
        termios.tcflush(sys.stdin, termios.TCIFLUSH)

        cleanup(sel)  # FIX: Critical!

        raise TimeoutError


def _win_inputimeout(prompt: str = "", timeout: float = DEFAULT_TIMEOUT) -> str:
    """Windows version - can wait for user input for the specified amount of time.

    **NOTE:** See example call.

    Args:
    * `prompt` (str, optional): Text to be printed encouraging user input. Defaults to empty string.
    * `timeout` (Optional[float], optional): If it is
        * positive numerical value, time in seconds that the function will wait for the user input (interaction). If input is not registered within that time budget `TimeoutError` is raised.
        * `None` the function will block forever until user input is registered. Defaults to DEFAULT_TIMEOUT = 30 [s].

    Raises:
    * `TimeoutError`: If wait time exceeds `timeout` (possible only if `timeout is not None`)

    Returns:
    `str`: Characters entered by the user.
    """
    _echo(prompt)
    begin = time.monotonic()
    end = begin + timeout
    line = ""

    while time.monotonic() < end:
        if msvcrt.kbhit():
            c = msvcrt.getwche()
            if c in (CR, LF):
                _echo(CRLF)
                return line
            
            if c == "\003":
                raise KeyboardInterrupt
            
            if c == "\b":
                line = line[:-1]
                cover = SP * len(prompt + line + SP)
                _echo("".join([CR, cover, CR, prompt, line]))

            else:
                line += c
                
        time.sleep(WIN_INTERVAL)

    _echo(CRLF)
    raise TimeoutError


try:
    import msvcrt
    import time

    inputimeout = _win_inputimeout

except ImportError:
    import selectors
    import termios

    inputimeout = _posix_inputimeout
