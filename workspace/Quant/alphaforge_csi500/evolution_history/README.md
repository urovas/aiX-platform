# AlphaForge CSI 500 系统进化历史

本目录记录 AlphaForge CSI 500 指数增强系统的版本更新和进化历程。

## 目录结构

```
evolution_history/
├── README.md                    # 本文件
├── versions/                    # 版本记录
│   ├── v0.1.0_initial.md       # 初始版本
│   ├── v0.2.0_data_enhancement.md  # 数据增强版本
│   ├── v0.3.0_transformer_enhanced.md  # Transformer增强版本
│   ├── v0.4.0_ppo_allocator.md  # PPO权重分配器版本
│   └── ...
├── milestones/                  # 里程碑记录
│   ├── 2026-02-22_system_init.md
│   ├── 2026-02-22_data_ready.md
│   └── ...
└── changelog.md                 # 变更日志汇总

```

## 版本命名规范

- **主版本号（X）**：重大架构变更
- **次版本号（Y）**：功能新增
- **修订号（Z）**：Bug修复和优化

格式：`vX.Y.Z`

## 当前版本

**v0.4.0** - 权重模块整合 + 高频交易优化

## 版本历史概览

| 版本 | 日期 | 主要特性 | 状态 |
|------|------|---------|------|
| v0.1.0 | 2026-02-22 | 系统初始化，基础架构搭建 | ✅ 已完成 |
| v0.2.0 | 2026-03-01 | 数据工程体系，CSI 500数据下载 | ✅ 已完成 |
| v0.3.0 | 2026-03-02 | 增强版Transformer，模态编码、交叉注意力 | ✅ 已完成 |
| v0.4.0 | 2026-03-02 | 权重模块整合(4合1)，高频优化(2.5-5ms响应) | ✅ 已完成 |
| v0.5.0 | 计划中 | 数据获取，模型训练，回测验证 | 🔄 计划中 |
| v1.0.0 | 计划中 | QMT接入，模拟交易，实盘部署 | 🔄 计划中 |

## 如何查看历史版本

1. 查看特定版本详情：`versions/vX.Y.Z_description.md`
2. 查看变更日志：`changelog.md`
3. 查看里程碑：`milestones/YYYY-MM-DD_event.md`

## 贡献指南

添加新版本时，请遵循以下步骤：

1. 创建版本文档：`versions/vX.Y.Z_feature.md`
2. 更新 `changelog.md`
3. 如有里程碑，创建 `milestones/YYYY-MM-DD_event.md`
4. 更新本 README 的版本历史概览

---

**维护者**：量化投资部  
**最后更新**：2026-03-02
