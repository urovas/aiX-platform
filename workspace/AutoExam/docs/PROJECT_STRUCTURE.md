# AutoExam 项目结构说明

**版本**: v1.0.0  
**日期**: 2026-03-02  
**状态**: 已发布

---

## 目录结构概览

```
AutoExam/
├── 📄 文档文件
│   ├── README.md                      # 项目概述和快速开始
│   ├── RELEASE_NOTES.md               # 版本发布说明
│   ├── ARCHITECTURE.md                # 架构设计文档
│   ├── API_DOCUMENTATION.md           # API接口文档
│   ├── USER_GUIDE.md                  # 用户操作指南
│   ├── QUICK_START.md                 # 快速开始指南
│   ├── TESTING.md                     # 测试文档
│   ├── DEPLOYMENT.md                  # 部署文档
│   ├── CHANGELOG.md                   # 变更日志
│   ├── PROJECT_SUMMARY.md             # 项目总结
│   └── PROJECT_STRUCTURE.md           # 本文件
│
├── 🔧 配置文件
│   ├── requirements.txt               # Python依赖列表
│   ├── environment.yml                # Conda环境配置
│   ├── config.yaml                    # 应用配置文件（可选）
│   ├── .gitignore                     # Git忽略规则
│   └── docker-compose.yml             # Docker配置（可选）
│
├── 🚀 脚本文件
│   ├── install_env.sh                 # 环境安装脚本
│   ├── start.sh                       # 服务启动脚本
│   └── backup.sh                      # 数据备份脚本（可选）
│
├── 🖥️ Web界面 (ui/)
│   ├── app.py                         # Flask应用主文件
│   ├── static/                        # 静态资源
│   │   ├── css/                       # CSS样式文件
│   │   ├── js/                        # JavaScript文件
│   │   └── images/                    # 图片资源
│   └── templates/                     # HTML模板
│       ├── index.html                 # 首页
│       ├── unprotected_left_turn.html # 无保护左转页面
│       ├── scenarios.html             # 场景管理页
│       ├── results.html               # 测试结果页
│       ├── generate.html              # 场景生成页
│       ├── test.html                  # 测试执行页
│       ├── analyze.html               # 结果分析页
│       └── report.html                # 报告页面
│
├── 🎨 场景生成器 (generators/)
│   └── unprotected_left_turn_generator.py  # 无保护左转场景生成器
│       # 核心功能：
│       # - 8参数维度场景生成
│       # - 自然语言解析
│       # - 对抗性生成算法
│       # - 迭代优化闭环
│
├── 📊 分析器 (analyzers/)
│   ├── difficulty_rater.py            # 难度评级器
│   │   # 功能：场景难度计算、分级、风险因子识别
│   ├── result_analyzer.py             # 结果分析器
│   │   # 功能：测试结果分析、失败诊断
│   ├── failure_cluster_analyzer.py    # 失败聚类分析器
│   │   # 功能：失败模式聚类、模式识别
│   └── test_report_generator.py       # 测试报告生成器
│       # 功能：生成Markdown格式测试报告
│
├── 📚 场景库 (library/)
│   └── scene_library.py               # 场景库管理
│       # 功能：
│       # - 场景的存储、加载、删除
│       # - 元数据管理
│       # - 统计信息
│       # - 批量操作
│
├── 📤 导出器 (exporters/)
│   └── openscenario_exporter.py       # OpenSCENARIO导出器
│       # 功能：
│       # - 单场景导出
│       # - 批量导出
│       # - ASAM OpenSCENARIO 1.0标准格式
│
├── 🔌 集成模块 (integrations/)
│   └── agent_interface.py             # 智能体接口
│       # 功能：
│       # - 与OpenClaw智能体系统集成
│       # - 场景生成调用
│       # - 测试执行调用
│
├── ⚙️ 执行器 (executors/)
│   ├── carla_executor.py              # CARLA执行器
│   │   # 功能：在CARLA仿真环境中执行测试
│   └── apollo_executor.py             # Apollo执行器
│       # 功能：在Apollo真实系统中执行测试
│
├── 🧪 测试目录 (tests/)
│   ├── test_unprotected_left_turn_generator.py  # 场景生成器测试
│   ├── test_difficulty_rater.py                 # 难度评级器测试
│   ├── test_scene_library.py                    # 场景库测试
│   ├── test_openscenario_exporter.py            # 导出器测试
│   ├── test_api_integration.py                  # API集成测试
│   └── performance_test.py                      # 性能测试
│
├── 🛠️ 脚本工具 (scripts/)
│   ├── demo.py                        # 基础功能演示
│   ├── user_demo.py                   # 用户操作流程演示
│   ├── test_8d_scenarios.py           # 8参数维度测试
│   └── generate_unprotected_left_turn_scenarios.py  # 批量生成脚本
│
└── 📁 数据目录
    ├── scenarios/                     # 场景存储目录
    │   └── unprotected_left_turn/     # 无保护左转场景
    ├── results/                       # 测试结果目录
    ├── reports/                       # 测试报告目录
    ├── openscenario/                  # OpenSCENARIO导出目录
    └── logs/                          # 日志文件目录
```

---

## 核心模块详解

### 1. 场景生成器 (generators/)

**文件**: `unprotected_left_turn_generator.py`

**职责**: 生成无保护左转场景

