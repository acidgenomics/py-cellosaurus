"""Tests for cellosaurus._globals."""

from cellosaurus._globals import (
    CELLOSAURUS_TXT_URL,
    COLUMN_RENAME_MAP,
    EXPORT_DROP_COLS,
    MINIMAL_COLS,
    OVERRIDES,
    SELECT_CELLS_VALID_COLS,
)


def test_cellosaurus_txt_url() -> None:
    """Test Cellosaurus TXT URL format."""
    assert CELLOSAURUS_TXT_URL.startswith("https://")
    assert CELLOSAURUS_TXT_URL.endswith(".txt")


def test_column_rename_map_keys() -> None:
    """Test column rename map contains expected keys."""
    assert "AC" in COLUMN_RENAME_MAP
    assert "ID" in COLUMN_RENAME_MAP
    assert COLUMN_RENAME_MAP["AC"] == "accession"
    assert COLUMN_RENAME_MAP["ID"] == "cell_line_name"


def test_minimal_cols() -> None:
    """Test minimal columns set."""
    assert "accession" in MINIMAL_COLS
    assert "cell_line_name" in MINIMAL_COLS


def test_select_cells_valid_cols() -> None:
    """Test valid columns for select_cells."""
    assert "category" in SELECT_CELLS_VALID_COLS
    assert "organism" in SELECT_CELLS_VALID_COLS
    assert "is_cancer" in SELECT_CELLS_VALID_COLS


def test_export_drop_cols() -> None:
    """Test export drop columns set."""
    assert "comments" in EXPORT_DROP_COLS
    assert "cross_references" in EXPORT_DROP_COLS


def test_overrides() -> None:
    """Test overrides dictionary."""
    assert isinstance(OVERRIDES, dict)
    assert len(OVERRIDES) > 0
    # All keys should be uppercase standardized names.
    for key in OVERRIDES:
        assert key == key.upper()
    # All values should be CVCL accessions.
    for val in OVERRIDES.values():
        assert val.startswith("CVCL_")
