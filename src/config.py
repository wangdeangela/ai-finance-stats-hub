"""Project constants for the integrated finance + statistics demo."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DEMO_PRICES_PATH = PROCESSED_DIR / "prices_wide_demo.csv"
IMAGES_DIR = PROJECT_ROOT / "images"
REPORTS_DIR = PROJECT_ROOT / "reports"
DEMO_DATA_DIR = PROJECT_ROOT / "demo_data"

# AI supply-chain watchlist (7 tickers)
TICKERS = ["GOOGL", "VRT", "SLV", "AVGO", "ASML", "TSM", "NVDA"]

TICKER_META: dict[str, dict[str, str]] = {
    "GOOGL": {
        "name": "Alphabet",
        "role": "Application - AI cloud, foundation models & enterprise AI services",
        "basket": "ai_platform",
        "layer": "application",
        "chain_position": "downstream",
    },
    "VRT": {
        "name": "Vertiv",
        "role": "Infrastructure - data-center power, cooling & rack PDUs",
        "basket": "ai_infra",
        "layer": "infrastructure",
        "chain_position": "midstream",
    },
    "SLV": {
        "name": "iShares Silver Trust",
        "role": "Macro hedge - precious-metal diversifier vs tech beta",
        "basket": "hedge",
        "layer": "hedge",
        "chain_position": "hedge",
    },
    "AVGO": {
        "name": "Broadcom",
        "role": "Silicon - custom AI ASIC, networking & high-speed interconnect",
        "basket": "ai_infra",
        "layer": "chip_design",
        "chain_position": "midstream",
    },
    "ASML": {
        "name": "ASML",
        "role": "Bottleneck - EUV lithography (global monopoly on advanced nodes)",
        "basket": "bottleneck_upstream",
        "layer": "equipment",
        "chain_position": "upstream",
    },
    "TSM": {
        "name": "TSMC",
        "role": "Bottleneck - advanced foundry (CoWoS packaging, 3nm/2nm AI chips)",
        "basket": "bottleneck_midstream",
        "layer": "foundry",
        "chain_position": "midstream",
    },
    "NVDA": {
        "name": "NVIDIA",
        "role": "Bottleneck - AI GPU compute (CUDA ecosystem & HBM bandwidth)",
        "basket": "bottleneck_downstream",
        "layer": "compute",
        "chain_position": "downstream",
    },
}

# Rich supply-chain layer definitions for the industry map diagram
SUPPLY_CHAIN_LAYERS: list[dict] = [
    {
        "id": "upstream",
        "label": "Upstream",
        "color": "#1e3a5f",
        "nodes": [
            {"id": "wafers", "short": "Wafer", "name": "High-purity silicon wafers", "watch": None},
            {"id": "gas", "short": "Gas", "name": "Photoresist & specialty gases", "watch": None},
            {"id": "eda", "short": "EDA", "name": "EDA design software (Synopsys/Cadence)", "watch": None},
            {"id": "asml", "short": "EUV", "name": "EUV lithography systems", "watch": "ASML", "bottleneck": True},
            {"id": "equip", "short": "Etch", "name": "Etch / deposition / inspection equipment", "watch": None},
        ],
    },
    {
        "id": "midstream",
        "label": "Midstream",
        "color": "#2563eb",
        "nodes": [
            {"id": "design", "short": "ASIC", "name": "Chip design IP & custom ASIC", "watch": "AVGO"},
            {"id": "gpu", "short": "GPU", "name": "GPU / AI accelerator architecture", "watch": "NVDA", "bottleneck": True},
            {"id": "foundry", "short": "Fab", "name": "Advanced foundry (3nm/2nm)", "watch": "TSM", "bottleneck": True},
            {"id": "hbm", "short": "HBM", "name": "HBM high-bandwidth memory", "watch": None},
            {"id": "cowos", "short": "CoWoS", "name": "CoWoS advanced packaging", "watch": "TSM", "bottleneck": True},
            {"id": "interconnect", "short": "CXL", "name": "High-speed interconnect (CXL / NVLink)", "watch": "AVGO"},
        ],
    },
    {
        "id": "infrastructure",
        "label": "Infrastructure",
        "color": "#7c3aed",
        "nodes": [
            {"id": "server", "short": "Rack", "name": "AI servers & racks", "watch": None},
            {"id": "power", "short": "UPS", "name": "Data-center power & UPS", "watch": "VRT"},
            {"id": "cool", "short": "Cool", "name": "Liquid cooling / precision HVAC", "watch": "VRT"},
            {"id": "net", "short": "Net", "name": "High-speed optical modules & network switches", "watch": "AVGO"},
        ],
    },
    {
        "id": "application",
        "label": "Application",
        "color": "#059669",
        "nodes": [
            {"id": "cloud", "short": "Cloud", "name": "Public cloud AI compute", "watch": "GOOGL"},
            {"id": "llm", "short": "LLM", "name": "Foundation model training & inference", "watch": "GOOGL"},
            {"id": "agent", "short": "Agent", "name": "Enterprise AI agents / search", "watch": "GOOGL"},
            {"id": "vert", "short": "Vert", "name": "Vertical industry AI solutions", "watch": None},
        ],
    },
    {
        "id": "hedge",
        "label": "Hedge",
        "color": "#b45309",
        "nodes": [
            {"id": "slv_etf", "short": "SLV", "name": "Silver / precious-metal ETF", "watch": "SLV"},
            {"id": "slv_beta", "short": "Hedge", "name": "Low-correlation diversifier vs tech beta", "watch": "SLV"},
        ],
    },
]

# Process-flow edges between industry nodes (prerequisite-style topology)
SUPPLY_CHAIN_NODE_EDGES: list[tuple[str, str]] = [
    ("wafers", "foundry"),
    ("gas", "asml"),
    ("eda", "design"),
    ("asml", "foundry"),
    ("equip", "foundry"),
    ("design", "gpu"),
    ("design", "foundry"),
    ("foundry", "cowos"),
    ("hbm", "cowos"),
    ("cowos", "gpu"),
    ("gpu", "server"),
    ("interconnect", "net"),
    ("server", "power"),
    ("power", "cool"),
    ("net", "cloud"),
    ("server", "cloud"),
    ("cloud", "llm"),
    ("llm", "agent"),
    ("agent", "vert"),
    ("foundry", "slv_beta"),
]

AI_CHAIN_TICKERS = [t for t, m in TICKER_META.items() if m["basket"] != "hedge"]
HEDGE_TICKERS = [t for t, m in TICKER_META.items() if m["basket"] == "hedge"]
BOTTLENECK_TICKERS = [
    t for t, m in TICKER_META.items() if m["basket"].startswith("bottleneck")
]

# Logical supply-chain links between watchlist tickers (used for correlation-weighted Sankey)
SUPPLY_CHAIN_TICKER_EDGES: list[tuple[str, str]] = [
    ("ASML", "TSM"),
    ("ASML", "AVGO"),
    ("AVGO", "TSM"),
    ("AVGO", "NVDA"),
    ("TSM", "NVDA"),
    ("NVDA", "VRT"),
    ("AVGO", "VRT"),
    ("VRT", "GOOGL"),
    ("NVDA", "GOOGL"),
    ("TSM", "SLV"),
]

TICKER_LAYER_COLORS: dict[str, str] = {
    "equipment": "#1e3a5f",
    "chip_design": "#2563eb",
    "foundry": "#2563eb",
    "compute": "#7c3aed",
    "infrastructure": "#7c3aed",
    "application": "#059669",
    "hedge": "#b45309",
}

PERIOD = "2y"
ROLLING_SHORT = 20
ROLLING_LONG = 60
