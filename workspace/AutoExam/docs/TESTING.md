# AutoExam 测试文档

**版本**: v1.0.0  
**日期**: 2026-03-02  
**状态**: 已发布

---

## 目录

1. [测试概述](#测试概述)
2. [测试策略](#测试策略)
3. [单元测试](#单元测试)
4. [集成测试](#集成测试)
5. [系统测试](#系统测试)
6. [性能测试](#性能测试)
7. [测试用例](#测试用例)
8. [测试工具](#测试工具)
9. [持续集成](#持续集成)

---

## 测试概述

### 测试目标

确保 AutoExam 系统的：
- **功能正确性**: 所有功能按预期工作
- **性能稳定性**: 在高负载下保持稳定
- **数据完整性**: 场景数据准确无误
- **接口兼容性**: API 接口符合规范

### 测试范围

| 模块 | 测试类型 | 覆盖率目标 |
|------|----------|-----------|
| SceneGenerator | 单元测试 | 80% |
| DifficultyRater | 单元测试 | 90% |
| SceneLibrary | 单元测试 + 集成测试 | 85% |
| OpenScenarioExporter | 单元测试 | 75% |
| Web API | 集成测试 | 100% |
| 端到端流程 | 系统测试 | 核心流程 |

---

## 测试策略

### 测试金字塔

```
         /\
        /  \
       / E2E\      <- 系统测试 (10%)
      /--------\
     / Integration\  <- 集成测试 (30%)
    /--------------\
   /   Unit Tests   \ <- 单元测试 (60%)
  /------------------\
```

### 测试原则

1. **自动化优先**: 所有测试用例尽可能自动化
2. **独立隔离**: 测试之间相互独立，不依赖执行顺序
3. **可重复性**: 测试结果可重复，不受环境影响
4. **快速反馈**: 单元测试执行时间 < 1分钟

---

## 单元测试

### 测试框架

- **Python**: pytest
- **JavaScript**: Jest (未来)

### 核心模块测试

#### 1. 场景生成器测试

**文件**: `tests/test_unprotected_left_turn_generator.py`

```python
import pytest
from generators.unprotected_left_turn_generator import UnprotectedLeftTurnGenerator

class TestUnprotectedLeftTurnGenerator:
    """无保护左转场景生成器测试"""
    
    @pytest.fixture
    def generator(self):
        return UnprotectedLeftTurnGenerator(use_llm=False)
    
    def test_generate_single_scenario(self, generator):
        """测试生成单个场景"""
        scenarios = generator.generate(count=1, difficulty='medium')
        assert len(scenarios) == 1
        assert 'id' in scenarios[0]
        assert 'parameters' in scenarios[0]
    
    def test_generate_multiple_scenarios(self, generator):
        """测试批量生成场景"""
        scenarios = generator.generate(count=10, difficulty='hard')
        assert len(scenarios) == 10
        # 验证ID唯一性
        ids = [s['id'] for s in scenarios]
        assert len(ids) == len(set(ids))
    
    def test_difficulty_levels(self, generator):
        """测试不同难度等级"""
        for difficulty in ['easy', 'medium', 'hard', 'extreme']:
            scenarios = generator.generate(count=5, difficulty=difficulty)
            assert len(scenarios) == 5
            for s in scenarios:
                assert s['difficulty'] == difficulty
    
    def test_parameter_ranges(self, generator):
        """测试参数范围"""
        scenarios = generator.generate(count=100, difficulty='medium')
        for s in scenarios:
            params = s['parameters']
            # 验证自车速度范围
            assert 5 <= params['ego_speed'] <= 30
            # 验证对向车速范围
            assert 30 <= params['oncoming_speed'] <= 80
            # 验证时间间隙范围
            assert 2 <= params['gap_time'] <= 8
    
    def test_natural_language_parsing(self, generator):
        """测试自然语言解析"""
        prompt = "生成50个雨天卡车遮挡场景"
        parsed = generator._parse_natural_language(prompt)
        assert parsed['count'] == 50
        assert parsed['weather'] == 'rain'
        assert parsed['vehicle_type'] == 'truck'
        assert parsed['view_blocked'] == True
    
    def test_adversarial_generation(self, generator):
        """测试对抗性生成"""
        # 模拟失败分析
        failure_analysis = {
            'high_risk_parameters': [
                {'combination': 'high_speed_rain', 'count': 10}
            ]
        }
        scenarios = generator.generate_adversarial(failure_analysis, count=10)
        assert len(scenarios) == 10
        for s in scenarios:
            assert s.get('adversarial') == True
```

#### 2. 难度评级器测试

**文件**: `tests/test_difficulty_rater.py`

```python
import pytest
from analyzers.difficulty_rater import DifficultyRater

class TestDifficultyRater:
    """难度评级器测试"""
    
    @pytest.fixture
    def rater(self):
        return DifficultyRater()
    
    def test_easy_scenario_rating(self, rater):
        """测试简单场景评级"""
        scenario = {
            'parameters': {
                'ego_speed': 5,
                'oncoming_speed': 30,
                'gap_time': 8,
                'weather': 'clear',
                'view_blocked': False,
                'traffic_flow': 'low',
                'pedestrian_present': False
            }
        }
        rating = rater.rate(scenario)
        assert rating['level'] == 'easy'
        assert rating['difficulty_score'] < 40
    
    def test_extreme_scenario_rating(self, rater):
        """测试极端场景评级"""
        scenario = {
            'parameters': {
                'ego_speed': 30,
                'oncoming_speed': 80,
                'gap_time': 2,
                'weather': 'rain_night',
                'view_blocked': True,
                'traffic_flow': 'high',
                'pedestrian_present': True
            }
        }
        rating = rater.rate(scenario)
        assert rating['level'] == 'extreme'
        assert rating['difficulty_score'] >= 80
    
    def test_risk_factors(self, rater):
        """测试风险因子识别"""
        scenario = {
            'parameters': {
                'ego_speed': 25,
                'oncoming_speed': 75,
                'gap_time': 2.5,
                'weather': 'rain',
                'view_blocked': True,
                'traffic_flow': 'high',
                'pedestrian_present': False
            }
        }
        rating = rater.rate(scenario)
        assert 'high_speed' in rating['risk_factors']
        assert 'tight_gap' in rating['risk_factors']
        assert 'bad_weather' in rating['risk_factors']
```

#### 3. 场景库测试

**文件**: `tests/test_scene_library.py`

```python
import pytest
import os
import tempfile
import shutil
from library.scene_library import SceneLibrary

class TestSceneLibrary:
    """场景库测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def library(self, temp_dir):
        return SceneLibrary(temp_dir)
    
    @pytest.fixture
    def sample_scenario(self):
        return {
            'id': 'test_scenario_001',
            'type': 'unprotected-left-turn',
            'difficulty': 'medium',
            'parameters': {'ego_speed': 15}
        }
    
    def test_save_scenario(self, library, sample_scenario):
        """测试保存场景"""
        library.save_scenario(sample_scenario)
        assert os.path.exists(os.path.join(library.base_path, 'test_scenario_001.json'))
    
    def test_load_scenario(self, library, sample_scenario):
        """测试加载场景"""
        library.save_scenario(sample_scenario)
        loaded = library.load_scenario('test_scenario_001')
        assert loaded['id'] == 'test_scenario_001'
        assert loaded['difficulty'] == 'medium'
    
    def test_list_scenarios(self, library):
        """测试列出场景"""
        for i in range(5):
            scenario = {
                'id': f'test_{i}',
                'type': 'unprotected-left-turn',
                'difficulty': 'easy'
            }
            library.save_scenario(scenario)
        
        scenarios = library.list_scenarios()
        assert len(scenarios) == 5
    
    def test_delete_scenario(self, library, sample_scenario):
        """测试删除场景"""
        library.save_scenario(sample_scenario)
        assert library.load_scenario('test_scenario_001') is not None
        
        library.delete_scenario('test_scenario_001')
        assert library.load_scenario('test_scenario_001') is None
    
    def test_get_statistics(self, library):
        """测试获取统计信息"""
        # 创建不同难度的场景
        difficulties = ['easy', 'medium', 'hard', 'extreme']
        for i, diff in enumerate(difficulties):
            for j in range(10):
                scenario = {
                    'id': f'{diff}_{j}',
                    'type': 'unprotected-left-turn',
                    'difficulty': diff
                }
                library.save_scenario(scenario)
        
        stats = library.get_statistics()
        assert stats['total'] == 40
        for diff in difficulties:
            assert stats[diff] == 10
```

#### 4. OpenSCENARIO导出测试

**文件**: `tests/test_openscenario_exporter.py`

```python
import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
from exporters.openscenario_exporter import OpenScenarioExporter

class TestOpenScenarioExporter:
    """OpenSCENARIO导出器测试"""
    
    @pytest.fixture
    def exporter(self):
        return OpenScenarioExporter()
    
    @pytest.fixture
    def sample_scenario(self):
        return {
            'id': 'test_scenario',
            'type': 'unprotected-left-turn',
            'description': '测试场景',
            'parameters': {
                'ego_speed': 15,
                'oncoming_speed': 60,
                'gap_time': 4.0,
                'oncoming_vehicle_type': 'sedan',
                'weather': 'clear',
                'view_blocked': False,
                'traffic_flow': 'low',
                'pedestrian_present': False
            }
        }
    
    def test_export_single_scenario(self, exporter, sample_scenario):
        """测试导出单个场景"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = exporter.export(sample_scenario, temp_dir)
            assert os.path.exists(file_path)
            assert file_path.endswith('.xosc')
    
    def test_export_format_validity(self, exporter, sample_scenario):
        """测试导出格式有效性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = exporter.export(sample_scenario, temp_dir)
            
            # 解析XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 验证根元素
            assert root.tag == 'OpenSCENARIO'
            
            # 验证必要元素存在
            assert root.find('FileHeader') is not None
            assert root.find('ParameterDeclarations') is not None
            assert root.find('Entities') is not None
            assert root.find('Storyboard') is not None
    
    def test_parameter_export(self, exporter, sample_scenario):
        """测试参数导出"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = exporter.export(sample_scenario, temp_dir)
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            params = root.find('ParameterDeclarations')
            param_names = [p.get('name') for p in params.findall('ParameterDeclaration')]
            
            assert 'ego_speed' in param_names
            assert 'oncoming_speed' in param_names
            assert 'gap_time' in param_names
```

---

## 集成测试

### Web API 测试

**文件**: `tests/test_api_integration.py`

```python
import pytest
import json
from ui.app import app

class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_generate_scenario_api(self, client):
        """测试场景生成API"""
        response = client.post('/api/unprotected_left_turn/generate',
                              data=json.dumps({
                                  'count': 5,
                                  'difficulty': 'medium'
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['scenarios']) == 5
    
    def test_generate_from_nlp_api(self, client):
        """测试自然语言生成API"""
        response = client.post('/api/unprotected_left_turn/generate_from_natural_language',
                              data=json.dumps({
                                  'prompt': '生成10个雨天场景'
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_get_scenarios_api(self, client):
        """测试获取场景列表API"""
        response = client.get('/api/unprotected_left_turn/scenarios')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'scenarios' in data
    
    def test_get_statistics_api(self, client):
        """测试获取统计API"""
        response = client.get('/api/unprotected_left_turn/statistics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data
    
    def test_export_scenario_api(self, client):
        """测试导出场景API"""
        # 先生成一个场景
        client.post('/api/unprotected_left_turn/generate',
                   data=json.dumps({'count': 1}),
                   content_type='application/json')
        
        # 获取场景列表
        response = client.get('/api/unprotected_left_turn/scenarios')
        data = json.loads(response.data)
        
        if data['scenarios']:
            scenario_id = data['scenarios'][0]['id']
            response = client.get(f'/api/unprotected_left_turn/export/{scenario_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
```

---

## 系统测试

### 端到端测试场景

#### 场景1: 完整工作流程

**目的**: 验证从场景生成到报告生成的完整流程

**步骤**:
1. 生成50个场景（各难度10个）
2. 执行测试（模拟）
3. 生成测试报告
4. 验证报告内容

**预期结果**:
- 所有步骤成功执行
- 报告包含正确的统计数据
- 场景文件正确保存

#### 场景2: 对抗性生成流程

**目的**: 验证对抗性生成的迭代优化效果

**步骤**:
1. 初始随机生成100个场景
2. 执行测试并分析
3. 对抗性生成100个场景
4. 对比失败率

**预期结果**:
- 对抗性生成的失败率显著高于随机生成
- 正确识别高危参数组合

#### 场景3: 大规模生成

**目的**: 验证系统在高负载下的稳定性

**步骤**:
1. 批量生成500个场景
2. 导出所有场景
3. 生成统计报告

**预期结果**:
- 生成时间 < 60秒
- 内存使用 < 2GB
- 所有场景正确保存

---

## 性能测试

### 性能指标

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 场景生成速度 | 100个/5秒 | 批量生成测试 |
| API响应时间 | <500ms | API压力测试 |
| 内存使用 | <2GB | 大规模生成测试 |
| 并发处理 | 10用户 | 并发API测试 |

### 性能测试脚本

**文件**: `tests/performance_test.py`

```python
import time
import psutil
import pytest
from generators.unprotected_left_turn_generator import UnprotectedLeftTurnGenerator

class TestPerformance:
    """性能测试"""
    
    @pytest.fixture
    def generator(self):
        return UnprotectedLeftTurnGenerator(use_llm=False)
    
    def test_generation_speed(self, generator):
        """测试生成速度"""
        start_time = time.time()
        scenarios = generator.generate(count=100, difficulty='medium')
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"生成100个场景耗时: {duration:.2f}秒")
        
        assert duration < 15  # 目标: < 15秒
        assert len(scenarios) == 100
    
    def test_memory_usage(self, generator):
        """测试内存使用"""
        process = psutil.Process()
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 生成大量场景
        scenarios = generator.generate(count=500, difficulty='hard')
        
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"内存增加: {memory_increase:.2f}MB")
        
        assert memory_increase < 500  # 目标: < 500MB
```

---

## 测试用例

### 功能测试用例矩阵

| 功能模块 | 测试用例 | 优先级 | 状态 |
|----------|----------|--------|------|
| 场景生成 | 生成单个场景 | P0 | ✅ |
| 场景生成 | 批量生成场景 | P0 | ✅ |
| 场景生成 | 不同难度生成 | P0 | ✅ |
| 场景生成 | 参数范围验证 | P1 | ✅ |
| 自然语言 | 解析数量 | P0 | ✅ |
| 自然语言 | 解析天气 | P0 | ✅ |
| 自然语言 | 解析车型 | P1 | ✅ |
| 自然语言 | 解析遮挡 | P1 | ✅ |
| 对抗性生成 | 初始生成 | P0 | ✅ |
| 对抗性生成 | 失败分析 | P0 | ✅ |
| 对抗性生成 | 密集采样 | P0 | ✅ |
| 难度评级 | 简单场景 | P1 | ✅ |
| 难度评级 | 极端场景 | P1 | ✅ |
| 难度评级 | 风险因子 | P2 | ✅ |
| 场景库 | 保存场景 | P0 | ✅ |
| 场景库 | 加载场景 | P0 | ✅ |
| 场景库 | 删除场景 | P1 | ✅ |
| 场景库 | 统计信息 | P1 | ✅ |
| 导出 | 单场景导出 | P0 | ✅ |
| 导出 | 批量导出 | P1 | ✅ |
| 导出 | 格式验证 | P0 | ✅ |
| Web API | 生成API | P0 | ✅ |
| Web API | 查询API | P0 | ✅ |
| Web API | 导出API | P0 | ✅ |

---

## 测试工具

### 推荐工具

| 工具 | 用途 | 版本 |
|------|------|------|
| pytest | Python单元测试 | 7.0+ |
| pytest-cov | 测试覆盖率 | 3.0+ |
| pytest-xdist | 并行测试 | 2.5+ |
| locust | 性能测试 | 2.0+ |
| coverage | 覆盖率报告 | 6.0+ |

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_unprotected_left_turn_generator.py

# 运行并生成覆盖率报告
pytest --cov=generators --cov=analyzers --cov=library tests/

# 并行运行测试
pytest -n auto tests/

# 运行性能测试
pytest tests/performance_test.py -v
```

---

## 持续集成

### CI/CD 配置

**文件**: `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=generators --cov=analyzers --cov=library --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## 附录

### 测试数据

**样本场景**:
```json
{
  "id": "test_scenario_001",
  "type": "unprotected-left-turn",
  "difficulty": "medium",
  "parameters": {
    "ego_speed": 15,
    "oncoming_speed": 60,
    "gap_time": 4.0,
    "oncoming_vehicle_type": "sedan",
    "weather": "clear",
    "view_blocked": false,
    "traffic_flow": "low",
    "pedestrian_present": false
  }
}
```

### 测试环境

- **操作系统**: Ubuntu 20.04 LTS
- **Python**: 3.9.7
- **内存**: 16GB
- **CPU**: Intel i7-10700

---

**文档维护**: AutoExam Team  
**最后更新**: 2026-03-02
