"""Tests for cellosaurus.cellosaurus (Cellosaurus class)."""

from pathlib import Path

import pandas as pd
import pytest

from cellosaurus.cellosaurus import Cellosaurus


@pytest.fixture
def mock_df() -> pd.DataFrame:
    """Create a mock annotated Cellosaurus DataFrame."""
    data = {
        "cell_line_name": ["Alpha", "Beta", "Gamma"],
        "category": [
            "Cancer cell line",
            "Cancer cell line",
            "Hybridoma",
        ],
        "is_cancer": [True, True, False],
        "is_contaminated": [False, True, False],
        "is_problematic": [False, True, False],
        "ncbi_taxonomy_id": [[9606], [9606], [10090]],
        "organism": [["Homo sapiens"], ["Homo sapiens"], ["Mus musculus"]],
        "sex_of_cell": ["Female", "Male", "Female"],
        "comments": [
            {"Sequence variation": []},
            {"Problematic cell line": ["Contaminated"]},
            {},
        ],
        "cross_references": [
            {"ATCC": ["CRL-1234"], "DepMap": ["ACH-000001"]},
            {"ATCC": ["CRL-5678"]},
            {},
        ],
        "atcc_id": ["CRL-1234", "CRL-5678", None],
        "depmap_id": ["ACH-000001", None, None],
        "sanger_model_id": [None, None, None],
        "synonyms": [["AlphaSyn"], [], []],
        "misspellings": [[], [], []],
        "secondary_accession": [[], [], []],
        "ncit_disease_id": [["C12345"], ["C67890"], []],
        "ncit_disease_name": [["Lung cancer"], ["Breast cancer"], []],
    }
    df = pd.DataFrame(data, index=["CVCL_0001", "CVCL_0002", "CVCL_0003"])
    df.index.name = "accession"
    df.attrs["data_version"] = "99.0"
    return df


@pytest.fixture
def cello(mock_df: pd.DataFrame) -> Cellosaurus:
    """Create a Cellosaurus instance from mock data."""
    return Cellosaurus.from_dataframe(mock_df)


def test_from_dataframe(cello: Cellosaurus) -> None:
    """Test creating Cellosaurus from a DataFrame."""
    assert isinstance(cello, Cellosaurus)
    assert len(cello) == 3


def test_repr(cello: Cellosaurus) -> None:
    """Test string representation."""
    r = repr(cello)
    assert "Cellosaurus" in r
    assert "cells: 3" in r
    assert "release: 99.0" in r


def test_data_version(cello: Cellosaurus) -> None:
    """Test data version attribute."""
    assert cello.data_version == "99.0"


def test_shape(cello: Cellosaurus) -> None:
    """Test shape property."""
    assert cello.shape == (3, len(cello.df.columns))


def test_accessions(cello: Cellosaurus) -> None:
    """Test accessions property."""
    assert cello.accessions == ["CVCL_0001", "CVCL_0002", "CVCL_0003"]


def test_columns(cello: Cellosaurus) -> None:
    """Test columns property."""
    assert "cell_line_name" in cello.columns


def test_getitem(cello: Cellosaurus) -> None:
    """Test bracket accessor."""
    series = cello["cell_line_name"]
    assert series.loc["CVCL_0001"] == "Alpha"


def test_head(cello: Cellosaurus) -> None:
    """Test head method."""
    result = cello.head(2)
    assert len(result) == 2


def test_exclude_contaminated_cells(cello: Cellosaurus) -> None:
    """Test excluding contaminated cell lines."""
    result = cello.exclude_contaminated_cells()
    assert "CVCL_0002" not in result.accessions
    assert "CVCL_0001" in result.accessions


def test_exclude_non_cancer_cells(cello: Cellosaurus) -> None:
    """Test excluding non-cancer cell lines."""
    result = cello.exclude_non_cancer_cells()
    assert "CVCL_0003" not in result.accessions


def test_exclude_non_human_cells(cello: Cellosaurus) -> None:
    """Test excluding non-human cell lines."""
    result = cello.exclude_non_human_cells()
    assert "CVCL_0003" not in result.accessions
    assert "CVCL_0001" in result.accessions


def test_exclude_problematic_cells(cello: Cellosaurus) -> None:
    """Test excluding problematic cell lines."""
    result = cello.exclude_problematic_cells()
    assert "CVCL_0002" not in result.accessions


def test_select_cells(cello: Cellosaurus) -> None:
    """Test selecting cells by criteria."""
    result = cello.select_cells(category="Cancer cell line")
    assert len(result) == 2


def test_select_cells_no_args(cello: Cellosaurus) -> None:
    """Test select_cells raises with no arguments."""
    with pytest.raises(ValueError, match="At least one"):
        cello.select_cells()


def test_select_cells_invalid_col(cello: Cellosaurus) -> None:
    """Test select_cells raises with invalid column."""
    with pytest.raises(ValueError, match="Invalid column"):
        cello.select_cells(bad_col="x")


def test_select_cells_no_match(cello: Cellosaurus) -> None:
    """Test select_cells raises when no cells match."""
    with pytest.raises(ValueError, match="No cell lines matched"):
        cello.select_cells(category="Nonexistent")


def test_map_cells_invalid_key_type(cello: Cellosaurus) -> None:
    """Test map_cells raises with invalid key_type."""
    with pytest.raises(ValueError, match="Invalid key_type"):
        cello.map_cells(["Alpha"], key_type="bad")


def test_map_cells_already_accessions(cello: Cellosaurus) -> None:
    """Test map_cells with accession inputs."""
    result = cello.map_cells(["CVCL_0001", "CVCL_0002"])
    assert result == {"CVCL_0001": "CVCL_0001", "CVCL_0002": "CVCL_0002"}


def test_map_cells_by_name(cello: Cellosaurus) -> None:
    """Test map_cells by cell line name."""
    result = cello.map_cells(["Alpha"])
    assert result["Alpha"] == "CVCL_0001"


def test_map_cells_strict_failure(cello: Cellosaurus) -> None:
    """Test map_cells strict mode raises on failure."""
    with pytest.raises(ValueError, match="Failed to map"):
        cello.map_cells(["NoSuchCell"], strict=True)


def test_map_cells_nonstrict_none(cello: Cellosaurus) -> None:
    """Test map_cells non-strict mode returns None for missing."""
    result = cello.map_cells(["NoSuchCell"])
    assert result["NoSuchCell"] is None


def test_export(cello: Cellosaurus, tmp_path: Path) -> None:
    """Test exporting to CSV."""
    path = tmp_path / "test.csv"
    result = cello.export(path)
    assert result.exists()
    exported = pd.read_csv(result, index_col=0)
    assert len(exported) == 3
