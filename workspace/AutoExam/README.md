# AutoExam - 自动驾驶系统高危场景生成与仿真测试平台

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](docs/VERSION)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

AutoExam 是一个面向自动驾驶系统的高危场景智能生成与测试平台，专注于发现和验证自动驾驶算法在复杂、危险场景下的表现。

## ✨ 核心特性

- **🎨 8参数维度场景生成**: 支持自车速度、对向车速、时间间隙、对向车型、天气、视野遮挡、交通流量、行人/非机动车等8个维度的组合
- **🧠 智能对抗生成**: 通过迭代优化自动发现系统弱点，失败率可从20%提升至90%+
- **🌐 Web可视化界面**: 现代化的Web界面，支持快速生成、自然语言、对抗性三种模式
- **📊 标准格式导出**: 支持 ASAM OpenSCENARIO 1.0 标准格式，兼容CARLA等仿真平台
- **📈 完整测试报告**: 自动分析失败模式，识别高危参数组合，提供改进建议
- **👥 智能行人行为**: 支持6种行人行为模式（正常/谨慎/鲁莽/结伴/突发/紧急），不同年龄/体型行人，速度差异
- **🚶‍♂️ 行人与车辆互动**: 行人会观察车辆，车辆会注意行人，模拟真实道路交互
- **🚗 优化交通流路径**: 使用waypoint导航，避免碰撞，生成更真实的多车道交通流
- **🌤️ 多天气场景库**: 8种天气场景（晴天/雨天/雾天/夜间等），影响感知难度
- **🔄 详细密度控制**: 支持行人/自行车/摩托车/交通流/路边停车的详细密度参数
- **⚡ 高复杂度场景**: 支持极端密度场景，最多可生成35+行人，15+交通流车辆

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd AutoExam

# 安装依赖
bash scripts/install_env.sh

# 激活环境
conda activate autoexam
```

### 启动Web界面

```bash
python src/autoexam/ui/app.py
```

访问 http://localhost:5000 使用Web界面

### 命令行示例

```bash
# 运行演示
python examples/demo.py

# 生成500个场景
python examples/generate_unprotected_left_turn_scenarios.py
```

## 📁 项目结构

```
AutoExam/
├── docs/                    # 文档目录
│   ├── README.md           # 项目概述
│   ├── QUICK_START.md      # 快速开始
│   ├── USER_GUIDE.md       # 用户指南
│   ├── ARCHITECTURE.md     # 架构设计
│   ├── API_DOCUMENTATION.md # API文档
│   └── ...
├── src/autoexam/           # 源代码
│   ├── generators/         # 场景生成器
│   ├── analyzers/          # 分析器
│   ├── library/            # 场景库
│   ├── exporters/          # 导出器
│   ├── integrations/       # 集成模块
│   ├── executors/          # 执行器
│   └── ui/                 # Web界面
├── tests/                  # 测试代码
├── examples/               # 示例脚本
├── scripts/                # 工具脚本
└── data/                   # 数据目录
    ├── scenarios/          # 场景存储
    ├── results/            # 测试结果
    ├── reports/            # 测试报告
    └── openscenario/       # 导出文件
```

## 📚 文档

- [快速开始](docs/QUICK_START.md) - 5分钟上手
- [用户指南](docs/USER_GUIDE.md) - 详细操作说明
- [架构设计](docs/ARCHITECTURE.md) - 系统架构文档
- [API文档](docs/API_DOCUMENTATION.md) - RESTful API
- [部署指南](docs/DEPLOYMENT.md) - 部署和运维

## 🎯 主要功能

### 1. 场景生成

**快速生成**:
```bash
curl -X POST http://localhost:5000/api/unprotected_left_turn/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 100, "difficulty": "hard"}'
```

**自然语言生成**:
```bash
curl -X POST http://localhost:5000/api/unprotected_left_turn/generate_from_natural_language \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成50个雨天卡车遮挡场景"}'
```

**对抗性生成**:
```bash
curl -X POST http://localhost:5000/api/unprotected_left_turn/adversarial_generate \
  -H "Content-Type: application/json" \
  -d '{"initial_count": 100, "iterations": 3}'
