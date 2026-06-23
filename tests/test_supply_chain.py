"""Tests for supply chain map."""

from pathlib import Path

from src.config import IMAGES_DIR
from src.finance.supply_chain_map import plot_supply_chain_map


def test_supply_chain_map_generates_png(tmp_path, monkeypatch):
    monkeypatch.setattr("src.finance.supply_chain_map.IMAGES_DIR", tmp_path)
    path = plot_supply_chain_map(save=True)
    assert isinstance(path, Path)
    assert path.exists()
    assert path.suffix == ".png"
