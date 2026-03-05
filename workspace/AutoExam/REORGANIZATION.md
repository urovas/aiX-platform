# AutoExam 项目重组说明

**日期**: 2026-03-02  
**版本**: v1.0.0

---

## 📁 新的项目结构

```
AutoExam/
├── 📄 根目录文件
│   ├── README.md              # 项目主文档
│   ├── setup.py               # Python包配置
│   ├── requirements.txt       # 依赖列表
│   ├── environment.yml        # Conda环境配置
│   ├── .gitignore            # Git忽略规则
│   └── install_env.sh       # 环境安装脚本（已废弃，使用scripts/）
│
├── 📚 docs/                   # 文档目录（12份）
│   ├── README.md
│   ├── QUICK_START.md
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE.md
│   ├── API_DOCUMENTATION.md
│   ├── TESTING.md
│   ├── DEPLOYMENT.md
│   ├── CHANGELOG.md
│   ├── RELEASE_NOTES.md
│   ├── PROJECT_STRUCTURE.md
│   ├── PROJECT_SUMMARY.md
│   ├── VERSION_ARCHIVE.md
│   └── VERSION
│
├── 💻 src/autoexam/           # 源代码目录
│   ├── __init__.py
│   ├── generators/            # 场景生成器
│   ├── analyzers/             # 分析器
│   ├── library/               # 场景库
│   ├── exporters/             # 导出器
│   ├── integrations/          # 集成模块
│   ├── executors/             # 执行器
│   └── ui/                    # Web界面
│       ├── app.py
│       ├── templates/         # HTML模板
│       └── static/            # 静态资源
│
├── 🧪 tests/                  # 测试代码（待添加）
│
├── 📖 examples/               # 示例脚本
│   ├── demo.py
│   ├── user_demo.py
│   ├── test_8d_scenarios.py
│   ├── generate_unprotected_left_turn_scenarios.py
│   └── test_unprotected_left_turn_scenarios.py
│
├── 🛠️ scripts/                # 工具脚本
│   ├── install_env.sh
│   └── start.sh
│
├── 📊 data/                   # 数据目录
│   ├── scenarios/             # 场景存储
│   ├── results/               # 测试结果
│   ├── reports/               # 测试报告
│   ├── openscenario/          # 导出文件
│   └── logs/                  # 日志文件
│
└── 🗄 archive/                 # 归档目录
    ├── old_files/            # 旧文件归档
    └── old_dirs/             # 旧目录归档
```

---

## ✅ 重组内容

### 1. 文档整理

**移动到 `docs/`**:
- README.md
- RELEASE_NOTES.md
- ARCHITECTURE.md
- API_DOCUMENTATION.md
- USER_GUIDE.md
- QUICK_START.md
- TESTING.md
- DEPLOYMENT.md
- CHANGELOG.md
- PROJECT_STRUCTURE.md
- PROJECT_SUMMARY.md
- VERSION_ARCHIVE.md
- VERSION