```

### 2. 8参数维度

| 参数 | 范围 | 说明 |
|------|------|------|
| 自车速度 | 5-30 km/h | 接近路口的速度 |
| 对向车速 | 30-80 km/h | 对向直行车的速度 |
| 时间间隙 | 2-8秒 | 到达冲突点的时间差 |
| 对向车型 | 轿车/卡车/公交 | 影响博弈行为 |
| 天气 | 晴/雨/雾/夜 | 影响感知难度 |
| 视野遮挡 | 有/无 | 大车遮挡小车 |
| 交通流量 | 低/中/高 | 多车道车流 |
| 行人/非机动车 | 有/无 | 增加复杂度 |

### 3. 对抗性生成效果

| 阶段 | 失败率 | 说明 |
|------|--------|------|
| 初始随机 | ~20-30% | 均匀采样参数空间 |
| 第1轮对抗 | ~50-60% | 聚焦高危参数空间 |
| 第2轮对抗 | ~70-80% | 细分失败模式 |
| 第3轮对抗 | ~90%+ | 精准打击弱点 |

### 4. 详细密度参数

| 参数 | 选项 | 说明 |
|------|------|------|
| pedestrian-density | none/low/medium/high/extreme | 行人密度（0-35+） |
| bicycle-density | none/low/medium/high/extreme | 自行车密度（0-12+） |
| motorcycle-density | none/low/medium/high/extreme | 摩托车密度（0-8+） |
| traffic-density | none/low/medium/high/extreme | 交通流密度（0-15+） |
| parked-density | none/low/medium/high | 路边停车密度（0-5+） |

### 5. 行人行为模式

| 模式 | 说明 |
|------|------|
| normal | 正常行走，随机目的地，偶尔停留 |
| cautious | 谨慎行走，先观察再走，速度较慢 |
| reckless | 鲁莽行为，不看车，直接冲 |
| group | 结伴而行，多人一起移动 |
| erratic | 突发行为，突然变向/停留 |
| emergency | 紧急情况，奔跑 |

### 6. 天气场景

| 场景 | 说明 |
|------|------|
| clear_day | 晴天 |
| clear_night | 晴天夜间 |
| rain_day | 雨天 |
| rain_night | 雨天夜间 |
| fog_day | 雾天 |
| fog_night | 雾天夜间 |
| heavy_rain | 暴雨 |
| wet_sunset | 雨后黄昏 |

## 🏗️ 系统架构

```
┌─────────────────────────────────────────┐
│           Web Interface (Flask)         │
├─────────────────────────────────────────┤
│  Generators │ Analyzers │ Exporters    │
├─────────────────────────────────────────┤
│  Executors (CARLA/Apollo/Simulation)   │
├─────────────────────────────────────────┤
│           Scene Library                 │
└─────────────────────────────────────────┘
```

## 🛠️ 技术栈

- **后端**: Python 3.9+, Flask
- **前端**: Bootstrap 5, Jinja2
- **数据**: JSON, OpenSCENARIO XML
- **测试**: pytest
- **部署**: Conda, Docker

## 📦 交付成果

- ✅ **500+无保护左转场景**: 覆盖8参数维度
- ✅ **四级难度分级**: 简单/中等/困难/极端
- ✅ **OpenSCENARIO格式**: 行业标准兼容
- ✅ **完整文档**: 12份文档，10000+行
- ✅ **Web界面**: 直观的可视化操作

## 🔮 路线图

### v1.1.0 (计划中)
- [ ] CARLA完整集成
- [ ] Apollo真实测试
- [ ] 场景图形化预览

### v1.2.0 (计划中)
- [ ] 更多场景类型
- [ ] ML优化对抗生成
- [ ] 性能优化

### v2.0.0 (远期)
- [ ] 分布式测试
- [ ] 云端场景库
- [ ] 自动化回归

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 联系我们

- **项目主页**: [URL]
- **问题反馈**: [Issue Tracker]
- **邮件联系**: [Email]

---

**版本**: v2.0.0  
**更新日期**: 2026-03-03

*AutoExam - 让自动驾驶测试更智能、更高效*
