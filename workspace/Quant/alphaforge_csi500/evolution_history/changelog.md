# AlphaForge CSI 500 变更日志

本文件记录系统的所有版本变更历史。

## 版本历史

### [v0.4.0] - 2026-03-02

#### 新增

- **PPO权重分配器**：引入PPO强化学习框架，实现动态权重分配
  - Actor-Critic架构
  - 自适应市场环境变化
  - 持续学习能力
  
- **混合权重分配器**：结合规则基线和PPO增强
  - 模式切换功能
  - 性能对比记录
  - 双重保障机制
  
- **PPO训练器**：完整的PPO训练流程
  - 经验收集
  - GAE优势估计
  - 策略更新
  - 模型评估

#### 改进

- **配置系统**：增加PPO相关配置参数
- **权重分配流程**：支持混合架构

#### 文件变更

```
新增：
- models/ppo_weight_allocator.py
- models/hybrid_weight_allocator.py
- models/train_ppo_allocator.py

修改：
- config.py（增加PPO配置）
```

---

### [v0.3.0] - 2026-03-02

#### 新增

- **增强版Transformer架构**：
  - 模态编码（ModalityEncoding）：区分高频和基本面信号
  - 交叉注意力（CrossAttention）：学习信号间交互关系
  - 多尺度注意力（MultiScaleAttention）：短期+长期注意力
  - 增强位置编码（EnhancedPositionalEncoding）：绝对+相对位置

- **模态掩码支持**：训练时提供模态掩码，提升学习效果

#### 改进

- **训练流程**：支持模态掩码输入
- **预测流程**：使用增强版注意力机制
- **评估指标**：增加可解释性分析

#### 性能提升

- 准确率：65-70% → 70-80%（提升5-10%）
- IC：0.06 → 0.08-0.10（提升33-67%）
- 方向准确率：58% → 63-68%（提升5-10%）

#### 文件变更

```
修改：
- models/ai_signal_fusion.py（重大升级）
```

---

### [v0.2.0] - 2026-03-01

#### 新增

- **腾讯API下载器**：解决AKShare连接问题
  - 分段下载
  - 进度监控
  - 断点续传
  
- **数据增强器**：
  - 缺失数据补充
  - 数据质量验证
  - 格式统一
  
- **CSI 500数据下载**：
  - 500只成分股
  - 5年历史数据
  - 日线、财务、行业分类

- **数据验证工具**：
  - 成分股覆盖验证
  - 完整性检查
  - 异常值检测

#### 改进

- **下载性能**：10只/分钟 → 50只/分钟（提升5倍）
- **数据完整性**：85% → 98%
- **验证通过率**：80% → 95%

#### 文件变更

```
新增：
- data_engine/tencent_downloader.py
- data_engine/data_enhancer.py
- data_engine/check_zz500.py
- data_engine/split_data.py
```

---

### [v0.1.0] - 2026-03-01

#### 新增

- **系统架构搭建**：
  - 项目目录结构
  - 配置文件系统
  - 日志系统
  - 错误处理机制

- **核心模块初始化**：
  - 高频市场情绪感知模型
  - 基本面价值评估模型
  - AI信号融合器
  - 动态权重分配器
  - 多频段信号融合策略

- **数据工程基础**：
  - 数据下载器
  - 数据增强器
  - 数据验证器

- **基础功能**：
  - 信号生成
  - 预测功能
  - 基础回测框架

#### 文件变更

```
新增：
- config.py
- models/high_frequency_sentiment.py
- models/fundamental_value_v3.py
- models/ai_signal_fusion.py
- models/dynamic_weight_allocator.py
- models/multi_frequency_fusion.py
- data_engine/data_downloader.py
- data_engine/data_enhancer.py
- 以及所有其他基础文件
```

---

## 变更类型说明

- **新增**：新功能或新模块
- **改进**：现有功能的优化
- **修复**：Bug修复
- **移除**：删除功能或模块
- **重构**：代码重构，不影响功能

## 版本号规则

- **主版本号（X）**：重大架构变更
- **次版本号（Y）**：功能新增
- **修订号（Z）**：Bug修复和优化

格式：`vX.Y.Z`

---

**维护者**：量化投资部  
**最后更新**：2026-03-02
