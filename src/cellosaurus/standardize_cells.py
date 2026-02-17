"""Standardize cell line names."""

from __future__ import annotations

import re


def standardize_cells(cells: list[str] | str) -> list[str] | str:
    """Standardize cell line names.

    Strip all non-alphanumeric characters, remove information in parentheses
    or brackets, and convert to uppercase.

    Note that this function doesn't attempt to perform any mapping to the
    Cellosaurus database. For that, refer to ``Cellosaurus.map_cells`` instead.

    Parameters
    ----------
    cells : str or list of str
        Cell line names to standardize.

    Returns
    -------
    str or list of str
        Standardized cell line names.

    Examples
    --------
    >>> standardize_cells(["22Rv1", "Jurkat", "Ramos (RA-1)"])
    ['22RV1', 'JURKAT', 'RAMOS']
    """
    scalar = isinstance(cells, str)
    if scalar:
        cells = [cells]
    out = []
    for cell in cells:
        s = cell.lower()
        # Handle "SUM-52PE, SUM52" to "SUM-52PE" edge case.
        s = re.sub(r",\s.+$", "", s)
        # Remove parenthesized/bracketed suffixes.
        s = re.sub(r"\s[\[\(].+$", "", s)
        # Remove all non-alphanumeric characters.
        s = re.sub(r"[^a-z0-9]+", "", s)
        if s == "":
            s = "invalid"
        # Insert underscores at boundaries between letters and digits
        # (mimics R's snakeCase without smart option).
        s = re.sub(r"([a-z])(\d)", r"\1_\2", s)
        s = re.sub(r"(\d)([a-z])", r"\1_\2", s)
        s = s.upper()
        out.append(s)
    if scalar:
        return out[0]
    return out
