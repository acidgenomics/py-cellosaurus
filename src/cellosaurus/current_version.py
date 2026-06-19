"""Get current Cellosaurus release version."""

import re
import urllib.request

from cellosaurus._globals import CELLOSAURUS_RELNOTES_URL

# Matches e.g. "Cellosaurus version 46" or "Cellosaurus version 46.0"
_VERSION_RE = re.compile(r"Cellosaurus version\s+(\S+)", re.IGNORECASE)


def current_cellosaurus_version() -> str:
    """Get the current Cellosaurus release version.

    Queries the server at ``ftp.expasy.org``.

    Returns
    -------
    str
        Release version string.

    Examples
    --------
    >>> ver = current_cellosaurus_version()
    >>> isinstance(ver, str)
    True
    """
    with urllib.request.urlopen(CELLOSAURUS_RELNOTES_URL) as response:
        text = response.read().decode("utf-8")
    for line in text.splitlines():
        m = _VERSION_RE.search(line)
        if m:
            return m.group(1)
    msg = "Failed to parse Cellosaurus version from release notes."
    raise RuntimeError(msg)
