#!/usr/bin/env python3
"""
批量生成无保护左转场景
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.unprotected_left_turn_generator import UnprotectedLeftTurnGenerator
from analyzers.difficulty_rater import DifficultyRater
from exporters.openscenario_exporter import OpenScenarioExporter
from library.scene_library import SceneLibrary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BatchGenerator')

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("批量生成无保护左转场景")
    logger.info("=" * 60)
    
    # 初始化组件
    generator = UnprotectedLeftTurnGenerator(use_llm=False)
    rater = DifficultyRater()
    exporter = OpenScenarioExporter()
    library = SceneLibrary('./scenarios')
    
    # 创建输出目录
    output_dir = './scenarios/unprotected_left_turn'
    openscenario_dir = './openscenario/unprotected_left_turn'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(openscenario_dir, exist_ok=True)
    
    # 生成场景配置
    generation_config = [
        {'count': 125, 'difficulty': 'easy', 'weather': 'clear'},
        {'count': 125, 'difficulty': 'medium', 'weather': 'clear'},
        {'count': 125, 'difficulty': 'hard', 'weather': 'rain'},
        {'count': 125, 'difficulty': 'extreme', 'weather': 'rain_night'}
    ]
    
    all_scenarios = []
    total_count = 0
    
    # 按配置生成场景
    for config in generation_config:
        count = config['count']
        difficulty = config['difficulty']
        weather = config['weather']
        
        logger.info(f"生成 {count} 个 {difficulty} 难度的场景，天气: {weather}")
        
        scenarios = generator.generate(count, difficulty, weather)
        
        # 评级场景
        for scenario in scenarios:
            rating = rater.rate(scenario)
            scenario['rating'] = rating
        
        all_scenarios.extend(scenarios)
        total_count += count
        
        logger.info(f"已生成 {len(scenarios)} 个场景")
    
    logger.info(f"总共生成 {total_count} 个场景")
    
    # 统计信息
    statistics = rater.get_statistics(all_scenarios)
    logger.info(f"难度分布: {statistics['difficulty_distribution']}")
    logger.info(f"平均难度分数: {statistics['average_score']:.2f}")
    logger.info(f"难度因素分布: {statistics['factor_distribution']}")
    
    # 保存场景到JSON
    for scenario in all_scenarios:
        scenario_path = os.path.join(output_dir, f"{scenario['id']}.json")
        with open(scenario_path, 'w', encoding='utf-8') as f:
            json.dump(scenario, f, indent=2, ensure_ascii=False)
        
        # 保存到场景库
        library.save_scenario(scenario)
    
    logger.info(f"场景已保存到: {output_dir}")
    
    # 导出OpenSCENARIO格式
    logger.info("导出OpenSCENARIO格式...")
    exporter.export_batch(all_scenarios, openscenario_dir)
    
    # 保存统计信息
    stats_path = os.path.join(output_dir, 'statistics.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(statistics, f, indent=2, ensure_ascii=False)
    
    logger.info(f"统计信息已保存到: {stats_path}")
    
    # 生成报告
    report = generate_report(all_scenarios, statistics)
    report_path = os.path.join(output_dir, 'generation_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"生成报告已保存到: {report_path}")
    
    logger.info("=" * 60)
    logger.info("批量生成完成！")
    logger.info("=" * 60)

def generate_report(scenarios, statistics):
    """生成报告"""
    report = f"""# 无保护左转场景生成报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概述

- **总场景数**: {len(scenarios)}
- **场景类型**: 无保护左转 (Unprotected Left Turn)
- **格式**: JSON + OpenSCENARIO

## 难度分布

| 难度等级 | 数量 | 占比 |
|----------|------|------|
| 简单 (Easy) | {statistics['difficulty_distribution']['easy']} | {statistics['difficulty_distribution']['easy']/len(scenarios)*100:.1f}% |
| 中等 (Medium) | {statistics['difficulty_distribution']['medium']} | {statistics['difficulty_distribution']['medium']/len(scenarios)*100:.1f}% |
| 困难 (Hard) | {statistics['difficulty_distribution']['hard']} | {statistics['difficulty_distribution']['hard']/len(scenarios)*100:.1f}% |
| 地狱 (Extreme) | {statistics['difficulty_distribution']['extreme']} | {statistics['difficulty_distribution']['extreme']/len(scenarios)*100:.1f}% |

## 难度因素分布

"""
    
    # 添加难度因素
    for factor, count in statistics['factor_distribution'].items():
        report += f"- **{factor}**: {count} 个场景\n"
    
    report += f"""
## 平均难度分数

{statistics['average_score']:.2f} (0-1，越高越难）

## 场景参数范围

- 主车速度: 30-80 km/h
- 对向来车速度: 40-90 km/h
- 间隙时间: 2.0-5.0 秒
- 对向来车数量: 1-3 辆
- 天气条件: clear, rain, fog, night, rain_night
- 能见度: 100-300 米
- 道路宽度: 3.5-4.5 米

## 文件结构

```
scenarios/unprotected_left_turn/
├── *.json              # 场景JSON文件
├── statistics.json      # 统计信息
└── generation_report.md # 生成报告

openscenario/unprotected_left_turn/
└── *.xosc             # OpenSCENARIO格式文件
```

## 使用方法

### 1. 加载场景

```python
from library.scene_library import SceneLibrary

library = SceneLibrary('./scenarios')
scenarios = library.load_all_scenarios('unprotected_left_turn')
```

### 2. 执行测试

```python
from executors.unprotected_left_turn_executor import UnprotectedLeftTurnExecutor

executor = UnprotectedLeftTurnExecutor()
results = executor.execute_batch(scenarios)
```

### 3. 导入OpenSCENARIO

将OpenSCENARIO文件导入CARLA或其他仿真工具。

## 注意事项

1. 确保CARLA服务器正在运行
2. 根据实际硬件调整场景数量
3. 建议先测试少量场景，确认无误后再批量执行
4. 定期备份场景库和测试结果

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report

if __name__ == '__main__':
    main()
