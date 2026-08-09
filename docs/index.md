# cellosaurus

Cellosaurus identifier mapping toolkit.

The package wraps the [Cellosaurus](https://www.cellosaurus.org/) cell-line
database (downloaded and cached from ExPASy) in a single `Cellosaurus` class, and
provides `standardize_cells` and `current_cellosaurus_version` as standalone
helpers.

## Installation

### uv method

This package is hosted at [python.acidgenomics.com](https://python.acidgenomics.com/).
We recommend using [uv](https://docs.astral.sh/uv/) to install.

```sh
uv pip install \
    --index-url 'https://python.acidgenomics.com/simple/' \
    cellosaurus
```

Or add the index to your project's `pyproject.toml`:

```toml
[[tool.uv.index]]
url = "https://python.acidgenomics.com/simple/"
```

Then install:

```sh
uv add cellosaurus
```

### Conda method

Configure [Conda](https://docs.conda.io/) to use the
[Bioconda](https://bioconda.github.io/) channels.

```sh
# Don't install recipe into base environment.
name='cellosaurus'
conda create --name="$name" "$name"
conda activate "$name"
python -c 'import cellosaurus'
```

## Loading the database

```pycon
>>> from cellosaurus import Cellosaurus
>>> cello = Cellosaurus(cache_dir="~/.cache/cellosaurus")  # doctest: +SKIP
```

The TXT database file is downloaded once and cached under `cache_dir`; pass
`update=True` to force a re-download. `cello.shape`, `cello.columns`, and
`cello.accessions` inspect the resulting `pandas.DataFrame`, and `cello["column"]`
subscripts it directly.

## Filtering

`exclude_contaminated_cells`, `exclude_non_cancer_cells`, `exclude_non_human_cells`,
and `exclude_problematic_cells` each return a new filtered `Cellosaurus` instance,
so they chain:

```pycon
>>> filtered = cello.exclude_non_human_cells().exclude_non_cancer_cells()  # doctest: +SKIP
```

`select_cells` subsets by exact column values (`organism`, `oncotree_code`,
`sex_of_cell`, and others), accepting scalars or lists per keyword.

## Mapping cell line names

`map_cells` resolves inconsistently formatted cell line names (as they'd appear in
a spreadsheet or ELN) to Cellosaurus identifiers, standardizing and checking against
accessions, synonyms, and known misspellings before giving up:

```pycon
>>> cello.map_cells(["Jurkat", "HeLa"])  # doctest: +SKIP
{'Jurkat': 'CVCL_0065', 'HeLa': 'CVCL_0030'}
```

Pass `strict=True` to raise instead of returning `None` for unmapped names, and
`key_type` to resolve to `depmap_id`, `sanger_model_id`, `atcc_id`, or
`cell_line_name` instead of the default Cellosaurus accession.

`standardize_cells` is the name-normalization step `map_cells` uses internally, and
is also exported standalone:

```pycon
>>> from cellosaurus import standardize_cells
>>> standardize_cells(["22Rv1", "Jurkat", "Ramos (RA-1)"])
['22_RV_1', 'JURKAT', 'RAMOS']
```

## Mutations and gene fusions

`mutations` and `gene_fusions` extract per-cell-line variant annotations (restricted
to human, cancer, non-contaminated lines); `cells_per_mutation` and
`cells_per_gene_fusion` turn those into a boolean cell-by-feature matrix, keeping
only features shared by at least `min_cells` cell lines. `tnbc` returns accessions
for triple-negative breast cancer lines specifically.

## Checking the database version

```pycon
>>> from cellosaurus import current_cellosaurus_version
>>> ver = current_cellosaurus_version()  # doctest: +SKIP
>>> isinstance(ver, str)  # doctest: +SKIP
True
```

```{toctree}
:maxdepth: 1
:caption: Contents
:hidden:

reference/index
changelog
```
