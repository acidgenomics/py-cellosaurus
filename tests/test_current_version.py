"""Tests for cellosaurus.current_version."""

import pytest

from cellosaurus.current_version import current_cellosaurus_version


@pytest.mark.network
def test_current_version() -> None:
    """Requires network access."""
    version = current_cellosaurus_version()
    assert isinstance(version, str)
    assert len(version) > 0
