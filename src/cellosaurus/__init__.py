"""Cellosaurus identifier mapping toolkit.

See Also
--------
- https://www.cellosaurus.org/
- https://ftp.expasy.org/databases/cellosaurus/
- https://github.com/calipho-sib/cellosaurus/
"""

from cellosaurus.cellosaurus import Cellosaurus
from cellosaurus.current_version import current_cellosaurus_version
from cellosaurus.standardize_cells import standardize_cells

__all__ = [
    "Cellosaurus",
    "current_cellosaurus_version",
    "standardize_cells",
]
