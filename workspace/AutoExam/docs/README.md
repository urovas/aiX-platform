# AutoExam - 自动驾驶高危场景智能生成与测试系统

## 项目概述

AutoExam是一个专注于自动驾驶高危场景智能生成与测试的系统，旨在帮助开发者和测试人员发现自动驾驶系统在极端情况下的潜在问题，提高系统的安全性和可靠性。

### 核心功能

- **智能场景生成**: 基于强化学习的场景参数优化，生成多样化的高危场景
- **多环境支持**: 同时支持CARLA仿真环境和Apollo 10真实系统
- **全面的场景类型**: 包括切入、紧急制动、遮挡、行人横穿、多车协同、恶劣天气等多种场景
- **自动测试执行**: 自动化执行场景测试，收集测试数据
- **智能结果分析**: 分析测试结果，识别失败模式，提供改进建议
- **场景库管理**: 管理和组织测试场景，支持导入导出

## 系统架构

AutoExam采用模块化设计，主要包含以下组件：

1. **场景生成器**: 负责生成多样化的高危场景
2. **测试执行器**: 在CARLA或Apollo 10环境中执行场景测试
3. **结果分析器**: 分析测试结果，识别失败模式
4. **强化学习优化器**: 优化场景参数，寻找最具挑战性的场景
5. **场景库**: 管理和存储测试场景

## 目录结构

```
AutoExam/
├── main.py              # 系统主入口
├── generators/         # 场景生成模块
│   └── scene_generator.py
├── executors/          # 测试执行模块
│   ├── carla_executor.py
│   └── apollo_executor.py
├── analyzers/          # 结果分析模块
│   └── result_analyzer.py
├── optimizers/         # 参数优化模块
│   └── rl_optimizer.py
├── library/            # 场景库模块
│   └── scene_library.py
├── scenarios/          # 场景存储目录
├── results/            # 测试结果目录
├── logs/               # 日志目录
├── requirements.txt    # 依赖包
├── README.md           # 项目说明
└── AGENTS_README.md    # 智能体说明
```

## 安装与配置

### 环境要求

- Python 3.8+
- CARLA 0.9.15 (仿真环境)
- Apollo 10 (真实系统，可选)
- GPU (推荐，用于强化学习优化)

### 安装依赖

```bash
cd /home/xcc/aiX-platform/workspace/AutoExam
pip install -r requirements.txt
```

### 配置CARLA

1. 下载并安装CARLA 0.9.15
2. 启动CARLA服务器：
   ```bash
   ./CarlaUE4.sh -windowed -ResX=800 -ResY=600
   ```

### 配置Apollo 10

1. 安装Apollo 10
2. 确保Apollo 10服务正在运行
3. 配置API接口

## 使用方法

### 生成场景

```bash
# 生成10个高风险场景
python main.py --mode generate --count 10 --risk-level high

# 生成5个极端风险场景
python main.py --mode generate --count 5 --risk-level extreme
```

### 测试场景

```bash
# 在仿真环境中测试场景
python main.py --mode test --scenario-id scenario_20260302_120000_001

# 在真实系统中测试场景
python main.py --mode test --scenario-id scenario_20260302_120000_001 --environment real
```

### 批量测试

```bash
# 批量测试多个场景
python main.py --mode batch --scenario-ids scenario_20260302_120000_001 scenario_20260302_120000_002
```

### 优化场景参数

```bash
# 运行强化学习优化，迭代100次
python main.py --mode optimize --iterations 100
```

## 场景类型

AutoExam支持以下场景类型：

1. **cut-in**: 车辆切入场景
2. **emergency-brake**: 紧急制动场景
3. **occlusion**: 视线遮挡场景
4. **pedestrian-crossing**: 行人横穿场景
5. **multi-vehicle**: 多车协同场景
6. **adverse-weather**: 恶劣天气场景

## 风险等级

场景风险等级分为：
- **low**: 低风险
- **medium**: 中等风险
- **high**: 高风险
- **extreme**: 极端风险

## 结果分析

测试完成后，系统会生成详细的分析报告，包括：

- 测试状态（成功/失败）
- 失败原因分析
- 改进建议
- 性能指标（响应时间、减速度等）
- 风险评估

## 场景库管理

### 导出场景

```python
from library.scene_library import SceneLibrary

library = SceneLibrary('./scenarios')
library.export_scenarios('exported_scenarios.json')
```

### 导入场景

```python
from library.scene_library import SceneLibrary

library = SceneLibrary('./scenarios')
library.import_scenarios('exported_scenarios.json')
```

## 扩展与定制

### 添加新的场景类型

1. 在 `generators/scene_generator.py` 中添加新的场景生成方法
2. 在 `executors/` 目录下的执行器中添加相应的执行逻辑
3. 在 `optimizers/rl_optimizer.py` 中添加新场景的参数范围

### 自定义评估指标

修改 `analyzers/result_analyzer.py` 中的评估逻辑，添加自定义的评估指标。

## 示例

### 生成并测试场景

```bash
# 生成场景
python main.py --mode generate --count 3 --risk-level high

# 测试生成的场景
python main.py --mode test --scenario-id scenario_20260302_120000_001
```

### 优化参数并生成场景

```bash
# 优化参数
python main.py --mode optimize --iterations 50

# 使用优化后的参数生成场景
# （需要手动将优化结果应用到场景生成器）
```

## 注意事项

1. 使用CARLA仿真环境时，确保CARLA服务器正在运行
2. 使用Apollo 10真实系统时，确保系统已正确配置并处于安全状态
3. 生成极端风险场景时，注意测试环境的安全性
4. 定期备份场景库和测试结果

## 故障排除

### CARLA连接失败

- 检查CARLA服务器是否正在运行
- 检查网络连接和端口设置
- 确保CARLA版本与依赖包版本匹配

### Apollo 10连接失败

- 检查Apollo 10服务是否正在运行
- 检查API接口是否可访问
- 检查网络连接和权限设置

### 场景生成失败

- 检查参数范围是否合理
- 确保场景生成器配置正确

## 贡献

欢迎提交Issue和Pull Request，共同改进AutoExam系统。

## 许可证

本项目采用MIT许可证。
