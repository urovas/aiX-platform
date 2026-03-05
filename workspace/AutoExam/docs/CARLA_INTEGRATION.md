# CARLA仿真集成文档

**版本**: v1.0.0  
**更新日期**: 2026-03-02

---

## 📋 概述

AutoExam已集成CARLA仿真环境，支持无保护左转场景的实际执行和测试。

### 核心功能

- ✅ **CARLA连接管理**: 自动连接到CARLA服务器
- ✅ **场景执行**: 在CARLA中执行无保护左转场景
- ✅ **碰撞检测**: 实时检测碰撞事件
- ✅ **轨迹记录**: 记录车辆运动轨迹
- ✅ **结果可视化**: 生成轨迹图和速度曲线
- ✅ **批量测试**: 支持批量场景执行
- ✅ **统计分析**: 自动生成测试报告

---

## 🔧 环境配置

### CARLA路径

CARLA已安装在: `/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA`

### 配置文件

配置文件位置: `config/carla_config.json`

```json
{
  "carla": {
    "host": "localhost",
    "port": 2000,
    "town": "Town05",
    "timeout": 10.0,
    "carla_path": "/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA",
    "python_api_path": "/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA/PythonAPI"
  },
  "simulation": {
    "max_duration": 30,
    "tick_rate": 0.05,
    "enable_collision_sensor": true,
    "enable_spectator": true
  }
}
```

---

## 🚀 快速开始

### 1. 启动CARLA服务器

```bash
cd /home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA
./CarlaUE4.sh
```

等待CARLA完全启动（约30秒）

### 2. 运行测试脚本

```bash
# 基本测试（5个场景）
python examples/test_carla_integration.py

# 自定义参数
python examples/test_carla_integration.py \
  --count 10 \
  --weather rain \
  --session my_test_session

# 自动启动CARLA
python examples/test_carla_integration.py --start-carla
```

### 3. 查看结果

测试结果保存在: `data/results/`

- JSON数据: `{session_name}.json`
- CSV导出: `{session_name}.csv`
- 测试报告: `{session_name}_report.md`
- 轨迹图: `{session_name}_trajectory_{i}.png`
- 速度曲线: `{session_name}_velocity_{i}.png`
- 统计图表: `{session_name}_statistics.png`

---

## 📊 API接口

### 1. 获取CARLA状态

```bash
curl http://localhost:5000/api/carla/status
```

响应:
```json
{
  "success": true,
  "status": "running",
  "carla_path": "/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA",
  "host": "localhost",
  "port": 2000,
  "town": "Town05"
}
```

### 2. 执行单个场景

```bash
curl -X POST http://localhost:5000/api/carla/execute \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": {
      "id": "test_001",
      "type": "unprotected_left_turn",
      "parameters": {
        "ego_speed": 15,
        "oncoming_speed": 50,
        "time_gap": 4,
        "oncoming_vehicle_type": "sedan",
        "weather": "clear",
        "occlusion": false,
        "traffic_flow": "low",
        "has_pedestrian": false
      }
    }
  }'
```

### 3. 批量执行场景

```bash
curl -X POST http://localhost:5000/api/carla/batch_execute \
  -H "Content-Type: application/json" \
  -d '{
    "scenarios": [...],
    "session_name": "batch_test"
  }'
```

### 4. 生成轨迹可视化

```bash
curl -X POST http://localhost:5000/api/carla/visualization/trajectory \
  -H "Content-Type: application/json" \
  -d '{
    "trajectory_data": [...]
  }'
```

### 5. 获取测试会话列表

```bash
curl http://localhost:5000/api/carla/sessions
```

---

## 🎯 场景参数

### 无保护左转场景参数

| 参数 | 类型 | 范围 | 说明 |
|------|------|------|------|
| ego_speed | float | 5-30 | 主车速度 (km/h) |
| oncoming_speed | float | 30-80 | 对向车速 (km/h) |
| time_gap | float | 2-8 | 时间间隙 (秒) |
| oncoming_vehicle_type | string | sedan/truck/bus | 对向车型 |
| weather | string | clear/rain/fog/night | 天气条件 |
| occlusion | boolean | true/false | 视野遮挡 |
| traffic_flow | string | low/medium/high | 交通流量 |
| has_pedestrian | boolean | true/false | 是否有行人 |

---

## 📈 测试结果

### 结果结构

