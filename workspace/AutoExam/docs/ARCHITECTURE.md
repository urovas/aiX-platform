# AutoExam 架构设计文档

**版本**: v1.0.0  
**日期**: 2026-03-02  
**状态**: 已发布

---

## 1. 架构概述

### 1.1 设计目标

AutoExam采用**分层架构设计**，实现以下目标：
- **模块化**: 各功能模块独立，便于维护和扩展
- **可扩展性**: 支持新场景类型和执行环境的快速集成
- **可测试性**: 各层独立测试，确保系统稳定性
- **标准化**: 遵循行业标准（OpenSCENARIO）

### 1.2 架构原则

1. **单一职责**: 每个模块只负责一个明确的功能
2. **依赖倒置**: 高层模块不依赖低层模块，都依赖抽象
3. **接口隔离**: 模块间通过明确的接口通信
4. **开闭原则**: 对扩展开放，对修改封闭

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              表示层 (Presentation Layer)                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Web Interface (Flask)                         │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │   │
│  │  │   首页      │ │ 无保护左转  │ │  场景管理   │ │ 测试结果  │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                              业务逻辑层 (Business Logic Layer)           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │
│  │  SceneGenerator │ │ DifficultyRater │ │   ReportGenerator       │   │
│  │  (场景生成器)    │ │   (难度评级器)   │ │    (报告生成器)          │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────────────┘   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │
│  │ ResultAnalyzer  │ │ FailureCluster  │ │   AdversarialGen        │   │
│  │  (结果分析器)    │ │ (失败聚类分析)   │ │   (对抗性生成)           │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                              执行层 (Execution Layer)                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │
│  │  CARLAExecutor  │ │ ApolloExecutor  │ │   SimulationExecutor    │   │
│  │ (CARLA执行器)    │ │ (Apollo执行器)   │ │    (模拟执行器)          │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                              数据层 (Data Layer)                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐   │
│  │   SceneLibrary  │ │ OpenScenario    │ │   ResultStorage         │   │
│  │   (场景库)       │ │   Exporter      │ │    (结果存储)            │   │
│  │                 │ │ (标准格式导出)   │ │                         │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 分层说明

#### 2.2.1 表示层 (Presentation Layer)
- **职责**: 用户界面展示和交互
- **技术**: Flask + Bootstrap + Jinja2
- **模块**:
  - `ui/app.py`: Flask应用主文件
  - `ui/templates/`: HTML模板
  - `ui/static/`: 静态资源(CSS/JS)

#### 2.2.2 业务逻辑层 (Business Logic Layer)
- **职责**: 核心业务逻辑处理
- **模块**:
  - `generators/`: 场景生成器
  - `analyzers/`: 分析器（难度评级、结果分析、报告生成）

#### 2.2.3 执行层 (Execution Layer)
- **职责**: 场景测试执行
- **模块**:
  - `executors/`: 各类执行器（CARLA、Apollo、模拟）

#### 2.2.4 数据层 (Data Layer)
- **职责**: 数据存储和格式转换
- **模块**:
  - `library/`: 场景库管理
  - `exporters/`: 格式导出器

---

## 3. 核心模块设计

### 3.1 场景生成器 (SceneGenerator)

#### 3.1.1 类图

```
┌─────────────────────────────────────────┐
│     UnprotectedLeftTurnGenerator        │
├─────────────────────────────────────────┤
│ - scenario_count: int                   │
│ - parameter_ranges: Dict                │
│ - use_llm: bool                         │
├─────────────────────────────────────────┤
│ + generate(count, difficulty, weather)  │
│ + generate_from_natural_language(prompt)│
│ + generate_adversarial(analysis, count) │
│ + iterative_adversarial_generation(...) │
│ - _sample_parameters(difficulty)        │
│ - _parse_natural_language(prompt)       │
│ - _simulate_execution(scenario)         │
└─────────────────────────────────────────┘
```

#### 3.1.2 设计模式
- **策略模式**: 不同难度使用不同的参数采样策略
- **模板方法模式**: 场景生成的基础流程固定，具体实现可扩展

#### 3.1.3 关键算法

**参数采样算法**:
```python
def _sample_parameters(self, difficulty: str) -> Dict:
    """基于难度等级的参数采样"""
    ranges = self.parameter_ranges
    
    if difficulty == 'easy':
        # 简单: 宽松条件
        return {
            'ego_speed': random.uniform(5, 15),
            'oncoming_speed': random.uniform(30, 50),
            'gap_time': random.uniform(5, 8),
            ...
        }
    elif difficulty == 'hard':
        # 困难: 严格条件
        return {
            'ego_speed': random.uniform(20, 30),
            'oncoming_speed': random.uniform(60, 80),
            'gap_time': random.uniform(2, 4),
            ...
        }
```

**对抗性生成算法**:
```python
def generate_adversarial(self, failure_analysis: Dict, count: int) -> List[Dict]:
    """在高危参数空间内密集采样"""
    high_risk_params = failure_analysis['high_risk_parameters']
    
    scenarios = []
    for i in range(count):
        # 按风险权重采样参数组合
        risk_combination = self._sample_by_risk_weight(high_risk_params)
        # 在高危参数空间内生成场景
        scenario = self._generate_in_risk_space(risk_combination)
        scenarios.append(scenario)
    
    return scenarios
```