**保留在根目录**:
- README.md (主文档，已更新为新版本）

### 2. 源代码整理

**移动到 `src/autoexam/`**:
- `generators/` → `src/autoexam/generators/`
- `analyzers/` → `src/autoexam/analyzers/`
- `library/` → `src/autoexam/library/`
- `exporters/` → `src/autoexam/exporters/`
- `integrations/` → `src/autoexam/integrations/`
- `executors/` → `src/autoexam/executors/`
- `ui/` → `src/autoexam/ui/`

**创建包结构**:
- 添加 `__init__.py` 到每个模块
- 实现标准的Python包结构

### 3. 脚本整理

**移动到 `examples/`**:
- demo.py
- user_demo.py
- test_8d_scenarios.py
- generate_unprotected_left_turn_scenarios.py
- test_unprotected_left_turn_scenarios.py

**保留在 `scripts/`**:
- install_env.sh (更新版)
- start.sh (更新版)

### 4. 数据目录整理

**创建 `data/` 目录**:
- scenarios/
- results/
- reports/
- openscenario/
- logs/

### 5. 归档旧文件

**移动到 `archive/`**:
- `old_files/`:
  - agents_config.json
  - AGENTS_README.md
  - angent.txt
  - ARCHITECTURE_UPGRADE.md
  - config.json
  - create_agents.py
  - create_openclaw_agents.py
  - ENV_SETUP.md
  - main.py
  - name.txt
  - openscenario_demo
  - stop.sh

- `old_dirs/`:
  - demo_openscenario/
  - demo_results/
  - optimizers/

---

## 🔧 配置更新

### 1. 导入路径更新

**旧路径**:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from library.scene_library import SceneLibrary
```

**新路径**:
```python
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))
from autoexam.library import SceneLibrary
```

### 2. 数据路径更新

**旧路径**:
```python
scene_library = SceneLibrary('./scenarios')
results_dir = './results'
```

**新路径**:
```python
data_dir = os.path.join(project_root, 'data')
scene_library = SceneLibrary(os.path.join(data_dir, 'scenarios'))
results_dir = os.path.join(data_dir, 'results')
```

### 3. Flask配置更新

```python
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
```

---

## 📦 安装方式

### 开发安装

```bash
# 激活环境
conda activate autoexam

# 开发安装
pip install -e .

# 或直接运行
python src/autoexam/ui/app.py
```

### 生产安装

```bash
# 使用pip安装
pip install autoexam

# 运行
autoexam
```

---

## 🎯 使用方式

### 启动Web界面

```bash
# 方式1: 使用启动脚本
bash scripts/start.sh

# 方式2: 直接运行
python src/autoexam/ui/app.py
```

### 运行示例

```bash
# 运行演示
python examples/demo.py

# 用户演示
python examples/user_demo.py

# 8参数测试
python examples/test_8d_scenarios.py
```

---

## 📝 文档更新

需要更新的文档：
- [x] README.md - 已更新
- [x] PROJECT_STRUCTURE.md - 已创建
- [x] DEPLOYMENT.md - 已更新
- [x] ARCHITECTURE.md - 已更新

---

## ✨ 改进点

### 1. 标准化
- ✅ 符合Python项目标准结构
- ✅ 支持 `pip install` 安装
- ✅ 清晰的模块划分

### 2. 可维护性
- ✅ 源代码集中管理
- ✅ 文档统一存放
- ✅ 脚本分类清晰

### 3. 可扩展性
- ✅ 包结构易于添加新模块
- ✅ 标准导入路径
- ✅ 统一数据目录

### 4. 清洁性
- ✅ 根目录简洁
- ✅ 旧文件归档
- ✅ Git忽略规则完善

---

## 🔄 迁移指南

### 对于开发者

1. **更新导入路径**:
   ```python
   # 旧
   from generators.unprotected_left_turn_generator import UnprotectedLeftTurnGenerator
   
   # 新
   from autoexam.generators import UnprotectedLeftTurnGenerator
   ```

2. **更新数据路径**:
   ```python
   # 旧
   SceneLibrary('./scenarios')
   
   # 新
   SceneLibrary(os.path.join(project_root, 'data', 'scenarios'))
   ```

3. **更新启动命令**:
   ```bash
   # 旧
   python ui/app.py
   
   # 新
   python src/autoexam/ui/app.py
   # 或
   bash scripts/start.sh
   ```

### 对于用户

1. **重新安装环境**:
   ```bash
   bash scripts/install_env.sh
   ```

2. **使用新的启动方式**:
   ```bash
   bash scripts/start.sh
   ```

---

## 📊 统计

### 重组前后对比

| 项目 | 重组前 | 重组后 |
|------|---------|---------|
| 根目录文件 | 25+ | 6 |
| 文档位置 | 根目录 | docs/ |
| 源代码位置 | 根目录 | src/autoexam/ |
| 脚本位置 | 根目录 | examples/ + scripts/ |
| 数据目录 | 分散 | 统一data/ |

### 清理统计

- 归档文件: 11个
- 归档目录: 3个
- 创建新目录: 5个
- 更新文件: 10+个

---

**重组完成时间**: 2026-03-02  
**重组人**: AutoExam Team
