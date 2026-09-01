# cellosaurus

[![Install with Bioconda](https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg)](https://bioconda.github.io/recipes/cellosaurus/README.html) ![Lifecycle: maturing](https://img.shields.io/badge/lifecycle-maturing-blue.svg)

Cellosaurus identifier mapping toolkit.

## Installation

### [uv][] method

This is a [Python][] package hosted on [PyPI][] as `acidgenomics-cellosaurus`.
The import name is unchanged: `cellosaurus`.
We recommend using [uv][] to install.

```sh
uv add acidgenomics-cellosaurus
```

Or with [pip][]:

```sh
pip install acidgenomics-cellosaurus
```

### [Conda][] method

Configure [Conda][] to use the [Bioconda][] channels.

```sh
# Don't install recipe into base environment.
name='cellosaurus'
conda create --name="$name" "$name"
conda activate "$name"
python -c 'import cellosaurus'
```

## License

Apache-2.0 — Copyright 2026 Acid Genomics LLC — see [LICENSE](LICENSE).

[bioconda]: https://bioconda.github.io/
[conda]: https://docs.conda.io/
[pip]: https://pip.pypa.io/
[pypi]: https://pypi.org/project/acidgenomics-cellosaurus/
[python]: https://www.python.org/
[uv]: https://docs.astral.sh/uv/