### 3.2 难度评级器 (DifficultyRater)

#### 3.2.1 评级算法

**加权评分算法**:
```python
def _calculate_difficulty_score(self, scenario: Dict) -> float:
    """计算场景难度分数 (0-100)"""
    params = scenario['parameters']
    score = 0.0
    
    # 自车速度权重 (越高越难)
    ego_speed = params['ego_speed']
    score += (ego_speed / 30) * 15  # 权重15
    
    # 对向车速权重 (越高越难)
    oncoming_speed = params['oncoming_speed']
    score += ((oncoming_speed - 30) / 50) * 20  # 权重20
    
    # 时间间隙权重 (越小越难)
    gap_time = params['gap_time']
    score += ((8 - gap_time) / 6) * 25  # 权重25
    
    # 天气权重
    weather_weights = {'clear': 0, 'rain': 10, 'fog': 15, 'night': 12, 'rain_night': 20}
    score += weather_weights.get(params['weather'], 0)
    
    # 遮挡权重
    if params['view_blocked']:
        score += 10
    
    # 流量权重
    traffic_weights = {'low': 0, 'medium': 5, 'high': 10}
    score += traffic_weights.get(params['traffic_flow'], 0)
    
    # 行人权重
    if params['pedestrian_present']:
        score += 10
    
    return min(score, 100)
```

#### 3.2.2 难度分级标准

| 难度等级 | 分数范围 | 描述 |
|----------|----------|------|
| Easy | 0-40 | 宽松条件，低挑战性 |
| Medium | 40-60 | 中等条件，标准测试 |
| Hard | 60-80 | 严格条件，高挑战性 |
| Extreme | 80-100 | 极端条件，极限测试 |

### 3.3 对抗性生成引擎

#### 3.3.1 核心闭环流程

```
┌─────────────────────────────────────────────────────────────┐
│                    对抗性生成核心闭环                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  初始随机    │───→│   测试执行   │───→│  失败分析    │  │
│  │  生成场景    │    │   (模拟/     │    │  识别高危    │  │
│  │  (第0轮)     │    │   CARLA)     │    │  参数组合    │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│  ┌───────────────────────────────────────────────┘          │
│  │                                                          │
│  ▼                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  聚焦高危    │───→│   密集采样   │───→│  深度测试    │  │
│  │  参数空间    │    │   (第1轮+)   │    │  验证弱点    │  │
│  │              │    │              │    │              │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│  ◄───────────────────────────────────────────────┘          │
│  (迭代优化，直到收敛或达到最大迭代次数)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.2 失败分析算法

```python
def _analyze_failures(self, scenarios: List[Dict], results: List[Dict]) -> Dict:
    """分析失败案例，识别高危参数组合"""
    failure_combinations = []
    
    for scenario, result in zip(scenarios, results):
        if not result.get('success', True):
            # 提取失败场景的参数组合
            params = scenario['parameters']
            combination = {
                'ego_speed_range': self._get_speed_range(params['ego_speed']),
                'oncoming_speed_range': self._get_speed_range(params['oncoming_speed']),
                'gap_time_range': self._get_gap_range(params['gap_time']),
                'weather': params['weather'],
                'view_blocked': params['view_blocked'],
                'traffic_flow': params['traffic_flow'],
                'pedestrian_present': params['pedestrian_present']
            }
            failure_combinations.append(combination)
    
    # 统计最常见的失败参数组合
    high_risk_params = self._cluster_failure_combinations(failure_combinations)
    
    return {
        'total_failures': len(failure_combinations),
        'high_risk_parameters': high_risk_params,
        'failure_rate': len(failure_combinations) / len(scenarios)
    }
```

---

## 4. 数据模型

### 4.1 场景数据模型

```json
{
  "id": "unprotected_left_turn_20260302_001",
  "type": "unprotected-left-turn",
  "description": "雨天条件下，自车以15km/h接近路口，对向有卡车以70km/h驶来，时间间隙3.0秒，有视野遮挡，高交通流量，有行人",
  "difficulty": "hard",
  "adversarial": false,
  "created_at": "2026-03-02T10:30:00",
  "parameters": {
    "ego_speed": 15,
    "oncoming_speed": 70,
    "gap_time": 3.0,
    "oncoming_vehicle_type": "truck",
    "weather": "rain",
    "view_blocked": true,
    "traffic_flow": "high",
    "pedestrian_present": true,
    "distance_to_intersection": 30,
    "road_width": 3.0,
    "visibility": 100
  },
  "rating": {
    "difficulty_score": 75.5,
    "level": "hard",
    "risk_factors": ["high_speed", "tight_gap", "bad_weather", "view_blocked"]
  },
  "tested": true,
  "success": false,
  "execution_result": {
    "collision": true,
    "timeout": false,
    "execution_time": 15.5
  }
}
```

### 4.2 OpenSCENARIO映射

| AutoExam参数 | OpenSCENARIO元素 | 说明 |
|--------------|------------------|------|
| ego_speed | SpeedAction/AbsoluteTargetSpeed | 自车速度 |
| oncoming_speed | SpeedAction/AbsoluteTargetSpeed | 对向车速度 |
| gap_time | StartTrigger/Condition/delay | 时间间隙 |
| weather | Environment/Weather | 天气条件 |
| view_blocked | Entity/Object | 遮挡车辆 |

---

## 5. 接口设计

### 5.1 内部接口

#### 5.1.1 场景生成器接口

```python
class SceneGeneratorInterface(ABC):
    """场景生成器接口"""
    
    @abstractmethod
    def generate(self, count: int, difficulty: str, **kwargs) -> List[Dict]:
        """生成场景"""
        pass
    
    @abstractmethod
    def generate_from_natural_language(self, prompt: str) -> List[Dict]:
        """从自然语言生成场景"""
        pass
