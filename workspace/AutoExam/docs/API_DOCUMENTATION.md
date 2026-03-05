# AutoExam API 接口文档

**版本**: v1.0.0  
**日期**: 2026-03-02  
**Base URL**: `http://localhost:5000`

---

## 目录

1. [概述](#概述)
2. [通用规范](#通用规范)
3. [场景管理 API](#场景管理-api)
4. [无保护左转场景 API](#无保护左转场景-api)
5. [测试结果 API](#测试结果-api)
6. [统计信息 API](#统计信息-api)
7. [智能体 API](#智能体-api)
8. [错误处理](#错误处理)
9. [示例代码](#示例代码)

---

## 概述

AutoExam 提供 RESTful API 接口，支持场景的生成、管理、测试和报告生成。所有 API 返回 JSON 格式的数据。

### 认证

当前版本暂不需要认证，所有 API 公开访问。

### 数据格式

- **请求**: JSON (Content-Type: application/json)
- **响应**: JSON
- **编码**: UTF-8

---

## 通用规范

### 响应格式

所有 API 响应遵循以下格式：

```json
{
  "success": true,      // 操作是否成功
  "data": { },          // 响应数据（成功时）
  "error": "错误信息"    // 错误信息（失败时）
}
```

### HTTP 状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Server Error | 服务器内部错误 |

### 分页参数

支持分页的 API 接受以下参数：

- `page`: 页码（从1开始）
- `per_page`: 每页数量（默认20，最大100）

---

## 场景管理 API

### 获取所有场景

**接口**: `GET /api/scenarios`

**描述**: 获取场景库中所有场景的元数据列表

**响应示例**:
```json
[
  {
    "id": "unprotected_left_turn_20260302_001",
    "type": "unprotected-left-turn",
    "difficulty": "hard",
    "created_at": "2026-03-02T10:30:00",
    "tested": true,
    "success": false
  }
]
```

---

### 获取场景统计

**接口**: `GET /api/statistics`

**描述**: 获取场景库的统计信息

**响应示例**:
```json
{
  "total": 500,
  "easy": 125,
  "medium": 125,
  "hard": 125,
  "extreme": 125,
  "adversarial": 0
}
```

---

## 无保护左转场景 API

### 快速生成场景

**接口**: `POST /api/unprotected_left_turn/generate`

**描述**: 基于参数配置快速生成无保护左转场景

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| count | int | 是 | 生成场景数量 (1-500) |
| difficulty | string | 否 | 难度等级: easy/medium/hard/extreme |
| weather | string | 否 | 天气: clear/rain/fog/night/rain_night |

**请求示例**:
```json
{
  "count": 100,
  "difficulty": "hard",
  "weather": "rain"
}
```

**响应示例**:
```json
{
  "success": true,
  "scenarios": [
    {
      "id": "unprotected_left_turn_20260302_001",
      "type": "unprotected-left-turn",
      "description": "雨天条件下，自车以15km/h接近路口...",
      "difficulty": "hard",
      "parameters": {
        "ego_speed": 15,
        "oncoming_speed": 70,
        "gap_time": 3.0,
        "oncoming_vehicle_type": "truck",
        "weather": "rain",
        "view_blocked": true,
        "traffic_flow": "high",
        "pedestrian_present": true
      },
      "rating": {
        "difficulty_score": 75.5,
        "level": "hard"
      }
    }
  ],
  "count": 100
}
```

---

### 自然语言生成

**接口**: `POST /api/unprotected_left_turn/generate_from_natural_language`

**描述**: 使用自然语言描述生成场景

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | string | 是 | 自然语言描述 |

**支持的描述要素**:
- 数量: "生成50个..."
- 天气: "雨天"、"雾天"、"夜间"
- 车型: "卡车"、"公交车"
- 遮挡: "有遮挡"
- 流量: "高流量"
- 行人: "有行人"
- 难度: "困难"、"简单"

**请求示例**:
```json
{
  "prompt": "生成100个雨天卡车遮挡高流量场景"
}
```

**响应示例**:
```json
{
  "success": true,
  "scenarios": [...],
  "count": 100
}
```

---

### 对抗性生成

**接口**: `POST /api/unprotected_left_turn/adversarial_generate`

**描述**: 执行对抗性生成，智能发现系统弱点

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| initial_count | int | 否 | 初始场景数 (50-500, 默认100) |
| iterations | int | 否 | 迭代次数 (2-5, 默认3) |
| executor | string | 否 | 执行方式: simulate/carla |

**请求示例**:
```json
{
  "initial_count": 100,
  "iterations": 3,
  "executor": "simulate"
}
```

**响应示例**:
```json
{
  "success": true,
  "total_scenarios": 400,
  "total_failures": 280,
  "high_risk_count": 5,
  "saved_count": 400,
  "iterations": 3
}
```

---

### 批量生成

**接口**: `POST /api/unprotected_left_turn/batch_generate`

**描述**: 批量生成不同难度的场景

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| config | array | 否 | 生成配置数组 |

**config 格式**:
```json
[
  {"count": 125, "difficulty": "easy", "weather": "clear"},
  {"count": 125, "difficulty": "medium", "weather": "clear"},
  {"count": 125, "difficulty": "hard", "weather": "rain"},
  {"count": 125, "difficulty": "extreme", "weather": "rain_night"}
]
```

**响应示例**:
```json
{
  "success": true,
  "scenarios": [...],
  "count": 500,
  "statistics": {
    "total": 500,
    "easy": 125,
    "medium": 125,
    "hard": 125,
    "extreme": 125
  },
  "output_dir": "./openscenario/unprotected_left_turn"
}
```

---

### 获取场景列表

**接口**: `GET /api/unprotected_left_turn/scenarios`

**描述**: 获取无保护左转场景列表

**响应示例**:
```json
{
  "success": true,
  "scenarios": [
    {
      "id": "unprotected_left_turn_20260302_001",
      "description": "雨天条件下...",
      "difficulty": "hard",
      "weather": "rain",
      "vehicle_type": "truck",
      "gap_time": 3.0,
      "tested": true,
      "success": false
    }
  ]
}
```

---

### 获取场景统计

**接口**: `GET /api/unprotected_left_turn/statistics`

**描述**: 获取无保护左转场景的统计信息

**响应示例**:
```json
{
  "total": 500,
  "easy": 125,
  "medium": 125,
  "hard": 125,
  "extreme": 125,
  "adversarial": 0
}
```

---

### 获取单个场景

**接口**: `GET /api/unprotected_left_turn/scenario/{scenario_id}`

**描述**: 获取指定场景的完整信息

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scenario_id | string | 是 | 场景ID |

**响应示例**:
```json
{
  "success": true,
  "scenario": {
    "id": "unprotected_left_turn_20260302_001",
    "type": "unprotected-left-turn",
    "description": "...",
    "parameters": {...},
    "rating": {...}
  }
}
```

---

### 导出场景

**接口**: `GET /api/unprotected_left_turn/export/{scenario_id}`

**描述**: 将场景导出为 OpenSCENARIO 格式

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scenario_id | string | 是 | 场景ID |

**响应示例**:
```json
{
  "success": true,
  "file_path": "./openscenario/unprotected_left_turn/unprotected_left_turn_20260302_001.xosc"
}
```

---

### 批量导出

**接口**: `POST /api/unprotected_left_turn/export`

**描述**: 批量导出场景为 OpenSCENARIO 格式

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| scenario_ids | array | 是 | 场景ID数组 |
| output_dir | string | 否 | 输出目录 |

**请求示例**:
```json
{
  "scenario_ids": ["unprotected_left_turn_001", "unprotected_left_turn_002"],
  "output_dir": "./openscenario/batch_export"
}
```

**响应示例**:
```json
{
  "success": true,
  "count": 2,
  "output_dir": "./openscenario/batch_export"
}
```

---

### 生成测试报告

**接口**: `POST /api/unprotected_left_turn/generate_report`

**描述**: 生成完整的测试报告

**响应示例**:
```json
{
  "success": true,
  "report_path": "./reports/comprehensive_test_report.md"
}
```

---

## 测试结果 API

### 获取所有结果

**接口**: `GET /api/results`

**描述**: 获取所有测试结果

**响应示例**:
```json
[
  {
    "scenario_id": "unprotected_left_turn_001",
    "test_type": "simulation",
    "result": {
      "success": false,
      "collision": true,
      "timeout": false,
      "execution_time": 15.5
    },
    "timestamp": "2026-03-02T10:35:00"
  }
]
```

---

## 统计信息 API

### 获取全局统计

**接口**: `GET /api/statistics`

**描述**: 获取系统全局统计信息

**响应示例**:
```json
{
  "total": 500,
  "easy": 125,
  "medium": 125,
  "hard": 125,
  "extreme": 125,
  "adversarial": 0
}
```

---

## 智能体 API

### 获取智能体列表

**接口**: `GET /api/agents`

**描述**: 获取可用的智能体列表

**响应示例**:
```json
{
  "success": true,
  "agents": [
    {
      "name": "scene_generator",
      "description": "场景生成智能体",
      "status": "available"
    }
  ]
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息",
  "code": "ERROR_CODE"
}
```

### 错误码

| 错误码 | 描述 | HTTP状态码 |
|--------|------|-----------|
| INVALID_PARAM | 参数错误 | 400 |
| SCENARIO_NOT_FOUND | 场景不存在 | 404 |
| GENERATION_FAILED | 生成失败 | 500 |
| EXPORT_FAILED | 导出失败 | 500 |
| INTERNAL_ERROR | 内部错误 | 500 |

---

## 示例代码

### Python 示例

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# 1. 快速生成场景
def generate_scenarios():
    url = f"{BASE_URL}/api/unprotected_left_turn/generate"
    data = {
        "count": 10,
        "difficulty": "hard",
        "weather": "rain"
    }
    response = requests.post(url, json=data)
    return response.json()

# 2. 自然语言生成
def generate_from_nlp():
    url = f"{BASE_URL}/api/unprotected_left_turn/generate_from_natural_language"
    data = {
        "prompt": "生成50个雨天卡车遮挡场景"
    }
    response = requests.post(url, json=data)
    return response.json()

# 3. 对抗性生成
def adversarial_generate():
    url = f"{BASE_URL}/api/unprotected_left_turn/adversarial_generate"
    data = {
        "initial_count": 100,
        "iterations": 3,
        "executor": "simulate"
    }
    response = requests.post(url, json=data)
    return response.json()

# 4. 获取场景列表
def get_scenarios():
    url = f"{BASE_URL}/api/unprotected_left_turn/scenarios"
    response = requests.get(url)
    return response.json()

# 5. 导出场景
def export_scenario(scenario_id):
    url = f"{BASE_URL}/api/unprotected_left_turn/export/{scenario_id}"
    response = requests.get(url)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 生成场景
    result = generate_scenarios()
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### cURL 示例

```bash
# 快速生成场景
curl -X POST http://localhost:5000/api/unprotected_left_turn/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 10, "difficulty": "hard", "weather": "rain"}'

# 自然语言生成
curl -X POST http://localhost:5000/api/unprotected_left_turn/generate_from_natural_language \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成50个雨天卡车场景"}'

# 对抗性生成
curl -X POST http://localhost:5000/api/unprotected_left_turn/adversarial_generate \
  -H "Content-Type: application/json" \
  -d '{"initial_count": 100, "iterations": 3}'

# 获取场景列表
curl http://localhost:5000/api/unprotected_left_turn/scenarios

# 导出场景
curl http://localhost:5000/api/unprotected_left_turn/export/unprotected_left_turn_001
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:5000';

// 快速生成场景
async function generateScenarios() {
  const response = await fetch(`${BASE_URL}/api/unprotected_left_turn/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      count: 10,
      difficulty: 'hard',
      weather: 'rain'
    })
  });
  return await response.json();
}

// 自然语言生成
async function generateFromNLP() {
  const response = await fetch(`${BASE_URL}/api/unprotected_left_turn/generate_from_natural_language`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: '生成50个雨天卡车遮挡场景'
    })
  });
  return await response.json();
}

// 获取场景列表
async function getScenarios() {
  const response = await fetch(`${BASE_URL}/api/unprotected_left_turn/scenarios`);
  return await response.json();
}
```

---

## 更新日志

### v1.0.0 (2026-03-02)
- 初始版本发布
- 支持无保护左转场景的生成、管理、导出
- 支持对抗性生成
- 支持 OpenSCENARIO 格式导出

---

**文档维护**: AutoExam Team  
**最后更新**: 2026-03-02
