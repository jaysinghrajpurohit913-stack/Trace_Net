import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def demo():
    from tracenet.importer import load_demo
    return load_demo(str(ROOT / "data"))


@pytest.fixture(scope="session")
def an(demo):
    from tracenet.pipeline import run_analysis
    return run_analysis(demo)
