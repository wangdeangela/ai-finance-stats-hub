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
        "role": "Application — AI cloud, foundation models & enterprise AI services",
        "basket": "ai_platform",
        "layer": "application",
        "chain_position": "downstream",
    },
    "VRT": {
        "name": "Vertiv",
        "role": "Infrastructure — data-center power, cooling & rack PDUs",
        "basket": "ai_infra",
        "layer": "infrastructure",
        "chain_position": "midstream",
    },
    "SLV": {
        "name": "iShares Silver Trust",
        "role": "Macro hedge — precious-metal diversifier vs tech beta",
        "basket": "hedge",
        "layer": "hedge",
        "chain_position": "hedge",
    },
    "AVGO": {
        "name": "Broadcom",
        "role": "Silicon — custom AI ASIC, networking & high-speed interconnect",
        "basket": "ai_infra",
        "layer": "chip_design",
        "chain_position": "midstream",
    },
    "ASML": {
        "name": "ASML",
        "role": "Bottleneck — EUV lithography (global monopoly on advanced nodes)",
        "basket": "bottleneck_upstream",
        "layer": "equipment",
        "chain_position": "upstream",
    },
    "TSM": {
        "name": "TSMC",
        "role": "Bottleneck — advanced foundry (CoWoS packaging, 3nm/2nm AI chips)",
        "basket": "bottleneck_midstream",
        "layer": "foundry",
        "chain_position": "midstream",
    },
    "NVDA": {
        "name": "NVIDIA",
        "role": "Bottleneck — AI GPU compute (CUDA ecosystem & HBM bandwidth)",
        "basket": "bottleneck_downstream",
        "layer": "compute",
        "chain_position": "downstream",
    },
}

# Rich supply-chain layer definitions for the industry map diagram
SUPPLY_CHAIN_LAYERS: list[dict] = [
    {
        "id": "upstream",
        "label": "上游 · Upstream",
        "color": "#1e3a5f",
        "nodes": [
            {"id": "wafers", "short": "Wafer", "name": "高纯硅晶圆 / Silicon Wafers", "watch": None},
            {"id": "gas", "short": "Gas", "name": "光刻胶 & 特种气体", "watch": None},
            {"id": "eda", "short": "EDA", "name": "EDA 设计软件 (Synopsys/Cadence)", "watch": None},
            {"id": "asml", "short": "EUV", "name": "EUV 光刻机", "watch": "ASML", "bottleneck": True},
            {"id": "equip", "short": "Etch", "name": "刻蚀 / 沉积 / 检测设备", "watch": None},
        ],
    },
    {
        "id": "midstream",
        "label": "中游 · Midstream",
        "color": "#2563eb",
        "nodes": [
            {"id": "design", "short": "ASIC", "name": "芯片设计 IP & 定制 ASIC", "watch": "AVGO"},
            {"id": "gpu", "short": "GPU", "name": "GPU / AI 加速器架构", "watch": "NVDA", "bottleneck": True},
            {"id": "foundry", "short": "Fab", "name": "先进制程代工 (3nm/2nm)", "watch": "TSM", "bottleneck": True},
            {"id": "hbm", "short": "HBM", "name": "HBM 高带宽存储", "watch": None},
            {"id": "cowos", "short": "CoWoS", "name": "CoWoS 先进封装", "watch": "TSM", "bottleneck": True},
            {"id": "interconnect", "short": "CXL", "name": "高速互联 (CXL / NVLink)", "watch": "AVGO"},
        ],
    },
    {
        "id": "infrastructure",
        "label": "算力基础设施 · Infrastructure",
        "color": "#7c3aed",
        "nodes": [
            {"id": "server", "short": "Rack", "name": "AI 服务器 & 机架", "watch": None},
            {"id": "power", "short": "UPS", "name": "数据中心供电 & UPS", "watch": "VRT"},
            {"id": "cool", "short": "Cool", "name": "液冷 / 精密空调", "watch": "VRT"},
            {"id": "net", "short": "Net", "name": "高速光模块 & 网络交换机", "watch": "AVGO"},
        ],
    },
    {
        "id": "application",
        "label": "下游应用 · Application",
        "color": "#059669",
        "nodes": [
            {"id": "cloud", "short": "Cloud", "name": "公有云 AI 算力", "watch": "GOOGL"},
            {"id": "llm", "short": "LLM", "name": "基础大模型训练 & 推理", "watch": "GOOGL"},
            {"id": "agent", "short": "Agent", "name": "企业 AI Agent / 搜索", "watch": "GOOGL"},
            {"id": "vert", "short": "Vert", "name": "行业垂直 AI 解决方案", "watch": None},
        ],
    },
    {
        "id": "hedge",
        "label": "宏观对冲 · Hedge",
        "color": "#b45309",
        "nodes": [
            {"id": "slv_etf", "short": "SLV", "name": "白银 / 贵金属 ETF", "watch": "SLV"},
            {"id": "slv_beta", "short": "Hedge", "name": "低相关性资产分散科技贝塔", "watch": "SLV"},
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
