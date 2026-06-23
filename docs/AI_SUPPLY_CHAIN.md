# AI Supply Chain Map

This project's watchlist covers key nodes across the AI value chain-from **upstream equipment** through **downstream applications**-with three structural bottleneck stocks highlighted.

## Overview

![AI Supply Chain Map](../images/ai_supply_chain_map.png)

> Regenerate with `python main.py --demo` or `python -c "from src.finance.supply_chain_map import plot_supply_chain_map; plot_supply_chain_map()"`.

## Mermaid Flow Diagram

```mermaid
flowchart LR
    subgraph UP["Upstream"]
        WAFER["High-purity silicon wafers"]
        GAS["Photoresist / specialty gases"]
        EDA["EDA design software"]
        ASML["* EUV lithography<br/><b>ASML</b>"]
        EQUIP["Etch / deposition / inspection"]
    end

    subgraph MID["Midstream"]
        DESIGN["Chip design IP / custom ASIC<br/><b>AVGO</b>"]
        GPU["* GPU / AI accelerators<br/><b>NVDA</b>"]
        FOUNDRY["* Advanced foundry 3nm/2nm<br/><b>TSM</b>"]
        HBM["HBM high-bandwidth memory"]
        COWOS["* CoWoS advanced packaging<br/><b>TSM</b>"]
        INTERCONNECT["High-speed interconnect CXL/NVLink<br/><b>AVGO</b>"]
    end

    subgraph INFRA["Compute Infrastructure"]
        SERVER["AI servers / racks"]
        POWER["Data-center power & UPS<br/><b>VRT</b>"]
        COOL["Liquid cooling / precision HVAC<br/><b>VRT</b>"]
        NET["Optical modules / network switches<br/><b>AVGO</b>"]
    end

    subgraph APP["Application"]
        CLOUD["Public cloud AI compute<br/><b>GOOGL</b>"]
        LLM["Foundation model training & inference<br/><b>GOOGL</b>"]
        AGENT["Enterprise AI agents / search<br/><b>GOOGL</b>"]
        VERT["Vertical industry AI"]
    end

    subgraph HEDGE["Macro Hedge"]
        SLV["Silver ETF<br/><b>SLV</b>"]
    end

    WAFER --> FOUNDRY
    GAS --> ASML
    EDA --> DESIGN
    ASML --> FOUNDRY
    EQUIP --> FOUNDRY
    DESIGN --> GPU
    DESIGN --> FOUNDRY
    FOUNDRY --> COWOS
    HBM --> COWOS
    COWOS --> GPU
    GPU --> SERVER
    INTERCONNECT --> NET
    SERVER --> POWER
    POWER --> COOL
    NET --> CLOUD
    SERVER --> CLOUD
    CLOUD --> LLM
    LLM --> AGENT
    AGENT --> VERT
    MID -.->|Diversify tech beta| HEDGE
```

## Watchlist (7 tickers)

| Ticker | Company | Chain position | Bottleneck? |
|--------|---------|----------------|-------------|
| **ASML** | ASML | Upstream - EUV lithography equipment | * Global monopoly on advanced-node equipment |
| **TSM** | TSMC | Midstream - advanced foundry & CoWoS packaging | * High-end AI chip capacity constraint |
| **NVDA** | NVIDIA | Midstream/downstream - GPU compute | * CUDA ecosystem + HBM bandwidth |
| **AVGO** | Broadcom | Midstream - custom ASIC & high-speed interconnect | Key silicon / networking node |
| **VRT** | Vertiv | Infrastructure - power & cooling | AI data-center necessity |
| **GOOGL** | Alphabet | Downstream - cloud + foundation models | Application-layer representative |
| **SLV** | Silver ETF | Macro hedge | Low-correlation diversifier |

## Three bottleneck stocks - rationale

1. **ASML (upstream)** - Sole manufacturer of production EUV lithography systems; advanced nodes (below 7nm) are nearly irreplaceable.
2. **TSM (midstream)** - Concentration of the world's most advanced foundry capacity; CoWoS packaging caps AI GPU shipments.
3. **NVDA (downstream compute)** - Leading share in AI training/inference GPUs; software stack (CUDA) creates ecosystem lock-in.

## Link to project analytics

- **Portfolio Dashboard -> Supply Chain Map**: Interactive diagram + layered node table
- **Basket Inference**: Group by upstream/midstream/downstream bottlenecks or AI chain vs SLV hedge for hypothesis tests
- **Correlation matrix**: Examine correlation structure among bottleneck names and the SLV hedge
