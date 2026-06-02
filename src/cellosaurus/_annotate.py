"""Annotation enrichment for Cellosaurus DataFrame.

This module provides functions that add derived columns (annotations)
to a parsed Cellosaurus DataFrame. Each function operates on a single
concern, keeping the processing pipeline composable and testable.
"""

from __future__ import annotations

import contextlib
import re

import pandas as pd

from cellosaurus._parse import _split_nested

# =============================================================================
# Formatting helpers
# =============================================================================


def format_comments(df: pd.DataFrame) -> pd.DataFrame:
    """Parse comments into nested dicts keyed by comment type.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``comments`` column of raw string lists.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``comments`` as list of dicts.
    """

    def _parse(vals: list[str]) -> dict[str, list[str]]:
        if not vals:
            return {}
        vals = [v.rstrip(".") for v in vals]
        seen: set[str] = set()
        unique: list[str] = []
        for v in vals:
            if v not in seen:
                seen.add(v)
                unique.append(v)
        return _split_nested(unique, ": ")

    df["comments"] = df["comments"].apply(_parse)
    return df


def format_cross_references(df: pd.DataFrame) -> pd.DataFrame:
    """Parse cross-references into nested dicts keyed by database name.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``cross_references`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``cross_references`` as dicts.
    """

    def _parse(vals: list[str]) -> dict[str, list[str]]:
        if not vals:
            return {}
        return _split_nested(vals, "; ")

    df["cross_references"] = df["cross_references"].apply(_parse)
    return df


def format_diseases(df: pd.DataFrame) -> pd.DataFrame:
    """Parse diseases into nested dicts keyed by ontology source.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``diseases`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``diseases`` as dicts.
    """

    def _parse(vals: list[str]) -> dict[str, list[str]]:
        if not vals:
            return {}
        return _split_nested(vals, "; ")

    df["diseases"] = df["diseases"].apply(_parse)
    return df


def format_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """Parse hierarchy entries, extracting accession identifiers.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``hierarchy`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``hierarchy`` as list of accession strings.
    """

    def _parse(vals: list[str]) -> list[str]:
        if not vals:
            return []
        out = []
        for v in vals:
            parts = v.split(" ! ", maxsplit=1)
            out.append(parts[0])
        return out

    df["hierarchy"] = df["hierarchy"].apply(_parse)
    return df


def format_secondary_accession(df: pd.DataFrame) -> pd.DataFrame:
    """Split secondary accession into a list.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``secondary_accession`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``secondary_accession`` as list of strings.
    """

    def _parse(val: str | None) -> list[str]:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return []
        return [s.strip() for s in val.split("; ")]

    df["secondary_accession"] = df["secondary_accession"].apply(_parse)
    return df


def format_synonyms(df: pd.DataFrame) -> pd.DataFrame:
    """Split synonyms into a list.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``synonyms`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``synonyms`` as list of strings.
    """

    def _parse(val: str | None) -> list[str]:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return []
        return [s.strip() for s in val.split("; ")]

    df["synonyms"] = df["synonyms"].apply(_parse)
    return df


