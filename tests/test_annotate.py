"""Tests for cellosaurus._annotate."""

import pandas as pd

from cellosaurus._annotate import (
    add_atcc_id,
    add_depmap_id,
    add_is_cancer,
    add_is_contaminated,
    add_is_problematic,
    add_misspellings,
    add_ncit_disease,
    add_taxonomy,
    format_comments,
    format_cross_references,
    format_diseases,
    format_hierarchy,
    format_secondary_accession,
    format_synonyms,
)


def _make_df(**kwargs: list) -> pd.DataFrame:
    """Create a small DataFrame for testing."""
    return pd.DataFrame(kwargs, index=["CVCL_0001"])


def test_format_comments() -> None:
    """Test formatting of comments column."""
    df = _make_df(comments=[["Group: TNBC", "Population: Caucasian"]])
    result = format_comments(df)
    assert result.loc["CVCL_0001", "comments"] == {
        "Group": ["TNBC"],
        "Population": ["Caucasian"],
    }


def test_format_comments_empty() -> None:
    """Test formatting of empty comments."""
    df = _make_df(comments=[[]])
    result = format_comments(df)
    assert result.loc["CVCL_0001", "comments"] == {}


def test_format_cross_references() -> None:
    """Test formatting of cross references column."""
    df = _make_df(cross_references=[["ATCC; CRL-1234", "DepMap; ACH-001"]])
    result = format_cross_references(df)
    assert result.loc["CVCL_0001", "cross_references"] == {
        "ATCC": ["CRL-1234"],
        "DepMap": ["ACH-001"],
    }


def test_format_diseases() -> None:
    """Test formatting of diseases column."""
    df = _make_df(diseases=[["NCIt; C12345; Lung cancer"]])
    result = format_diseases(df)
    assert "NCIt" in result.loc["CVCL_0001", "diseases"]


def test_format_hierarchy() -> None:
    """Test formatting of hierarchy column."""
    df = _make_df(hierarchy=[["CVCL_0001 ! Parent Cell"]])
    result = format_hierarchy(df)
    assert result.loc["CVCL_0001", "hierarchy"] == ["CVCL_0001"]


def test_format_secondary_accession() -> None:
    """Test formatting of secondary accession column."""
    df = _make_df(secondary_accession=["CVCL_A001; CVCL_A002"])
    result = format_secondary_accession(df)
    assert result.loc["CVCL_0001", "secondary_accession"] == [
        "CVCL_A001",
        "CVCL_A002",
    ]


def test_format_synonyms() -> None:
    """Test formatting of synonyms column."""
    df = _make_df(synonyms=["Syn1; Syn2; Syn3"])
    result = format_synonyms(df)
    assert result.loc["CVCL_0001", "synonyms"] == ["Syn1", "Syn2", "Syn3"]


def test_add_atcc_id() -> None:
    """Test adding ATCC ID column."""
    df = _make_df(cross_references=[{"ATCC": ["CRL-5678"]}])
    result = add_atcc_id(df)
    assert result.loc["CVCL_0001", "atcc_id"] == "CRL-5678"


def test_add_atcc_id_missing() -> None:
    """Test adding ATCC ID when not present."""
    df = _make_df(cross_references=[{}])
    result = add_atcc_id(df)
    assert result.loc["CVCL_0001", "atcc_id"] is None


def test_add_depmap_id() -> None:
    """Test adding DepMap ID column."""
    df = _make_df(cross_references=[{"DepMap": ["ACH-000001"]}])
    result = add_depmap_id(df)
    assert result.loc["CVCL_0001", "depmap_id"] == "ACH-000001"


def test_add_is_cancer() -> None:
    """Test adding is_cancer flag for cancer cell lines."""
    df = _make_df(category=["Cancer cell line"])
    result = add_is_cancer(df)
    assert result.loc["CVCL_0001", "is_cancer"]


def test_add_is_cancer_false() -> None:
    """Test adding is_cancer flag for non-cancer cell lines."""
    df = _make_df(category=["Hybridoma"])
    result = add_is_cancer(df)
    assert not result.loc["CVCL_0001", "is_cancer"]


def test_add_is_contaminated() -> None:
    """Test adding is_contaminated flag."""
    df = _make_df(comments=[{"Problematic cell line": ["Contaminated. Known to be ..."]}])
    result = add_is_contaminated(df)
    assert result.loc["CVCL_0001", "is_contaminated"]


def test_add_is_contaminated_false() -> None:
    """Test adding is_contaminated flag when not contaminated."""
    df = _make_df(comments=[{}])
    result = add_is_contaminated(df)
    assert not result.loc["CVCL_0001", "is_contaminated"]


def test_add_is_problematic() -> None:
    """Test adding is_problematic flag."""
    df = _make_df(comments=[{"Problematic cell line": ["Misidentified"]}])
    result = add_is_problematic(df)
    assert result.loc["CVCL_0001", "is_problematic"]


def test_add_misspellings() -> None:
    """Test adding misspellings column."""
    df = _make_df(comments=[{"Misspelling": ["HEla; in Smith et al."]}])
    result = add_misspellings(df)
    assert result.loc["CVCL_0001", "misspellings"] == ["HEla"]


def test_add_ncit_disease() -> None:
    """Test adding NCIt disease columns."""
    df = _make_df(diseases=[{"NCIt": ["C12345; Lung adenocarcinoma"]}])
    result = add_ncit_disease(df)
    assert result.loc["CVCL_0001", "ncit_disease_id"] == ["C12345"]
    assert result.loc["CVCL_0001", "ncit_disease_name"] == ["Lung adenocarcinoma"]


def test_add_taxonomy() -> None:
    """Test adding taxonomy columns."""
    df = _make_df(species_of_origin=[["NCBI_TaxID=9606; ! Homo sapiens"]])
    result = add_taxonomy(df)
    assert result.loc["CVCL_0001", "ncbi_taxonomy_id"] == [9606]
    assert "species_of_origin" not in result.columns
