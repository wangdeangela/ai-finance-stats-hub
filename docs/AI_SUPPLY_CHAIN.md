# AI 产业链上下游图谱

本项目的 watchlist 覆盖 AI 产业链从**上游设备**到**下游应用**的关键节点，并标注三大结构性瓶颈股。

## 图谱总览

![AI Supply Chain Map](images/ai_supply_chain_map.png)

> 运行 `python main.py --demo` 或 `python -c "from src.finance.supply_chain_map import plot_supply_chain_map; plot_supply_chain_map()"` 可重新生成此图。

## Mermaid 流程图

```mermaid
flowchart TB
    subgraph UP["上游 Upstream"]
        WAFER["高纯硅晶圆"]
        GAS["光刻胶 / 特种气体"]
        EDA["EDA 设计软件"]
        ASML["★ EUV 光刻机<br/><b>ASML</b>"]
        EQUIP["刻蚀 / 沉积 / 检测"]
    end

    subgraph MID["中游 Midstream"]
        DESIGN["芯片设计 IP / 定制 ASIC<br/><b>AVGO</b>"]
        GPU["★ GPU / AI 加速器<br/><b>NVDA</b>"]
        FOUNDRY["★ 先进制程代工 3nm/2nm<br/><b>TSM</b>"]
        HBM["HBM 高带宽存储"]
        COWOS["★ CoWoS 先进封装<br/><b>TSM</b>"]
        INTERCONNECT["高速互联 CXL/NVLink<br/><b>AVGO</b>"]
    end

    subgraph INFRA["算力基础设施 Infrastructure"]
        SERVER["AI 服务器 / 机架"]
        POWER["数据中心供电 UPS<br/><b>VRT</b>"]
        COOL["液冷 / 精密空调<br/><b>VRT</b>"]
        NET["光模块 / 网络交换机<br/><b>AVGO</b>"]
    end

    subgraph APP["下游应用 Application"]
        CLOUD["公有云 AI 算力<br/><b>GOOGL</b>"]
        LLM["大模型训练 & 推理<br/><b>GOOGL</b>"]
        AGENT["企业 AI Agent / 搜索<br/><b>GOOGL</b>"]
        VERT["行业垂直 AI"]
    end

    subgraph HEDGE["宏观对冲 Hedge"]
        SLV["白银 ETF<br/><b>SLV</b>"]
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

    MID -.->|分散科技贝塔| HEDGE
```

## Watchlist 标的（7 支）

| 代码 | 公司 | 产业链位置 | 是否瓶颈 |
|------|------|-----------|---------|
| **ASML** | ASML | 上游 — EUV 光刻设备 | ★ 全球先进制程设备垄断 |
| **TSM** | 台积电 | 中游 — 先进代工 & CoWoS 封装 | ★ 高端 AI 芯片产能瓶颈 |
| **NVDA** | NVIDIA | 中游/下游 — GPU 算力 | ★ CUDA 生态 + HBM 带宽 |
| **AVGO** | Broadcom | 中游 — 定制 ASIC & 高速互联 | 关键硅片/网络节点 |
| **VRT** | Vertiv | 基础设施 — 电力/散热 | AI 数据中心刚需 |
| **GOOGL** | Alphabet | 下游 — 云 + 大模型 | 应用层代表 |
| **SLV** | 白银 ETF | 宏观对冲 | 低相关性分散 |

## 三大瓶颈股逻辑

1. **ASML（上游）** — 唯一能量产 EUV 光刻机的厂商，先进制程（7nm 以下）几乎不可替代。
2. **TSM（中游）** — 全球最先进代工产能集中，CoWoS 封装决定 AI GPU 出货上限。
3. **NVDA（下游算力）** — AI 训练/推理 GPU 市占率领先，软件栈（CUDA）形成生态锁定。

## 与本项目分析的关联

- **Portfolio Dashboard → Supply Chain Map**：交互式图谱 + 分层节点表
- **Basket Inference**：可按「上游/中游/下游瓶颈」或「AI 链 vs SLV 对冲」分组做假设检验
- **相关性矩阵**：观察瓶颈股之间及与 SLV 对冲标的的相关结构
