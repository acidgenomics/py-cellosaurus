"""Global constants."""

from __future__ import annotations

import csv
import importlib.resources

CELLOSAURUS_TXT_URL = "https://ftp.expasy.org/databases/cellosaurus/cellosaurus.txt"

CELLOSAURUS_RELNOTES_URL = "https://ftp.expasy.org/databases/cellosaurus/cellosaurus_relnotes.txt"

MINIMAL_COLS = [
    "accession",
    "cell_line_name",
    "atcc_id",
    "depmap_id",
    "sanger_model_id",
    "ncit_disease_id",
    "ncit_disease_name",
    "oncotree_code",
    "oncotree_main_type",
    "oncotree_name",
    "oncotree_tissue",
    "organism",
]

REQUIRED_KEYS = ["AC", "CA", "DT", "ID"]

NESTED_KEYS = ["CC", "DI", "DR", "HI", "OI", "OX", "RX", "ST", "WW"]

OPTIONAL_KEYS = ["AG", "AS", "SX", "SY"]

COLUMN_RENAME_MAP: dict[str, str] = {
    "AC": "accession",
    "AG": "age_at_sampling",
    "AS": "secondary_accession",
    "CA": "category",
    "CC": "comments",
    "DI": "diseases",
    "DR": "cross_references",
    "DT": "date",
    "HI": "hierarchy",
    "ID": "cell_line_name",
    "OI": "originate_from_same_individual",
    "OX": "species_of_origin",
    "RX": "references_identifiers",
    "ST": "str_profile_data",
    "SX": "sex_of_cell",
    "SY": "synonyms",
    "WW": "web_pages",
}

SELECT_CELLS_VALID_COLS = [
    "category",
    "is_cancer",
    "is_contaminated",
    "is_problematic",
    "ncbi_taxonomy_id",
    "ncit_disease_id",
    "ncit_disease_name",
    "oncotree_code",
    "oncotree_main_type",
    "oncotree_name",
    "oncotree_tissue",
    "organism",
    "sex_of_cell",
]

EXPORT_DROP_COLS = [
    "comments",
    "cross_references",
    "date",
    "diseases",
    "hierarchy",
    "originate_from_same_individual",
    "references_identifiers",
    "str_profile_data",
    "web_pages",
]


def _load_overrides() -> dict[str, str]:
    """Load identifier overrides from the bundled CSV file."""
    ref = importlib.resources.files("cellosaurus").joinpath("overrides.csv")
    with importlib.resources.as_file(ref) as path, open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        return {row["input"]: row["output"] for row in reader}


OVERRIDES: dict[str, str] = _load_overrides()