```

#### 5.1.2 执行器接口

```python
class ExecutorInterface(ABC):
    """执行器接口"""
    
    @abstractmethod
    def execute(self, scenario: Dict) -> Dict:
        """执行场景测试"""
        pass
    
    @abstractmethod
    def validate_environment(self) -> bool:
        """验证执行环境"""
        pass
```

### 5.2 REST API接口

详见 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 6. 部署架构

### 6.1 单机部署

```
┌─────────────────────────────────────┐
│           单机部署架构               │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │      AutoExam Web Server    │   │
│  │         (Flask)             │   │
│  │         Port: 5000          │   │
│  └─────────────────────────────┘   │
│              │                      │
│              ▼                      │
│  ┌─────────────────────────────┐   │
│  │      Scene Library          │   │
│  │    (JSON Files)             │   │
│  └─────────────────────────────┘   │
│              │                      │
│              ▼                      │
│  ┌─────────────────────────────┐   │
│  │      CARLA Simulator        │   │
│  │      (Optional)             │   │
│  │      Port: 2000             │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### 6.2 分布式部署（未来）

```
┌─────────────────────────────────────────────────────────┐
│                   分布式部署架构                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐         ┌─────────────────────────┐   │
│  │   Nginx     │────────→│   AutoExam Web Cluster  │   │
│  │   (LB)      │         │   (Multiple Instances)  │   │
│  └─────────────┘         └─────────────────────────┘   │
│                                     │                   │
│                                     ▼                   │
│                          ┌─────────────────────────┐   │
│                          │    Redis (Cache)        │   │
│                          └─────────────────────────┘   │
│                                     │                   │
│                    ┌────────────────┼────────────────┐  │
│                    ▼                ▼                ▼  │
│           ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│           │CARLA Node 1 │  │CARLA Node 2 │  │  ...   │ │
│           └─────────────┘  └─────────────┘  └────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 安全设计

### 7.1 输入验证
- 所有API接口参数进行类型和范围验证
- 自然语言输入进行敏感词过滤
- 文件上传限制类型和大小

### 7.2 数据安全
- 场景数据本地存储，不上传云端
- 测试结果加密存储（可选）
- 定期备份机制

### 7.3 执行安全
- CARLA执行环境隔离
- 测试执行超时机制
- 异常场景自动终止

---

## 8. 性能设计

### 8.1 性能指标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| 场景生成速度 | 100个/5秒 | 100个/5-10秒 |
| API响应时间 | <500ms | <200ms |
| 页面加载时间 | <2秒 | <1秒 |
| 并发用户数 | 10 | 未测试 |

### 8.2 优化策略

1. **缓存优化**: 场景元数据缓存，减少磁盘IO
2. **异步处理**: 对抗性生成使用异步任务
3. **批量操作**: 支持场景的批量生成和导出
4. **懒加载**: 场景列表分页加载

---

## 9. 扩展性设计

### 9.1 新场景类型扩展

添加新场景类型只需：
1. 创建新的生成器类，继承 `SceneGeneratorInterface`
2. 实现 `generate()` 和 `generate_from_natural_language()` 方法
3. 在Web界面添加对应的路由和页面

### 9.2 新执行环境扩展

添加新执行环境只需：
1. 创建新的执行器类，继承 `ExecutorInterface`
2. 实现 `execute()` 和 `validate_environment()` 方法
3. 在配置中添加执行环境选项

---

## 10. 附录

### 10.1 术语表

| 术语 | 说明 |
|------|------|
| 无保护左转 | 没有交通信号灯保护的左转场景 |
| 对抗性生成 | 智能发现系统弱点的场景生成方法 |
| OpenSCENARIO | ASAM标准的场景描述格式 |
| 时间间隙 | 自车与对向车到达冲突点的时间差 |
| 高危参数组合 | 最容易导致失败的参数配置 |

### 10.2 参考资料

- [ASAM OpenSCENARIO 1.0](https://www.asam.net/standards/detail/openscenario/)
- [CARLA Simulator](https://carla.org/)
- [Apollo Auto](https://apollo.auto/)

---

**文档版本**: v1.0.0  
**最后更新**: 2026-03-02  
**维护者**: AutoExam Team
