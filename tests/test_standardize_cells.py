"""Tests for cellosaurus.standardize_cells."""

from cellosaurus.standardize_cells import standardize_cells


def test_single_string() -> None:
    """Test standardizing a single string."""
    result = standardize_cells("Jurkat")
    assert result == "JURKAT"


def test_list() -> None:
    """Test standardizing a list of strings."""
    result = standardize_cells(["22Rv1", "Jurkat"])
    assert isinstance(result, list)
    assert result == ["22_RV_1", "JURKAT"]


def test_bracket_removal() -> None:
    """Test bracket content removal."""
    result = standardize_cells("Ramos (RA-1)")
    assert result == "RAMOS"


def test_empty_becomes_invalid() -> None:
    """Test that empty result becomes INVALID."""
    result = standardize_cells("---")
    assert result == "INVALID"


def test_underscore_insertion() -> None:
    """Test underscore insertion at boundaries."""
    result = standardize_cells("HeLa")
    assert isinstance(result, str)
    # Letters and digits boundary insertion.
    result2 = standardize_cells("A549")
    assert result2 == "A_549"
