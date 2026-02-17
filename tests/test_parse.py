"""Tests for cellosaurus._parse."""

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from cellosaurus._parse import (
    _extract_version,
    _process_entry,
    _split_nested,
    parse_cellosaurus_txt,
)


def test_split_nested() -> None:
    """Test splitting nested delimited values."""
    values = ["ATCC; CRL-1234", "ATCC; CRL-5678", "DepMap; ACH-000001"]
    result = _split_nested(values, "; ")
    assert result == {
        "ATCC": ["CRL-1234", "CRL-5678"],
        "DepMap": ["ACH-000001"],
    }


def test_split_nested_empty() -> None:
    """Test splitting empty list returns empty dict."""
    assert _split_nested([], "; ") == {}


def test_extract_version() -> None:
    """Test extracting version from header lines."""
    lines = [
        "________",
        " Cellosaurus",
        " Version: 49.0",
        "________",
    ]
    assert _extract_version(lines) == "49.0"


def test_extract_version_missing() -> None:
    """Test extracting version raises when missing."""
    with pytest.raises(RuntimeError):
        _extract_version(["no version here"])


def test_process_entry_basic() -> None:
    """Test processing a basic cell line entry."""
    lines = [
        "ID   Test Cell",
        "AC   CVCL_0001",
        "SY   TestSyn1; TestSyn2",
        "CA   Cancer cell line",
        "SX   Female",
        "AG   30Y",
        "DT   Created: 04-04-12; Last updated: 05-10-23; Version: 30",
        "OX   NCBI_TaxID=9606; ! Homo sapiens",
    ]
    entry = _process_entry(lines)
    assert entry["ID"] == "Test Cell"
    assert entry["AC"] == "CVCL_0001"
    assert entry["SY"] == "TestSyn1; TestSyn2"
    assert entry["CA"] == "Cancer cell line"
    assert entry["SX"] == "Female"
    assert entry["AG"] == "30Y"
    assert isinstance(entry["OX"], list)
    assert len(entry["OX"]) == 1


def test_process_entry_nested_keys_default_empty() -> None:
    """Test that nested keys default to empty lists."""
    lines = [
        "ID   Minimal",
        "AC   CVCL_0002",
        "CA   Hybridoma",
        "DT   Created: 04-04-12; Last updated: 05-10-23; Version: 1",
    ]
    entry = _process_entry(lines)
    assert entry["CC"] == []
    assert entry["DR"] == []
    assert entry["HI"] == []


def test_parse_cellosaurus_txt(tmp_path: Path) -> None:
    """Test full parsing with a minimal fake cellosaurus.txt."""
    content = textwrap.dedent("""\
        _____
         Cellosaurus
         Version: 99.0
        _____
        ID   Alpha
        AC   CVCL_0001
        SY   AlphaSyn
        CA   Cancer cell line
        SX   Male
        AG   45Y
        DT   Created: 01-01-20; Last updated: 01-01-23; Version: 5
        OX   NCBI_TaxID=9606; ! Homo sapiens
        //
        ID   Beta
        AC   CVCL_0002
        CA   Hybridoma
        SX   Female
        AG   Age unspecified
        DT   Created: 02-02-20; Last updated: 02-02-23; Version: 3
        OX   NCBI_TaxID=10090; ! Mus musculus
        //
    """)
    txt_file = tmp_path / "cellosaurus.txt"
    txt_file.write_text(content)
    df = parse_cellosaurus_txt(txt_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.index.name == "accession"
    assert "CVCL_0001" in df.index
    assert "CVCL_0002" in df.index
    assert df.loc["CVCL_0001", "cell_line_name"] == "Alpha"
    assert df.attrs["data_version"] == "99.0"
