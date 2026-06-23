"""Tests for supply chain map."""

from pathlib import Path

from src.config import (
    IMAGES_DIR,
    SUPPLY_CHAIN_LAYERS,
    SUPPLY_CHAIN_NODE_EDGES,
    SUPPLY_CHAIN_TICKER_EDGES,
    TICKERS,
)
from src.finance.analysis import correlation_matrix, daily_returns
from src.finance.data_fetch import load_demo_prices
from src.finance.supply_chain_map import (
    build_correlation_weighted_edges,
    plot_supply_chain_coursemap,
    plot_supply_chain_map,
    plot_supply_chain_sankey,
)


def test_supply_chain_node_edges_reference_valid_nodes():
    node_ids = {node["id"] for layer in SUPPLY_CHAIN_LAYERS for node in layer["nodes"]}
    for source, target in SUPPLY_CHAIN_NODE_EDGES:
        assert source in node_ids
        assert target in node_ids


def test_supply_chain_map_generates_png(tmp_path, monkeypatch):
    monkeypatch.setattr("src.finance.supply_chain_map.IMAGES_DIR", tmp_path)
    path = plot_supply_chain_map(save=True)
    assert isinstance(path, Path)
    assert path.exists()
    assert path.suffix == ".png"


def test_plot_supply_chain_coursemap_returns_interactive_figure():
    prices = load_demo_prices()
    corr = correlation_matrix(daily_returns(prices))
    fig = plot_supply_chain_coursemap(corr, layer_filter="all")
    assert fig.data
    assert any(trace.name == "nodes" for trace in fig.data)


def test_build_correlation_weighted_edges_uses_supply_chain_topology():
    prices = load_demo_prices()
    corr = correlation_matrix(daily_returns(prices))
    edges = build_correlation_weighted_edges(corr)

    assert len(edges) == len(SUPPLY_CHAIN_TICKER_EDGES)
    assert set(edges["source"]) | set(edges["target"]) <= set(TICKERS)
    assert edges["correlation"].between(-1, 1).all()
    assert (edges["abs_correlation"] == edges["correlation"].abs()).all()


def test_plot_supply_chain_sankey_returns_figure():
    prices = load_demo_prices()
    corr = correlation_matrix(daily_returns(prices))
    fig = plot_supply_chain_sankey(corr)

    assert fig.data
    sankey = fig.data[0]
    assert len(sankey.link.value) == len(SUPPLY_CHAIN_TICKER_EDGES)
    assert len(sankey.node.label) == len({t for pair in SUPPLY_CHAIN_TICKER_EDGES for t in pair})
