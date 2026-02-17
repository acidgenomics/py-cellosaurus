"""Get current Cellosaurus release version."""

from __future__ import annotations

import urllib.request

from cellosaurus._globals import CELLOSAURUS_RELNOTES_URL


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
    lines = text.splitlines()
    for line in lines:
        if "This is the release notes for Cellosaurus version" in line:
            parts = line.strip().split()
            version = parts[8]
            return version
    msg = "Failed to parse Cellosaurus version from release notes."
    raise RuntimeError(msg)