```json
{
  "success": true,
  "collision": false,
  "execution_time": 12.34,
  "collision_count": 0,
  "trajectory_data": [
    {
      "time": 0.0,
      "location": {"x": 0.0, "y": 0.0, "z": 0.0},
      "velocity": {"x": 4.17, "y": 0.0, "z": 0.0},
      "rotation": {"pitch": 0, "yaw": 0, "roll": 0}
    }
  ],
  "scenario_id": "test_001",
  "scenario_type": "unprotected_left_turn",
  "parameters": {...},
  "timestamp": "2026-03-02T20:00:00",
  "environment": "CARLA"
}
```

### 统计指标

- **总场景数**: 执行的场景总数
- **碰撞数**: 发生碰撞的场景数
- **成功数**: 成功完成的场景数
- **碰撞率**: 碰撞场景占比
- **成功率**: 成功场景占比
- **平均执行时间**: 所有场景的平均执行时间

---

## 🔍 可视化功能

### 1. 轨迹图

显示车辆在仿真过程中的运动轨迹

- 蓝色线条: 车辆轨迹
- 绿色圆点: 起点
- 红色方块: 终点

### 2. 速度曲线

显示车辆速度随时间的变化

- X轴: 时间 (秒)
- Y轴: 速度 (km/h)

### 3. 统计图表

包含四个子图:

- **结果分布**: 成功/碰撞比例饼图
- **执行时间分布**: 执行时间直方图
- **天气分布**: 不同天气场景数量
- **难度分布**: 不同难度场景数量

---

## 🛠️ 代码示例

### Python脚本

```python
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

from autoexam.executors import CarlaExecutorEnhanced, SimulationRecorder
from autoexam.generators import UnprotectedLeftTurnGenerator

# 初始化
executor = CarlaExecutorEnhanced()
recorder = SimulationRecorder('./data/results')
generator = UnprotectedLeftTurnGenerator(use_llm=False)

# 生成场景
scenario = generator.generate_one(difficulty='medium', weather='clear')

# 执行场景
result = executor.execute(scenario)

# 记录结果
recorder.record_result(result)

# 保存会话
recorder.save_session('my_session.json')

# 生成可视化
if 'trajectory_data' in result:
    recorder.plot_trajectory(result['trajectory_data'], 'trajectory.png')
    recorder.plot_velocity_profile(result['trajectory_data'], 'velocity.png')

# 清理
executor.cleanup()
```

---

## ⚠️ 注意事项

### 1. CARLA服务器

- 确保CARLA服务器正在运行
- 默认端口: 2000
- 默认地图: Town05

### 2. Python环境

- 需要安装CARLA Python API
- 添加到Python路径:

```bash
export PYTHONPATH=$PYTHONPATH:/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg
```

### 3. 资源清理

- 测试完成后调用 `executor.cleanup()` 清理资源
- 避免CARLA中残留Actor

### 4. 性能优化

- 批量执行时场景间等待3秒
- 同步模式下tick_rate: 0.05
- 最大执行时间: 30秒

---

## 🐛 故障排除

### 问题1: 无法连接CARLA

**错误**: `连接CARLA服务器失败`

**解决方案**:
```bash
# 检查CARLA是否运行
ps aux | grep CarlaUE4

# 启动CARLA
cd /home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA
./CarlaUE4.sh
```

### 问题2: 导入carla失败

**错误**: `ModuleNotFoundError: No module named 'carla'`

**解决方案**:
```bash
# 添加CARLA Python API到路径
export PYTHONPATH=$PYTHONPATH:/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg
```

### 问题3: 生成车辆失败

**错误**: `生成车辆失败`

**解决方案**:
- 检查spawn points是否可用
- 尝试更换地图或spawn point
- 检查是否有碰撞的Actor

---

## 📚 相关文档

- [CARLA官方文档](http://carla.org/)
- [CARLA Python API](https://carla.readthedocs.io/en/latest/python_api/)
- [OpenSCENARIO标准](https://www.asam.net/standards/detail/open-scenario/)
- [AutoExam用户指南](USER_GUIDE.md)
- [AutoExam架构文档](ARCHITECTURE.md)

---

## 🔄 更新日志

### v1.0.0 (2026-03-02)

- ✅ 初始版本发布
- ✅ 实现CARLA连接管理
- ✅ 实现无保护左转场景执行
- ✅ 实现碰撞检测和轨迹记录
- ✅ 实现结果可视化
- ✅ 实现批量测试支持
- ✅ 实现统计分析功能

---

**维护者**: AutoExam Team  
**联系方式**: autoexam@example.com
