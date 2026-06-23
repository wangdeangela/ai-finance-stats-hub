# AI Finance & Statistics Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Problem:** Investors and analysts need one place to monitor an AI supply-chain watchlist, understand upstream/downstream bottlenecks, run rigorous return diagnostics, and apply correct statistical tests—with client-ready PDF output.

**Solution:** An integrated Python demo merging [financial-analysis-demo](https://github.com/bobooooo6868/financial-analysis-demo) with [stats-inference-toolkit](https://github.com/LIUYOUCecilia/stats-inference-toolkit), plus a rich **AI supply-chain map** explaining where each ticker sits in the value chain.

**Result:** A portfolio-ready repo with CLI, unified Streamlit dashboard, supply-chain diagram, offline demo fallback, pytest + CI, and basket-level inference.

## AI 产业链图谱

![AI Supply Chain Map](images/ai_supply_chain_map.png)

详细说明见 [docs/AI_SUPPLY_CHAIN.md](docs/AI_SUPPLY_CHAIN.md)（含 Mermaid 流程图）。

## Watchlist (7 tickers)

| Ticker | Role | Layer |
|--------|------|-------|
| **ASML** | ★ **Upstream bottleneck** — EUV lithography monopoly | 上游设备 |
| **TSM** | ★ **Midstream bottleneck** — advanced foundry & CoWoS packaging | 中游代工 |
| **NVDA** | ★ **Downstream bottleneck** — AI GPU compute (CUDA) | 算力芯片 |
| **AVGO** | Custom AI ASIC, networking & high-speed interconnect | 芯片/互联 |
| **VRT** | Data-center power, cooling & rack infrastructure | 基础设施 |
| **GOOGL** | AI cloud, foundation models & enterprise AI | 下游应用 |
| **SLV** | Precious-metal hedge / macro diversifier | 宏观对冲 |

## Highlights

| Module | Features |
|--------|----------|
| **Supply Chain Map** | Layered upstream→application diagram, bottleneck markers, node glossary |
| **Portfolio Dashboard** | yfinance fetch, correlation, rolling vol, JB/ADF tests, charts |
| **Basket Inference** | AI chain vs SLV hedge → auto t-test/ANOVA → PDF |
| **A/B Stats Toolkit** | CSV upload → assumption checks → Z/t/Welch/MWU/ANOVA/Chi² → PDF |

## Quick Start

```bash
cd ai-finance-stats-hub
chmod +x setup.sh && ./setup.sh --demo
streamlit run app.py
```

## Commands

| Command | Purpose |
|---------|---------|
| `python main.py --demo` | Portfolio pipeline + charts + supply-chain map |
| `streamlit run app.py` | Unified dashboard (map + portfolio + inference + A/B) |
| `pytest tests/` | Unit tests |

## Data Notes

- Market data via [yfinance](https://github.com/ranaroussi/yfinance) (delayed; education/research only).
- Use **Use demo data** when offline or rate-limited.

## License

MIT License
