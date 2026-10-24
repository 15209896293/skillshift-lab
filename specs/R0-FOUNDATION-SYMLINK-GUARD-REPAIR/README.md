# R0-FOUNDATION-SYMLINK-GUARD-REPAIR：根路径符号链接检查修复

## 状态

- Task ID：`R0-FOUNDATION-SYMLINK-GUARD-REPAIR`
- 类型：BUG / 安全 Spike 修复
- 状态：Implemented / PARTIAL（2026-09-24）。

## 目标与范围

修复 Gate 1 QA 发现的静态缺口：`LocalRestrictedProcessProvider` 不得在检查传入 Workspace root 是否为符号链接之前先调用 `resolve()`。新增仅验证调用顺序的回归测试。

允许修改：`execution/providers/local_restricted_process.py`、`tests/test_foundation_spike.py`、本规格和 `artifacts/R0-FOUNDATION-SPIKE/` 的修复报告。

## 非目标与停止条件

本修复不创建符号链接、不启用 Developer Mode、不修改权限、不验证 junction/reparse point 或 TOCTOU，也不关闭 FS-02。若测试需要实际创建符号链接或触及临时目录外路径，即停止并保留为 PARTIAL。
