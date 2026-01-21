import importlib.util

import pytest

from echoed.data import BdfDependencyError, load_bdf


def test_load_bdf_requires_dependency(tmp_path):
    if importlib.util.find_spec("bdf") is not None:
        pytest.skip("bdf is installed; dependency error is not expected.")

    dummy_bdf = tmp_path / "dummy.bdf"
    dummy_bdf.write_text("placeholder", encoding="utf-8")

    with pytest.raises(BdfDependencyError) as exc:
        load_bdf(dummy_bdf)

    assert "echoed[bdf]" in str(exc.value)
