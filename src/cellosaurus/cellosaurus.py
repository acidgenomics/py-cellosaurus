"""Main Cellosaurus class.

This module provides the ``Cellosaurus`` class that wraps a parsed and
annotated pandas DataFrame of the Cellosaurus cell-line database.

Examples
--------
>>> cello = Cellosaurus(cache_dir="~/.cache/cellosaurus")
>>> cello.shape
(156520, 40)
>>> mapped = cello.map_cells(["Jurkat", "HeLa"])
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from cellosaurus._annotate import annotate
from cellosaurus._globals import (
    EXPORT_DROP_COLS,
    MINIMAL_COLS,
    OVERRIDES,
    SELECT_CELLS_VALID_COLS,
)
from cellosaurus._parse import download_cellosaurus_txt, parse_cellosaurus_txt
from cellosaurus.standardize_cells import standardize_cells


class Cellosaurus:
    """Cellosaurus cell-line database wrapper.

    Parameters
    ----------
    cache_dir : str or Path or None
        Directory to cache the downloaded Cellosaurus TXT file.
        Defaults to ``~/.cache/cellosaurus``.
    update : bool
        Force re-download of the database file.
    ncit2oncotree_path : str or Path or None
        Path to a CSV mapping NCIt identifiers to OncoTree codes.
        If ``None``, OncoTree annotations are skipped.
    oncotree_path : str or Path or None
        Path to the OncoTree reference CSV.
        If ``None``, OncoTree annotations are skipped.

    Attributes
    ----------
    df : pd.DataFrame
        Annotated Cellosaurus DataFrame indexed by accession.
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        *,
        update: bool = False,
        ncit2oncotree_path: str | Path | None = None,
        oncotree_path: str | Path | None = None,
    ) -> None:
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "cellosaurus"
        txt_path = download_cellosaurus_txt(cache_dir, update=update)
        df = parse_cellosaurus_txt(txt_path)
        ncit2oncotree: pd.DataFrame | None = None
        oncotree_df: pd.DataFrame | None = None
        if ncit2oncotree_path is not None:
            ncit2oncotree = pd.read_csv(ncit2oncotree_path)
        if oncotree_path is not None:
            oncotree_df = pd.read_csv(oncotree_path)
        self.df = annotate(df, ncit2oncotree, oncotree_df)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> Cellosaurus:
        """Create a ``Cellosaurus`` instance from an existing DataFrame.

        This bypasses downloading and parsing, useful for testing
        or working with pre-processed data.

        Parameters
        ----------
        df : pd.DataFrame
            Annotated Cellosaurus DataFrame (already indexed by
            accession).

        Returns
        -------
        Cellosaurus
            Instance wrapping the given DataFrame.
        """
        obj = cls.__new__(cls)
        obj.df = df
        return obj

    # -- Display ---------------------------------------------------------------

    def __repr__(self) -> str:  # noqa: D105
        lines = [
            "Cellosaurus",
            f"  cells: {len(self.df)}",
        ]
        version = self.data_version
        if version is not None:
            lines.append(f"  release: {version}")
        return "\n".join(lines)

    def __len__(self) -> int:  # noqa: D105
        return len(self.df)

    # -- Properties ------------------------------------------------------------

    @property
    def data_version(self) -> str | None:
        """Return the Cellosaurus release version, if available."""
        return self.df.attrs.get("data_version")

    @property
    def shape(self) -> tuple[int, int]:
        """Return (n_rows, n_cols)."""
        return self.df.shape

    @property
    def accessions(self) -> list[str]:
        """Return all accession identifiers."""
        return list(self.df.index)

    @property
    def columns(self) -> list[str]:
        """Return column names."""
        return list(self.df.columns)

    # -- Subscripting ----------------------------------------------------------

    def __getitem__(self, key: str) -> pd.Series:
        """Access a column by name."""
        result = self.df[key]
        if not isinstance(result, pd.Series):
            raise TypeError(f"Column {key!r} did not return a Series.")
        return result

    def head(self, n: int = 5) -> pd.DataFrame:
        """Return the first *n* rows."""
        return self.df.head(n)

    # -- Filtering (exclude) ---------------------------------------------------

    def exclude_contaminated_cells(self) -> Cellosaurus:
        """Exclude contaminated cell lines.

        Only filters on ``Problematic cell line: Contaminated`` metadata.
        Less strict than :meth:`exclude_problematic_cells`; keeps
        misidentified cell lines.

        Returns
        -------
        Cellosaurus
            Filtered instance.
        """
        mask = ~self.df["is_contaminated"]
        return Cellosaurus.from_dataframe(self.df.loc[mask].copy())

    def exclude_non_cancer_cells(self) -> Cellosaurus:
        """Exclude non-cancer cell lines.

        Returns
        -------
        Cellosaurus
            Filtered instance with only cancer cell lines.
        """
        mask = self.df["is_cancer"]
        return Cellosaurus.from_dataframe(self.df.loc[mask].copy())

    def exclude_non_human_cells(self) -> Cellosaurus:
        """Exclude non-human cell lines.

        Keeps only cell lines whose sole NCBI taxonomy ID is 9606
        (*Homo sapiens*). Hybrid cell lines are removed.

        Returns
        -------
        Cellosaurus
            Filtered instance.
        """
        mask = self.df["ncbi_taxonomy_id"].apply(
            lambda x: isinstance(x, list) and len(x) == 1 and x[0] == 9606
        )
        return Cellosaurus.from_dataframe(self.df.loc[mask].copy())

    def exclude_problematic_cells(self) -> Cellosaurus:
        """Exclude problematic cell lines.

        Filters on any ``Problematic cell line`` comment. More strict
        than :meth:`exclude_contaminated_cells`; also removes
        misidentified lines.

        Returns
        -------
        Cellosaurus
            Filtered instance.
        """
        mask = ~self.df["is_problematic"]
        return Cellosaurus.from_dataframe(self.df.loc[mask].copy())

    # -- Selection -------------------------------------------------------------

    def select_cells(self, **kwargs: object) -> Cellosaurus:
        """Subset cell lines by column values.

        Only exact matching is supported. Supported column names:

        - ``bto_id``
        - ``category``
        - ``is_cancer``
        - ``is_contaminated``
        - ``is_problematic``
        - ``ncbi_taxonomy_id``
        - ``ncit_disease_id``
        - ``ncit_disease_name``
        - ``oncotree_code``
        - ``oncotree_main_type``
        - ``oncotree_name``
        - ``oncotree_tissue``
        - ``organism``
        - ``sex_of_cell``
        - ``uberon_id``
        - ``uberon_name``

        Parameters
        ----------
        **kwargs
            Column-name / value pairs.  Values can be scalars or lists.

        Returns
        -------
        Cellosaurus
            Filtered instance.

        Raises
        ------
        ValueError
            If no keyword arguments are given or an unsupported column
            is specified.
        """
        if not kwargs:
            msg = "At least one keyword argument is required."
            raise ValueError(msg)
        invalid = set(kwargs.keys()) - set(SELECT_CELLS_VALID_COLS)
        if invalid:
            msg = f"Invalid column(s): {', '.join(sorted(invalid))}"
            raise ValueError(msg)
        masks: list[pd.Series] = []
        for col, value in kwargs.items():
            vals_raw = self.df[col]
            if not isinstance(vals_raw, pd.Series):
                raise TypeError(f"Column {col!r} is not a Series.")
            vals: pd.Series = vals_raw
            arg_list = value if isinstance(value, list) else [value]
            if bool(vals.apply(lambda v: isinstance(v, list)).any()):
                mask_raw = vals.apply(
                    lambda v, a=arg_list: (
                        any(item in a for item in v) if isinstance(v, list) else v in a
                    )
                )
                if not isinstance(mask_raw, pd.Series):
                    raise TypeError("apply() did not return a Series.")
                mask: pd.Series = mask_raw
            else:
                mask = vals.isin(arg_list)
            masks.append(mask)
        combined = masks[0]
        for m in masks[1:]:
            combined = combined & m
        result = self.df.loc[combined]
        if result.empty:
            msg = "No cell lines matched selection criteria."
            raise ValueError(msg)
        return Cellosaurus.from_dataframe(result.copy())

    # -- Mutations & gene fusions ----------------------------------------------

    def mutations(self) -> dict[str, list[str]]:
        """Extract mutations per cell line.

        Returns a dict mapping Cellosaurus accession to a list of
        mutation strings (``GENE_NAME (HGNC_ID)``).

        Only human, cancer, non-contaminated cell lines are included.

        Returns
        -------
        dict[str, list[str]]
            Mutations keyed by accession.
        """
        obj = self.exclude_non_human_cells().exclude_non_cancer_cells().exclude_contaminated_cells()
        pattern = r"^Mutation; HGNC; ([0-9]+); ([^;]+);.+$"
        result: dict[str, list[str]] = {}
        for acc, row in obj.df.iterrows():
            comments_raw = row.get("comments", {})
            comments: dict = comments_raw if isinstance(comments_raw, dict) else {}
            seq_vars = comments.get("Sequence variation", [])
            matches = [s for s in seq_vars if re.match(pattern, s)]
            if matches:
                muts = list({re.sub(pattern, r"\2 (\1)", m) for m in matches})
                result[str(acc)] = sorted(muts)
        return result

    def gene_fusions(self) -> dict[str, list[str]]:
        """Extract gene fusions per cell line.

        Returns a dict mapping Cellosaurus accession to a list of
        fusion strings (``FUSION_NAME (HGNC1-HGNC2)``).

        Only human, cancer, non-contaminated cell lines are included.

        Returns
        -------
        dict[str, list[str]]
            Gene fusions keyed by accession.
        """
        obj = self.exclude_non_human_cells().exclude_non_cancer_cells().exclude_contaminated_cells()
        pattern = (
            r"^Gene fusion; "
            r"HGNC; ([0-9]+); ([^ ]+) \+ "
            r"HGNC; ([0-9]+); ([^ ]+); "
            r"Name\(s\)=([^ ,;]+).+$"
        )
        result: dict[str, list[str]] = {}
        for acc, row in obj.df.iterrows():
            comments_raw = row.get("comments", {})
            comments: dict = comments_raw if isinstance(comments_raw, dict) else {}
            seq_vars = comments.get("Sequence variation", [])
            matches = [s for s in seq_vars if re.match(pattern, s)]
            if matches:
                fusions = list({re.sub(pattern, r"\5 (\1-\3)", m) for m in matches})
                result[str(acc)] = sorted(fusions)
        return result

    def _cells_per_feature(
        self,
        features: dict[str, list[str]],
        min_cells: int = 2,
    ) -> pd.DataFrame | None:
        """Build a cell-by-feature boolean matrix.

        Shared logic for :meth:`cells_per_mutation` and
        :meth:`cells_per_gene_fusion`.

        Parameters
        ----------
        features : dict[str, list[str]]
            Feature dict keyed by accession.
        min_cells : int
            Minimum number of cells sharing a feature.

        Returns
        -------
        pd.DataFrame or None
            Boolean matrix, or ``None`` if nothing passes filters.
        """
        if not features:
            return None
        all_feats: set[str] = set()
        for v in features.values():
            all_feats.update(v)
        rows: dict[str, dict[str, bool]] = {}
        for acc, feats in features.items():
            rows[acc] = {f: f in feats for f in all_feats}
        mat = pd.DataFrame.from_dict(rows, orient="index")
        mat = mat.fillna(False).astype(bool)
        col_counts = mat.sum(axis=0)
        keep_cols = col_counts >= min_cells
        if not keep_cols.any():
            return None
        mat = mat.loc[:, keep_cols]
        keep_rows = mat.sum(axis=1) > 0
        if not keep_rows.any():
            return None
        mat = mat.loc[keep_rows]
        mat = mat[mat.sum().sort_values(ascending=False).index]
        minimal = [c for c in MINIMAL_COLS if c in self.df.columns]
        info = self.df.loc[mat.index, minimal].copy()
        return pd.concat([info, mat], axis=1)

    def cells_per_mutation(
        self,
        min_cells: int = 2,
    ) -> pd.DataFrame | None:
        """Cell-by-mutation boolean matrix.

        Parameters
        ----------
        min_cells : int
            Minimum number of cells per mutation (default 2).

        Returns
        -------
        pd.DataFrame or None
            Boolean matrix with cell info columns, or ``None``.
        """
        return self._cells_per_feature(self.mutations(), min_cells)

    def cells_per_gene_fusion(
        self,
        min_cells: int = 2,
    ) -> pd.DataFrame | None:
        """Cell-by-gene-fusion boolean matrix.

        Parameters
        ----------
        min_cells : int
            Minimum number of cells per gene fusion (default 2).

        Returns
        -------
        pd.DataFrame or None
            Boolean matrix with cell info columns, or ``None``.
        """
        return self._cells_per_feature(self.gene_fusions(), min_cells)

    # -- TNBC ------------------------------------------------------------------

    def tnbc(self) -> list[str]:
        """Return accession identifiers for triple-negative breast cancer lines.

        Returns
        -------
        list[str]
            Cellosaurus accession identifiers.
        """
        obj = self.exclude_non_human_cells().exclude_non_cancer_cells().exclude_contaminated_cells()
        result: list[str] = []
        for acc, row in obj.df.iterrows():
            comments_raw = row.get("comments", {})
            comments: dict = comments_raw if isinstance(comments_raw, dict) else {}
            groups = comments.get("Group", [])
            if "Triple negative breast cancer (TNBC) cell line" in groups:
                result.append(str(acc))
        return result

    # -- Mapping ---------------------------------------------------------------

    def map_cells(
        self,
        cells: list[str],
        key_type: str = "cellosaurus_id",
        *,
        strict: bool = False,
    ) -> dict[str, str | None]:
        """Map cell line names to Cellosaurus identifiers.

        This function is designed to take input from a spreadsheet,
        electronic laboratory notebook entry, or cell line provider
        where names may be inconsistent.

        Parameters
        ----------
        cells : list[str]
            Cell names (or Cellosaurus accession identifiers).
        key_type : str
            Identifier format to return. One of ``"cellosaurus_id"``
            (default), ``"depmap_id"``, ``"sanger_model_id"``,
            ``"atcc_id"``, ``"cell_line_name"``.
        strict : bool
            If ``True``, raise on mapping failure. If ``False``,
            return ``None`` for failures.

        Returns
        -------
        dict[str, str | None]
            Mapping from input cell name to matched identifier.

        Raises
        ------
        ValueError
            If ``strict=True`` and any cell fails to map.
        """
        valid_key_types = {
            "cellosaurus_id": "accession",
            "depmap_id": "depmap_id",
            "sanger_model_id": "sanger_model_id",
            "atcc_id": "atcc_id",
            "cell_line_name": "cell_line_name",
        }
        if key_type not in valid_key_types:
            msg = f"Invalid key_type {key_type!r}; choose from {list(valid_key_types.keys())}"
            raise ValueError(msg)
        id_col = valid_key_types[key_type]
        use_index = id_col == "accession"
        all_ids = list(self.df.index) if use_index else list(self.df[id_col])

        if all(c in all_ids for c in cells):
            return {c: c for c in cells}
        overrides = OVERRIDES
        resolved = []
        for cell in cells:
            std = standardize_cells(cell)
            if isinstance(std, list):
                std = std[0]
            if std in overrides:
                resolved.append(overrides[std])
            else:
                resolved.append(cell)
        df = self.df.copy()
        df["_cell_line_name_no_bracket"] = df["cell_line_name"].str.replace(
            r"[_ ]+\[.+$", "", regex=True
        )
        lookup_cols = [
            "secondary_accession",
            "depmap_id",
            "sanger_model_id",
            "atcc_id",
            "cell_line_name",
            "_cell_line_name_no_bracket",
            "synonyms",
            "misspellings",
        ]
        lookup_cols = [c for c in lookup_cols if c in df.columns]
        result: dict[str, str | None] = {}
        for orig, cell in zip(cells, resolved, strict=True):
            matched_acc = self._match_cell(cell, df, lookup_cols)
            if matched_acc is None:
                std = standardize_cells(cell)
                if isinstance(std, list):
                    std = std[0]
                if std in overrides:
                    std = overrides[std]
                std_df = pd.DataFrame(
                    {
                        "_std_name": standardize_cells(df["cell_line_name"].tolist()),
                        "synonyms": df["synonyms"],
                        "misspellings": df["misspellings"],
                    },
                    index=df.index,
                )
                matched_acc = self._match_cell(
                    std, std_df, ["_std_name", "synonyms", "misspellings"]
                )
            if matched_acc is not None:
                if use_index:
                    result[orig] = matched_acc
                else:
                    val = df.loc[matched_acc, id_col]
                    result[orig] = val if pd.notna(val) else None
            else:
                if strict:
                    msg = f"Failed to map cell: {orig!r}"
                    raise ValueError(msg)
                result[orig] = None
        return result

    @staticmethod
    def _match_cell(
        cell: str,
        df: pd.DataFrame,
        columns: list[str],
    ) -> str | None:
        """Attempt to match a single cell name against DataFrame columns.

        Parameters
        ----------
        cell : str
            Cell name to match.
        df : pd.DataFrame
            DataFrame to search (with accession as index).
        columns : list[str]
            Columns to search, in priority order.

        Returns
        -------
        str or None
            Matched accession, or ``None``.
        """
        for col in columns:
            if col not in df.columns:
                continue
            series = df[col]
            if bool(series.apply(type).eq(list).any()):
                mask = series.apply(lambda v: cell in v if isinstance(v, list) else v == cell)
            else:
                mask = series == cell
            matches = df.index[mask]
            if len(matches) > 0:
                return str(matches[0])
        if cell in df.index:
            return str(cell)
        return None

    # -- Export ----------------------------------------------------------------

    def export(self, path: str | Path) -> Path:
        """Export to CSV, dropping complex nested columns.

        Parameters
        ----------
        path : str or Path
            Destination file path.

        Returns
        -------
        Path
            Path to the written file.
        """
        path = Path(path)
        drop = [c for c in EXPORT_DROP_COLS if c in self.df.columns]
        out = self.df.drop(columns=drop).copy()
        for col in out.columns:
            if bool(out[col].apply(type).eq(list).any()):
                out[col] = out[col].apply(
                    lambda v: "; ".join(str(i) for i in v) if isinstance(v, list) else v
                )
        out.to_csv(path)
        return path
