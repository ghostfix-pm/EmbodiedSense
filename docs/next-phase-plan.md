# 下一阶段：纪律与评测口径

> 本文补充 [roadmap.md](roadmap.md)。roadmap 回答"接下来做哪些功能"，本文回答两个问题：
> **做这些事时不能违反什么**，以及**结果怎么才算数**。

## 1. 立足点：外部工具链实测

见 [工具链集成对照表](toolchain-integration-matrix.md)。摘要：

| 工具 | 对同一份注入 8 种故障的数据 | 备注 |
|---|---|---|
| physlint 0.3.2 | **检出 0 / 8** | 干净数据与故障数据报告逐条一致 |
| embodied-sync 0.1.3 | **1 / 8，且漏报** | 报 cam_front 缺 1 帧，真值为 7 帧 |
| bagx 0.6.0 | 未测 | 需 rosbag2 输入；**已自带 `mcp` 与 `ask`** |
| hflow 0.2.21 | 无法运行 | Windows 下缺 `fcntl`（Linux-only） |

交接层面的实测缺陷：`export-lerobot` **丢弃全部相机/事件流**（7 条流变 3 条）；流命名不匹配（`actions`/`robot_state` vs `action`/`observation.state`）导致**干净数据被判 2 条 error**；`embsync --adapter mcap` 产出的不是二进制 MCAP。

**含义：本项目不重写检查规则，只补工具之间的缝隙。**

## 2. 不做（每条都有实测依据）

| ❌ 不做 | 依据 |
|---|---|
| 自研检测规则 | physlint 已装 32 条确定性规则 |
| 自研故障注入引擎 | `embsync corrupt` 的 8 类故障 schema 已完备 |
| 通用 MCP 框架 | `bagx mcp` 已存在；只做统一报告封装 |
| 不透明的单一质量总分 | physlint 明确拒绝该做法，且无法定位问题 |
| 修改或"修复"源数据 | 全链路只读；上游工具同样如此设计 |

## 3. 要做（三条增量，均不改动 MVP 1 的核心 API）

1. **交接保真。** 把上游多流数据导出成**合规且含视频**的 LeRobot 数据集，使下游工具的规则真正能运行。
   *可验证指标：* physlint 的 `video.decode` / `video.frozen_frames` / `video.black_frames` 由 `not_run` 变为实际执行；干净数据 `exit=0`；故障数据检出由 0/8 提升到 ≥3/8。
2. **统一 finding 口径。** 把不同工具的结论归一成同一语义（来源工具 / 规则 ID / 严重度 / 位置 / 证据 / 建议），使跨工具结果可并列、可对比、可归档。这是目前唯一必须自研的部分。
3. **因果验证。** 见下方模板。roadmap 第 3 项已提出该实验方向，本文补充其**判定口径**。

## 4. Evaluation 预注册模板（**跑实验之前必须提交**）

用 Git 提交时间戳证明预注册先于实验。缺少预注册的结果不得用于任何结论。

```
实验编号：
假设：上游质量指标能预测下游策略性能退化，且预测力强于"训练数据量"这一简单基线。
自变量：故障类型（dropped_frames / clock_drift / jitter / missing_interval）
        × 严重度 5 档（clean / 轻微 / 中等 / 严重 / 极严重）
因变量：任务成功率（固定测试 episode 数）、训练步数、推理时延
控制变量：策略架构、超参、训练步数、随机种子（每档 ≥3）、硬件
判定阈值（先说死）：
  - 成立：严重档成功率相对 clean 下降 ≥15 个百分点，且质量指标与成功率的 Spearman ρ ≥ 0.7
  - 不成立：下降 <5 个百分点 → 报告"清洗的边际价值低"（同样是有效结论）
必须报告：失败与无显著差异的结果、每个 seed 的原始数据、机器可读 CSV
禁止：事后挑选指标、事后剔除 seed、只报告最好的一组
公平性：若本方法使用了额外传感器信息，必须另设获得相同信息的基线，
        否则不得把收益归因于本项目的处理流程。
```

## 5. 与 MVP 1 的关系

MVP 1 是**单传感器（RGB-D）链路**，已完成并验收（见 [verification.md](verification.md)）。本文三条属于**跨工具、跨传感器**层面的补充，不修改 `core/pipeline.py` 的公共接口，也不引入 Rerun / ROS / GPU 依赖。

可复现输入：故障注入配置位于 [`benchmarks/integration/profiles/kitchen_sink.yaml`](../benchmarks/integration/profiles/kitchen_sink.yaml)；工具链准备与复现命令见对照表 §6。
