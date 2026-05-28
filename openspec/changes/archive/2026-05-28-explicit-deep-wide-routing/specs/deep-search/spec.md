## MODIFIED Requirements

### Requirement: deep-search 同 turn 并行派发
deep-search 在一轮内派多个 subagent 时 MUST 在同一 message 内一次性发起多个 Task 工具调用（并行），不是串行。派发前 MUST 先调 `TaskCreate` 注册任务。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 一轮派 3 个 evidence-search
- **WHEN** deep-search 第一轮要并行调研 3 个子主题
- **THEN** 3 个 Task 工具调用在同一 message 内发起；TaskCreate 已先注册 3 个任务

### Requirement: deep-search 派 subagent 时传 target 目录
deep-search 派下级 subagent 时 MUST 把目标目录传给下级（如 `<run_root>/deep-search/traces/evidence-search-<sid>/`），让下级在该目录内工作。这避免「一次 deep-search 的产物散落在多个 session-id 目录」。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-28

#### Scenario: 派 evidence-search 时传 target_dir
- **WHEN** deep-search 派 evidence-search
- **THEN** 调用参数包含 `target_dir=<run_root>/deep-search/traces/evidence-search-<sid>/`；下级产物落在该目录而非自己的 session-id 目录
