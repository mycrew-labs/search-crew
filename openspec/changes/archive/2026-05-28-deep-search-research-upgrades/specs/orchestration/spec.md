## ADDED Requirements

### Requirement: 主 agent 派 deep-search 前对明显歧义做非阻塞澄清
主 agent（`/search-deep` 流程）在派出 deep-search **之前**，若 topic 有明显歧义 / 范围过宽，MUST 先向用户发**一句话**澄清（含一个合理默认）；**非阻塞**——用户不答则按言明的默认继续派发。topic 已清晰时 MUST NOT 多问（默认静默）。此澄清在派发前做，因为 deep-search 是 subagent，跑起来后无法与用户来回交互。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 明显歧义先一句话澄清
- **WHEN** 用户 `/search-deep 调研 transformer`（范围过宽 / 歧义）
- **THEN** 主 agent 派 deep-search 前先问一句（如「你要的是模型架构、还是 Transformers 库用法？默认我按模型架构全面查」），用户不答则按默认派发

#### Scenario: 清晰 topic 不打扰
- **WHEN** 用户 `/search-deep 对比 vLLM 与 TensorRT-LLM 的吞吐与显存`（已清晰）
- **THEN** 主 agent 不额外提问，直接派 deep-search