**核心类**:
```python
class UnprotectedLeftTurnGenerator:
    - generate()                    # 快速生成
    - generate_from_natural_language()  # 自然语言生成
    - generate_adversarial()        # 对抗性生成
    - iterative_adversarial_generation()  # 迭代对抗性生成
```

**8参数维度**:
1. 自车速度 (5-30 km/h)
2. 对向车速 (30-80 km/h)
3. 时间间隙 (2-8秒)
4. 对向车型 (轿车/卡车/公交车)
5. 天气 (晴/雨/雾/夜)
6. 视野遮挡 (有/无)
7. 交通流量 (低/中/高)
8. 行人/非机动车 (有/无)

---

### 2. 难度评级器 (analyzers/difficulty_rater.py)

**职责**: 计算场景难度等级

**算法**: 加权评分算法
```python
难度分数 = Σ(参数值 × 权重)

权重分配:
- 时间间隙: 25% (越小越难)
- 对向车速: 20% (越高越难)
- 天气: 15-20% (恶劣天气)
- 自车速度: 15% (越高越难)
- 遮挡: 10%
- 流量: 5-10%
- 行人: 10%
```

**分级标准**:
- Easy: 0-40分
- Medium: 40-60分
- Hard: 60-80分
- Extreme: 80-100分

---

### 3. 场景库 (library/scene_library.py)

**职责**: 场景的持久化存储和管理

**存储格式**: JSON
```json
{
  "id": "场景唯一标识",
  "type": "场景类型",
  "difficulty": "难度等级",
  "parameters": {...},
  "rating": {...},
  "tested": false,
  "success": false
}
```

**API**:
- `save_scenario()` - 保存场景
- `load_scenario()` - 加载场景
- `delete_scenario()` - 删除场景
- `list_scenarios()` - 列出场景
- `get_statistics()` - 获取统计

---

### 4. OpenSCENARIO导出器 (exporters/openscenario_exporter.py)

**职责**: 导出标准格式场景文件

**标准**: ASAM OpenSCENARIO 1.0

**输出格式**: XML (.xosc)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<OpenSCENARIO>
  <FileHeader ... />
  <ParameterDeclarations>
    <ParameterDeclaration name="ego_speed" ... />
  </ParameterDeclarations>
  <Entities>...</Entities>
  <Storyboard>...</Storyboard>
</OpenSCENARIO>
```

---

### 5. Web应用 (ui/app.py)

**框架**: Flask

**路由**:
- `/` - 首页
- `/unprotected_left_turn` - 无保护左转管理
- `/scenarios` - 场景管理
- `/results` - 测试结果
- `/api/*` - RESTful API

**模板引擎**: Jinja2

**前端框架**: Bootstrap 5

---

## 数据流

### 场景生成流程

```
用户输入 → 生成器 → 难度评级 → 场景库 → 导出器 → OpenSCENARIO
    ↓
自然语言 → 解析器 → 参数配置
    ↓
对抗性生成 → 失败分析 → 高危参数空间 → 密集采样
```

### 测试执行流程

```
场景库 → 执行器 → CARLA/Apollo → 结果分析 → 报告生成
    ↓
模拟执行 → 结果存储 → 统计分析
```

---

## 配置文件说明

### requirements.txt

```
flask>=2.0.0          # Web框架
numpy>=1.20.0         # 数值计算
matplotlib>=3.3.0     # 可视化
scikit-learn>=0.24.0  # 机器学习
pytest>=7.0.0         # 测试框架
pytest-cov>=3.0.0     # 覆盖率
```

### environment.yml

```yaml
name: autoexam
channels:
  - defaults
  - conda-forge
dependencies:
  - python=3.9
  - pip
  - numpy
  - matplotlib
  - scikit-learn
  - pip:
    - flask>=2.0.0
    - pytest>=7.0.0
```

---

## 开发规范

### 代码风格

- **Python**: PEP 8
- **命名规范**:
  - 类名: PascalCase (如: `SceneGenerator`)
  - 函数: snake_case (如: `generate_scenario`)
  - 常量: UPPER_CASE (如: `MAX_COUNT`)

### 文档规范

- **模块文档**: 模块级别的docstring
- **函数文档**: 参数、返回值、异常说明
- **类型注解**: 使用Python类型提示

### 测试规范

- **单元测试**: 每个模块对应的测试文件
- **测试覆盖率**: 目标80%+
- **命名规范**: `test_*.py`

---

## 扩展指南

### 添加新场景类型

1. 创建生成器文件: `generators/new_scenario_generator.py`
2. 继承基类或实现接口
3. 实现 `generate()` 方法
4. 在Web界面添加路由

### 添加新执行环境

1. 创建执行器文件: `executors/new_executor.py`
2. 实现 `ExecutorInterface`
3. 实现 `execute()` 和 `validate_environment()`
4. 在配置中启用

### 添加新导出格式

1. 创建导出器文件: `exporters/new_exporter.py`
2. 实现 `export()` 方法
3. 在场景管理界面添加导出选项

---

## 版本控制

### Git工作流

```
main (生产分支)
  ↓
develop (开发分支)
  ↓
feature/* (功能分支)
  ↓
hotfix/* (修复分支)
```

### 提交规范

```
feat: 新功能
fix: 修复
docs: 文档
style: 格式
test: 测试
chore: 构建/工具
```

---

## 维护信息

**项目主页**: [URL]  
**问题反馈**: [Issue Tracker]  
**邮件联系**: [Email]  

**维护者**: AutoExam Team  
**最后更新**: 2026-03-02

---

**文档版本**: v1.0.0
