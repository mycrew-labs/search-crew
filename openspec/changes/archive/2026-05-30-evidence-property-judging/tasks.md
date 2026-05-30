## 1. evidence-search 采集标注

- [x] 1.1 agents/evidence-search.md：front-matter 模板加 `evidence_type` / `firsthand` / `lane` 三字段 + 取值说明
- [x] 1.2 evidence-summary.md 模板的来源表加「证据类型 / 一手 / lane」列
- [x] 1.3 工作流里加一步「判定每条的证据类型与一手/二手」

## 2. deep-search 综合阶段质量标准

- [x] 2.1 agents/deep-search.md 综合阶段加「报告质量标准」6 条（证据类型决定可信度 / 独立印证量化 / 一手优先 / 冲突裁决 / 场景化支撑数据 / 反茧房异常段）
- [x] 2.2 report.md 模板示例体现：独立印证数标注、异常信号段

## 3. wide-search 综合阶段质量标准

- [x] 3.1 agents/wide-search.md 综合阶段：矩阵格标证据属性 + 异常信号段

## 4. 验证 + 归档

- [x] 4.1 `openspec validate evidence-property-judging --strict`
- [ ] 4.2 完工简报 + 锁确认（evidence/deep/wide 三条新需求）
- [ ] 4.3 bump version → archive → commit → push
- [ ] 4.4 **manual** 实测：跑一次 /search-deep，报告含独立印证数 + 异常段 + 证据类型标注
