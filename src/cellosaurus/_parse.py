"""Parse Cellosaurus TXT file into a pandas DataFrame.

This module handles downloading, caching, and parsing the Cellosaurus
flat-file database from ExPASy into a structured DataFrame.

Notes
-----
- https://www.cellosaurus.org/
- https://ftp.expasy.org/databases/cellosaurus/
- https://github.com/calipho-sib/cellosaurus/

Line codes in cellosaurus.txt:

=========  ===========================  ======================
Line code  Content                      Occurrence in an entry
=========  ===========================  ======================
ID         Identifier (cell line name)  Once; starts an entry
AC         Accession (CVCL_xxxx)        Once
AS         Secondary accession          Optional; once
SY         Synonyms                     Optional; once
DR         Cross-references             Optional; once or more
RX         References identifiers       Optional; once or more
WW         Web pages                    Optional; once or more
CC         Comments                     Optional; once or more
ST         STR profile data             Optional; twice or more
DI         Diseases                     Optional; once or more
OX         Species of origin            Once or more
HI         Hierarchy                    Optional; once or more
OI         Same individual              Optional; once or more
SX         Sex of cell                  Optional; once
AG         Age at sampling              Optional; once
CA         Category                     Once
DT         Date (entry history)         Once
//         Terminator                   Once; ends an entry
=========  ===========================  ======================
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import pandas as pd

from cellosaurus._globals import (
    CELLOSAURUS_TXT_URL,
    COLUMN_RENAME_MAP,
    NESTED_KEYS,
)


def download_cellosaurus_txt(
    cache_dir: str | Path | None = None,
    *,
    update: bool = False,
) -> Path:
    """Download the Cellosaurus TXT file, with optional caching.

    Parameters
    ----------
    cache_dir : str or Path or None
        Directory to cache the downloaded file. If ``None``, downloads
        to a temporary location each time.
    update : bool
        Force re-download even if cached file exists.

    Returns
    -------
    Path
        Path to the downloaded file.
    """
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        dest = cache_dir / "cellosaurus.txt"
        if dest.exists() and not update:
            return dest
    else:
        import tempfile

        dest = Path(tempfile.mkdtemp()) / "cellosaurus.txt"
    print(f"Downloading Cellosaurus TXT from {CELLOSAURUS_TXT_URL}...")
    urllib.request.urlretrieve(CELLOSAURUS_TXT_URL, dest)
    return dest


def _process_entry(
    lines: list[str],
) -> dict[str, str | list[str] | None]:
    """Process lines for a single Cellosaurus entry.

    Parameters
    ----------
    lines : list[str]
        Raw text lines for one entry (ID through line before //).

    Returns
    -------
    dict
        Parsed entry with line-code keys.
    """
    parsed: dict[str, list[str]] = {}
    for line in lines:
        if len(line) < 5:
            continue
        key = line[:2].strip()
        value = line[5:]
        if key not in parsed:
            parsed[key] = []
        parsed[key].append(value)
    entry: dict[str, str | list[str] | None] = {}
    for key in ["AC", "CA", "ID", "SX", "AG"]:
        vals = parsed.get(key)
        if vals is not None and len(vals) > 0:
            entry[key] = vals[0]
        else:
            entry[key] = None
    # Multi-value optional keys (AS: secondary accessions, SY: synonyms).
    # Store as lists so no values are truncated.
    for key in ("AS", "SY"):
        vals = parsed.get(key)
        entry[key] = list(vals) if vals else []
    for key in NESTED_KEYS:
        vals = parsed.get(key)
        if vals is not None:
            seen: set[str] = set()
            unique: list[str] = []
            for v in vals:
                if v not in seen:
                    seen.add(v)
                    unique.append(v)
            entry[key] = unique
        else:
            entry[key] = []
    entry["DT"] = parsed.get("DT", [])
    cc_vals = entry.get("CC", [])
    if isinstance(cc_vals, list):
        discontinued = [c for c in cc_vals if isinstance(c, str) and c.startswith("Discontinued:")]
        if discontinued:
            disc_refs = set()
            for d in discontinued:
                m = re.match(r"^Discontinued: (.+);.+$", d)
                if m:
                    disc_refs.add(m.group(1))
            dr_vals = entry.get("DR", [])
            if isinstance(dr_vals, list):
                entry["DR"] = [dr for dr in dr_vals if dr not in disc_refs]
    return entry


def _extract_version(lines: list[str]) -> str:
    """Extract Cellosaurus release version from file header.

    Parameters
    ----------
    lines : list[str]
        First ~20 lines of the file.

    Returns
    -------
    str
        Version string.
    """
    for line in lines[:20]:
        if line.strip().startswith("Version:"):
            parts = line.strip().split(": ", maxsplit=1)
            return parts[1].strip()
    msg = "Failed to extract version from cellosaurus.txt header."
    raise RuntimeError(msg)


def _split_nested(
    values: list[str],
    sep: str,
) -> dict[str, list[str]]:
    """Split a list of 'key<sep>value' strings into a dict of lists.

    Parameters
    ----------
    values : list[str]
        Strings with embedded key-value pairs.
    sep : str
        Separator between key and value.

    Returns
    -------
    dict[str, list[str]]
        Grouped values by key.
    """
    result: dict[str, list[str]] = {}
    for v in values:
        parts = v.split(sep, maxsplit=1)
        if len(parts) == 2:
            k, val = parts
            k = k.strip()
            if k not in result:
                result[k] = []
            result[k].append(val.strip())
    return result


def parse_cellosaurus_txt(path: str | Path) -> pd.DataFrame:
    """Parse a Cellosaurus TXT file into a DataFrame.

    This performs only the initial parsing step: splitting entries,
    extracting line codes, and renaming columns. The resulting DataFrame
    contains nested list columns (``comments``, ``cross_references``,
    etc.) that are further processed by annotation functions.

    Parameters
    ----------
    path : str or Path
        Path to the ``cellosaurus.txt`` file.

    Returns
    -------
    pd.DataFrame
        Parsed DataFrame indexed by accession identifier, with columns
        renamed from line codes to descriptive snake_case names.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    version = _extract_version(lines)
    print(f"Detected Cellosaurus release {version}.")
    id_indices = [i for i, line in enumerate(lines) if line.startswith("ID   ")]
    term_indices = [i for i, line in enumerate(lines) if line == "//"]
    if len(id_indices) != len(term_indices):
        raise RuntimeError(
            f"Malformed Cellosaurus file: {len(id_indices)} ID lines but "
            f"{len(term_indices)} terminator ('//') lines."
        )
    print(f"Processing {len(id_indices)} entries...")
    entries = []
    for start, end in zip(id_indices, term_indices, strict=True):
        entry = _process_entry(lines[start:end])
        entries.append(entry)
    df = pd.DataFrame(entries)
    df = df.rename(columns=COLUMN_RENAME_MAP)
    if bool(df["accession"].isna().any()):
        raise RuntimeError("Parsed Cellosaurus data contains entries with missing accessions.")
    if not bool(df["accession"].str.startswith("CVCL_").all()):
        raise RuntimeError("Parsed Cellosaurus data contains accessions not starting with 'CVCL_'.")
    if bool(df["cell_line_name"].isna().any()):
        raise RuntimeError("Parsed Cellosaurus data contains entries with missing cell line names.")
    df = df.set_index("accession")
    df = df.sort_index()
    df.attrs["data_version"] = version
    df.attrs["package_version"] = _get_package_version()
    return df


def _get_package_version() -> str:
    """Get package version string."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("cellosaurus")
    except PackageNotFoundError:
        return "unknown"
