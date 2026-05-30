## ADDED Requirements

### Requirement: evidence-search 标注每条证据的属性（类型/一手二手/lane）
evidence-search 给每条结果打 ranking 时，MUST 额外标注三个属性，供上层综合阶段按「证据本身」而非「来源身份」论证：

- **证据类型**：`客观规格` / `独立测评` / `用户体验` / `厂商宣传` / `二手转述` 之一（领域相关——参数看规格/实测，体验看用户社区，排名看独立测评）
- **firsthand**：`true`（能追到原始数据 / 官方规格 / 原始实测）/ `false`（二手转述、"据说"）
- **lane**：`zh` / `en`（来自中文还是英文 lane）

这三个属性 MUST 写进每条 `evidence-search-NNN.md` 的 YAML front-matter，并在 `evidence-summary.md` 的来源表中各占一列。

**Lock**: user-confirmed
**Confirmed-At**: 2026-05-29

#### Scenario: front-matter 含证据属性
- **WHEN** evidence-search 写 evidence-search-001.md
- **THEN** front-matter 含 `evidence_type` / `firsthand` / `lane` 三字段（除原有 url/ranking/recommended/keywords）

#### Scenario: summary 来源表含属性列
- **WHEN** evidence-search 写 evidence-summary.md 的来源表
- **THEN** 表头含「证据类型 / 一手 / lane」列，每行如实填写，供综合阶段量化独立印证