def format_age_at_sampling(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up age_at_sampling, converting 'Age unspecified' to None.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``age_at_sampling`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with cleaned ``age_at_sampling``.
    """
    df["age_at_sampling"] = df["age_at_sampling"].replace("Age unspecified", None)
    return df


def format_date(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date entries into dicts keyed by date type.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``date`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``date`` as dicts.
    """

    def _parse(vals: list[str]) -> dict[str, list[str]]:
        if not vals:
            return {}
        expanded: list[str] = []
        for v in vals:
            expanded.extend(v.split("; "))
        return _split_nested(expanded, ": ")

    df["date"] = df["date"].apply(_parse)
    return df


def format_references_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Parse reference identifiers into dicts.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``references_identifiers`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``references_identifiers`` as dicts.
    """

    def _parse(vals: list[str]) -> dict[str, list[str]]:
        if not vals:
            return {}
        cleaned = [v.rstrip(";") for v in vals]
        return _split_nested(cleaned, "=")

    df["references_identifiers"] = df["references_identifiers"].apply(_parse)
    return df


def format_str_profile_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse STR profile data into dicts.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``str_profile_data`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``str_profile_data`` as dicts.
    """

    def _parse(vals: list[str]) -> dict[str, list[str]]:
        if not vals:
            return {}
        return _split_nested(vals, ": ")

    df["str_profile_data"] = df["str_profile_data"].apply(_parse)
    return df


# =============================================================================
# Annotation adders
# =============================================================================


def _extract_cross_ref(
    cross_refs: dict[str, list[str]],
    key_name: str,
) -> str | None:
    """Extract first identifier from cross-references for a given key.

    Takes the first matching identifier, which helps avoid issues with
    discontinued identifiers (e.g. CVCL_0455).

    Parameters
    ----------
    cross_refs : dict
        Parsed cross-references dict.
    key_name : str
        Database key name (e.g. ``"ATCC"``, ``"DepMap"``).

    Returns
    -------
    str or None
        First matching identifier, or ``None``.
    """
    ids = cross_refs.get(key_name)
    if ids is None or len(ids) == 0:
        return None
    return ids[0]


def _extract_comment(
    comments: dict[str, list[str]],
    key_name: str,
) -> list[str]:
    """Extract values for a comment key.

    Parameters
    ----------
    comments : dict
        Parsed comments dict.
    key_name : str
        Comment key name.

    Returns
    -------
    list[str]
        Values for that key, or empty list.
    """
    return comments.get(key_name, [])


def add_bto_id(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``bto_id`` column from cross-references.

    BTO identifiers are already in CURIE format (e.g. ``BTO:0000565``).
    A cell line may map to multiple BTO terms, so this column is a list.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``cross_references`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``bto_id`` column added.
    """
    df["bto_id"] = df["cross_references"].apply(
        lambda x: x.get("BTO", [])
    )
    return df


def add_atcc_id(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``atcc_id`` column from cross-references.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``cross_references`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``atcc_id`` column added.
    """
    df["atcc_id"] = df["cross_references"].apply(_extract_cross_ref, key_name="ATCC")
    return df


def add_depmap_id(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``depmap_id`` column from cross-references.

    Note that some cell lines (e.g. CVCL_0041) map to multiple DepMap
    identifiers.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``cross_references`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``depmap_id`` column added.
    """
    df["depmap_id"] = df["cross_references"].apply(_extract_cross_ref, key_name="DepMap")
    return df


def add_sanger_model_id(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``sanger_model_id`` column from cross-references.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``cross_references`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``sanger_model_id`` column added.
    """
    df["sanger_model_id"] = df["cross_references"].apply(
        _extract_cross_ref, key_name="Cell_Model_Passport"
    )
    return df


def add_is_cancer(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``is_cancer`` boolean column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``category`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``is_cancer`` column added.
    """
    df["is_cancer"] = df["category"] == "Cancer cell line"
    return df


def add_is_contaminated(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``is_contaminated`` boolean column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``comments`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``is_contaminated`` column added.
    """

    def _check(comments: dict[str, list[str]]) -> bool:
        prob = comments.get("Problematic cell line", [])
        return any(p.startswith("Contaminated") for p in prob)

    df["is_contaminated"] = df["comments"].apply(_check)
    return df


def add_is_problematic(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``is_problematic`` boolean column.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``comments`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``is_problematic`` column added.
    """
    df["is_problematic"] = df["comments"].apply(lambda c: "Problematic cell line" in c)
    return df


def add_misspellings(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``misspellings`` column from comments.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``comments`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``misspellings`` column added.
    """

    def _extract(comments: dict[str, list[str]]) -> list[str]:
        vals = _extract_comment(comments, "Misspelling")
        return [re.sub(r";.+$", "", v).strip() for v in vals]

    df["misspellings"] = df["comments"].apply(_extract)
    return df


def add_msi_status(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``msi_status`` column from comments.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``comments`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``msi_status`` column added.
    """
    df["msi_status"] = df["comments"].apply(_extract_comment, key_name="Microsatellite instability")
    return df


def add_population(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``population`` column from comments.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``comments`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``population`` column added.
    """
    df["population"] = df["comments"].apply(_extract_comment, key_name="Population")
    return df


def add_sampling_site(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``sampling_site`` column from comments.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``comments`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``sampling_site`` column added.
    """
    df["sampling_site"] = df["comments"].apply(_extract_comment, key_name="Derived from site")
    return df


def add_uberon(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``uberon_id`` and ``uberon_name`` columns from sampling site.

    Parses UBERON ontology identifiers from the ``sampling_site`` column.
    The raw ``sampling_site`` column is preserved unchanged.

    Cell lines may have multiple sampling sites, so these columns are
    stored as lists.  IDs are normalised to CURIE format (e.g.
    ``UBERON:0000178``).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``sampling_site`` column (list of raw strings).

    Returns
    -------
    pd.DataFrame
        DataFrame with ``uberon_id`` and ``uberon_name`` columns added.
    """

    def _parse(vals: list[str]) -> tuple[list[str], list[str]]:
        if not vals:
            return [], []
        ids: list[str] = []
        names: list[str] = []
        for v in vals:
            parts = v.split("; ")
            uberon_curie: str | None = None
            for part in parts:
                if part.startswith("UBERON=UBERON_"):
                    uberon_curie = "UBERON:" + part[len("UBERON=UBERON_"):]
                    break
            if uberon_curie is None:
                continue
            ids.append(uberon_curie)
            if len(parts) >= 2:
                names.append(parts[1].strip())
        return ids, names

    parsed = df["sampling_site"].apply(_parse)
    df["uberon_id"] = parsed.apply(lambda x: x[0])
    df["uberon_name"] = parsed.apply(lambda x: x[1])
    return df


def add_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``ncbi_taxonomy_id`` and ``organism`` columns.

    Hybrid cell lines contain multiple taxonomies, so these columns
    are stored as lists.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with ``species_of_origin`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``ncbi_taxonomy_id`` and ``organism`` columns,
        and ``species_of_origin`` removed.
    """

    def _parse(vals: list[str]) -> tuple[list[int], list[str]]:
        if not vals:
            return [], []
        tax_ids: list[int] = []
        organisms: list[str] = []
        for v in vals:
            parts = v.split(" ! ", maxsplit=1)
            if len(parts) == 2:
                tid = parts[0].replace("NCBI_TaxID=", "").rstrip(";").strip()
                with contextlib.suppress(ValueError):
                    tax_ids.append(int(tid))
                org = parts[1].strip()
                org = re.sub(r"\s\(.+\)$", "", org)
                organisms.append(org)
        return tax_ids, organisms

    parsed = df["species_of_origin"].apply(_parse)
    df["ncbi_taxonomy_id"] = parsed.apply(lambda x: x[0])
    df["organism"] = parsed.apply(lambda x: x[1])
    df = df.drop(columns=["species_of_origin"])
    return df


def add_ncit_disease(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``ncit_disease_id`` and ``ncit_disease_name`` columns.

    Some cell lines map to multiple NCIt identifiers (e.g. CVCL_0028).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with parsed ``diseases`` column (dict format).

    Returns
    -------
    pd.DataFrame
        DataFrame with disease ID and name columns.
    """

    def _parse(diseases: dict[str, list[str]]) -> tuple[list[str], list[str]]:
        ncit_vals = diseases.get("NCIt", [])
        if not ncit_vals:
            return [], []
        ids: list[str] = []
        names: list[str] = []
        for v in ncit_vals:
            parts = v.split("; ", maxsplit=1)
            if len(parts) == 2:
                ids.append(parts[0].strip())
                names.append(parts[1].strip())
        return ids, names

    parsed = df["diseases"].apply(_parse)
    df["ncit_disease_id"] = parsed.apply(lambda x: x[0])
    df["ncit_disease_name"] = parsed.apply(lambda x: x[1])
    return df


def add_oncotree(
    df: pd.DataFrame,
    ncit2oncotree: pd.DataFrame,
    oncotree: pd.DataFrame,
) -> pd.DataFrame:
    """Add OncoTree metadata columns via NCIt disease ID mapping.

    Parameters
    ----------
    df : pd.DataFrame
        Main DataFrame with ``ncit_disease_id`` column.
    ncit2oncotree : pd.DataFrame
        Mapping table with ``ncit`` and ``oncotree`` columns.
    oncotree : pd.DataFrame
        OncoTree metadata table.

    Returns
    -------
    pd.DataFrame
        DataFrame with OncoTree annotation columns added.
    """
    single_mask = df["ncit_disease_id"].apply(lambda x: len(x) == 1)
    mapping = df.loc[single_mask, ["ncit_disease_id"]].copy()
    mapping["ncit_disease_id_scalar"] = mapping["ncit_disease_id"].apply(lambda x: x[0])
    n2o = ncit2oncotree.rename(
        columns={
            "ncit": "ncit_disease_id_scalar",
            "oncotree": "oncotree_code",
        }
    )
    mapping = mapping.merge(
        n2o,
        on="ncit_disease_id_scalar",
        how="left",
    )
    keep_cols = ["code", "name", "mainType", "tissue", "parent", "level"]
    ot = oncotree[[c for c in keep_cols if c in oncotree.columns]].copy()
    ot = ot.rename(
        columns={
            "code": "oncotree_code",
            "name": "oncotree_name",
            "mainType": "oncotree_main_type",
            "tissue": "oncotree_tissue",
            "parent": "oncotree_parent",
            "level": "oncotree_level",
        }
    )
    mapping = mapping.merge(ot, on="oncotree_code", how="left")
    oncotree_cols = [
        "oncotree_code",
        "oncotree_name",
        "oncotree_main_type",
        "oncotree_tissue",
        "oncotree_parent",
        "oncotree_level",
    ]
    for col in oncotree_cols:
        if col not in mapping.columns:
            mapping[col] = None
    mapping = mapping[oncotree_cols]
    for col in oncotree_cols:
        df[col] = None
    df.loc[mapping.index, oncotree_cols] = mapping[oncotree_cols]
    return df


# =============================================================================
# Pipeline
# =============================================================================


def annotate(
    df: pd.DataFrame,
    ncit2oncotree: pd.DataFrame | None = None,
    oncotree: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Run the full annotation pipeline on a parsed Cellosaurus DataFrame.

    This applies all formatting and annotation steps in the correct
    order.

    Parameters
    ----------
    df : pd.DataFrame
        Parsed DataFrame from :func:`parse_cellosaurus_txt`.
    ncit2oncotree : pd.DataFrame or None
        NCIt-to-OncoTree mapping table. If ``None``, OncoTree columns
        are skipped.
    oncotree : pd.DataFrame or None
        OncoTree reference table. If ``None``, OncoTree columns are
        skipped.

    Returns
    -------
    pd.DataFrame
        Fully annotated DataFrame.
    """
    print("Formatting annotations...")
    df = format_age_at_sampling(df)
    df = format_comments(df)
    df = format_cross_references(df)
    df = format_date(df)
    df = format_diseases(df)
    df = format_hierarchy(df)
    df = format_references_identifiers(df)
    df = format_secondary_accession(df)
    df = format_str_profile_data(df)
    df = format_synonyms(df)
    print("Adding annotations...")
    df = add_atcc_id(df)
    df = add_bto_id(df)
    df = add_depmap_id(df)
    df = add_is_cancer(df)
    df = add_is_contaminated(df)
    df = add_is_problematic(df)
    df = add_misspellings(df)
    df = add_msi_status(df)
    df = add_ncit_disease(df)
    if ncit2oncotree is not None and oncotree is not None:
        df = add_oncotree(df, ncit2oncotree, oncotree)
    df = add_population(df)
    df = add_sampling_site(df)
    df = add_uberon(df)
    df = add_sanger_model_id(df)
    df = add_taxonomy(df)
    df = df.reindex(sorted(df.columns), axis=1)
    return df
