#!/usr/bin/env python3
"""
CARLA集成测试 - 模拟模式
当CARLA不可用时使用模拟数据测试
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import random

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from autoexam.generators import UnprotectedLeftTurnGenerator
from autoexam.analyzers import DifficultyRater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CarlaSimulationTest')

def simulate_scenario_execution(scenario):
    """模拟场景执行
    
    参数:
        scenario: 场景字典
        
    返回:
        模拟的测试结果
    """
    params = scenario['parameters']
    
    difficulty = scenario.get('difficulty', 'medium')
    
    collision_probability = {
        'easy': 0.1,
        'medium': 0.3,
        'hard': 0.6,
        'extreme': 0.9
    }.get(difficulty, 0.3)
    
    collision = random.random() < collision_probability
    
    execution_time = random.uniform(8, 25)
    
    trajectory_data = []
    num_points = int(execution_time * 20)
    
    for i in range(num_points):
        t = i / num_points
        trajectory_data.append({
            'time': t * execution_time,
            'location': {
                'x': -50 + t * 100,
                'y': random.uniform(-2, 2),
                'z': 0.5
            },
            'velocity': {
                'x': params.get('ego_speed', 15) / 3.6 * (0.8 + 0.4 * random.random()),
                'y': random.uniform(-1, 1),
                'z': 0
            },
            'rotation': {
                'pitch': random.uniform(-1, 1),
                'yaw': random.uniform(-5, 5),
                'roll': random.uniform(-1, 1)
            }
        })
    
    result = {
        'success': True,
        'collision': collision,
        'execution_time': execution_time,
        'collision_count': 1 if collision else 0,
        'trajectory_data': trajectory_data,
        'scenario_id': scenario.get('id'),
        'scenario_type': scenario.get('type', 'unprotected_left_turn'),
        'parameters': params,
        'timestamp': datetime.now().isoformat(),
        'environment': 'SIMULATION'
    }
    
    if collision:
        result['collision_details'] = [{
            'time': execution_time * random.uniform(0.5, 0.9),
            'other_actor': 'vehicle.tesla.model3',
            'impulse': {'x': 100, 'y': 50, 'z': 0}
        }]
    
    return result

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CARLA仿真集成测试（模拟模式）')
    parser.add_argument('--count', type=int, default=5, help='测试场景数量')
    parser.add_argument('--weather', type=str, default='clear', 
                       choices=['clear', 'rain', 'fog', 'night'], help='天气条件')
    parser.add_argument('--session', type=str, help='会话名称')
    parser.add_argument('--output', type=str, help='输出目录')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("CARLA仿真集成测试（模拟模式）")
    logger.info("=" * 60)
    
    data_dir = os.path.join(project_root, 'data')
    results_dir = args.output if args.output else os.path.join(data_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    generator = UnprotectedLeftTurnGenerator(use_llm=False)
    difficulty_rater = DifficultyRater()
    
    session_name = args.session if args.session else f"sim_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"生成{args.count}个测试场景...")
    scenarios = generator.generate(
        count=args.count,
        difficulty='medium',
        weather=args.weather
    )
    
    logger.info(f"成功生成{len(scenarios)}个场景")
    
    results = []
    logger.info("开始执行场景测试（模拟）...")
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"\n[{i}/{len(scenarios)}] 测试场景: {scenario.get('id')}")
        
        difficulty = difficulty_rater.rate(scenario)
        scenario['difficulty'] = difficulty['difficulty_level']
        
        result = simulate_scenario_execution(scenario)
        results.append(result)
        
        logger.info(f"  结果: 碰撞={result.get('collision')}, 耗时={result.get('execution_time', 0):.2f}s")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)
    
    total = len(results)
    collisions = sum(1 for r in results if r.get('collision', False))
    successes = total - collisions
    execution_times = [r.get('execution_time', 0) for r in results]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    
    logger.info(f"统计结果:")
    logger.info(f"  总场景数: {total}")
    logger.info(f"  碰撞数: {collisions}")
    logger.info(f"  成功数: {successes}")
    logger.info(f"  碰撞率: {collisions/total:.2%}" if total > 0 else "  碰撞率: 0%")
    logger.info(f"  成功率: {successes/total:.2%}" if total > 0 else "  成功率: 0%")
    logger.info(f"  平均执行时间: {avg_execution_time:.2f}s")
    
    filepath = os.path.join(results_dir, f"{session_name}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n结果已保存: {filepath}")
    
    import csv
    csv_path = os.path.join(results_dir, f"{session_name}.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['scenario_id', 'collision', 'execution_time', 'difficulty', 'weather'])
        for r in results:
            writer.writerow([
                r.get('scenario_id'),
                r.get('collision'),
                f"{r.get('execution_time', 0):.2f}",
                r.get('parameters', {}).get('weather', 'unknown'),
                r.get('difficulty', 'unknown')
            ])
    
    logger.info(f"CSV已保存: {csv_path}")
    
    report = f"""
# 仿真测试报告（模拟模式）

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计概览

- **总场景数**: {total}
- **碰撞数**: {collisions}
- **成功数**: {successes}
- **碰撞率**: {collisions/total:.2%}
- **成功率**: {successes/total:.2%}
- **平均执行时间**: {avg_execution_time:.2f}s

## 详细结果

"""
    
    for i, result in enumerate(results, 1):
        report += f"""
### 场景 {i}: {result.get('scenario_id', 'unknown')}

- **类型**: {result.get('scenario_type', 'unknown')}
- **难度**: {result.get('difficulty', 'unknown')}
- **碰撞**: {'是' if result.get('collision') else '否'}
- **执行时间**: {result.get('execution_time', 0):.2f}s
- **天气**: {result.get('parameters', {}).get('weather', 'unknown')}
- **时间**: {result.get('timestamp', 'unknown')}
"""
    
    report_path = os.path.join(results_dir, f"{session_name}_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"报告已保存: {report_path}")
    
    logger.info("\n✅ 测试完成！")
    logger.info("\n提示: 要使用真实CARLA仿真，请:")
    logger.info("1. 确保CARLA服务器正在运行")
    logger.info("2. 设置PYTHONPATH环境变量")
    logger.info("3. 使用 test_carla_integration.py 脚本")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
