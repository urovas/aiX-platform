#!/usr/bin/env python3
"""
批量执行无保护左转场景测试
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.scene_library import SceneLibrary
from executors.unprotected_left_turn_executor import UnprotectedLeftTurnExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BatchTester')

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("批量执行无保护左转场景测试")
    logger.info("=" * 60)
    
    # 初始化组件
    library = SceneLibrary('./scenarios')
    executor = UnprotectedLeftTurnExecutor()
    
    # 加载场景
    logger.info("加载场景...")
    scenarios = library.load_all_scenarios('unprotected_left_turn')
    logger.info(f"加载了 {len(scenarios)} 个场景")
    
    # 创建输出目录
    output_dir = './results/unprotected_left_turn'
    os.makedirs(output_dir, exist_ok=True)
    
    # 执行测试
    logger.info("开始执行测试...")
    results = executor.execute_batch(scenarios)
    
    # 保存结果
    logger.info("保存测试结果...")
    
    # 保存单个结果
    for i, result in enumerate(results):
        result_path = os.path.join(output_dir, f"result_{i:04d}.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    # 保存汇总结果
    summary = generate_summary(scenarios, results)
    summary_path = os.path.join(output_dir, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"测试结果已保存到: {output_dir}")
    
    # 生成报告
    report = generate_test_report(scenarios, results, summary)
    report_path = os.path.join(output_dir, 'test_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"测试报告已保存到: {report_path}")
    
    logger.info("=" * 60)
    logger.info("批量测试完成！")
    logger.info("=" * 60)

def generate_summary(scenarios, results):
    """生成测试汇总"""
    summary = {
        'total_scenarios': len(scenarios),
        'total_results': len(results),
        'success_count': 0,
        'collision_count': 0,
        'timeout_count': 0,
        'error_count': 0,
        'difficulty_distribution': {
            'easy': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'medium': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'hard': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'extreme': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0}
        },
        'weather_distribution': {
            'clear': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'rain': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'fog': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'night': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0},
            'rain_night': {'total': 0, 'success': 0, 'collision': 0, 'timeout': 0}
        },
        'average_response_time': 0,
        'average_execution_time': 0,
        'average_max_deceleration': 0
    }
    
    # 统计结果
    for i, result in enumerate(results):
        scenario = scenarios[i] if i < len(scenarios) else {}
        
        # 总体统计
        if result.get('success'):
            summary['success_count'] += 1
        elif result.get('collision'):
            summary['collision_count'] += 1
        elif result.get('timeout'):
            summary['timeout_count'] += 1
        else:
            summary['error_count'] += 1
        
        # 难度分布
        difficulty = scenario.get('difficulty', 'unknown')
        if difficulty in summary['difficulty_distribution']:
            summary['difficulty_distribution'][difficulty]['total'] += 1
            if result.get('success'):
                summary['difficulty_distribution'][difficulty]['success'] += 1
            elif result.get('collision'):
                summary['difficulty_distribution'][difficulty]['collision'] += 1
            elif result.get('timeout'):
                summary['difficulty_distribution'][difficulty]['timeout'] += 1
        
        # 天气分布
        weather = scenario.get('environment', {}).get('weather', 'unknown')
        if weather in summary['weather_distribution']:
            summary['weather_distribution'][weather]['total'] += 1
            if result.get('success'):
                summary['weather_distribution'][weather]['success'] += 1
            elif result.get('collision'):
                summary['weather_distribution'][weather]['collision'] += 1
            elif result.get('timeout'):
                summary['weather_distribution'][weather]['timeout'] += 1
        
        # 性能指标
        summary['average_response_time'] += result.get('response_time', 0)
        summary['average_execution_time'] += result.get('execution_time', 0)
        summary['average_max_deceleration'] += result.get('max_deceleration', 0)
    
    # 计算平均值
    if len(results) > 0:
        summary['average_response_time'] /= len(results)
        summary['average_execution_time'] /= len(results)
        summary['average_max_deceleration'] /= len(results)
    
    # 计算成功率
    summary['success_rate'] = summary['success_count'] / len(results) if len(results) > 0 else 0
    summary['collision_rate'] = summary['collision_count'] / len(results) if len(results) > 0 else 0
    summary['timeout_rate'] = summary['timeout_count'] / len(results) if len(results) > 0 else 0
    
    return summary

def generate_test_report(scenarios, results, summary):
    """生成测试报告"""
    report = f"""# 无保护左转场景测试报告

测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概述

- **总场景数**: {summary['total_scenarios']}
- **测试结果数**: {summary['total_results']}
- **成功**: {summary['success_count']} ({summary['success_rate']*100:.1f}%)
- **碰撞**: {summary['collision_count']} ({summary['collision_rate']*100:.1f}%)
- **超时**: {summary['timeout_count']} ({summary['timeout_rate']*100:.1f}%)
- **错误**: {summary['error_count']}

## 性能指标

- **平均响应时间**: {summary['average_response_time']:.2f} 秒
- **平均执行时间**: {summary['average_execution_time']:.2f} 秒
- **平均最大减速度**: {summary['average_max_deceleration']:.2f} m/s²

## 按难度分布

| 难度 | 总数 | 成功 | 碰撞 | 超时 | 成功率 |
|------|------|------|------|------|--------|
"""
    
    for difficulty, stats in summary['difficulty_distribution'].items():
        total = stats['total']
        success = stats['success']
        collision = stats['collision']
        timeout = stats['timeout']
        success_rate = success / total * 100 if total > 0 else 0
        
        report += f"| {difficulty} | {total} | {success} | {collision} | {timeout} | {success_rate:.1f}% |\n"
    
    report += "\n## 按天气分布\n\n"
    report += "| 天气 | 总数 | 成功 | 碰撞 | 超时 | 成功率 |\n"
    report += "|------|------|------|------|------|--------|\n"
    
    for weather, stats in summary['weather_distribution'].items():
        total = stats['total']
        success = stats['success']
        collision = stats['collision']
        timeout = stats['timeout']
        success_rate = success / total * 100 if total > 0 else 0
        
        report += f"| {weather} | {total} | {success} | {collision} | {timeout} | {success_rate:.1f}% |\n"
    
    report += f"""
## 失败案例分析

### 碰撞案例
"""
    
    # 添加碰撞案例
    collision_count = 0
    for i, result in enumerate(results):
        if result.get('collision'):
            scenario = scenarios[i] if i < len(scenarios) else {}
            collision_count += 1
            if collision_count <= 10:  # 只显示前10个
                report += f"""
#### 案例 {collision_count}: {scenario.get('id', 'unknown')}
- **场景ID**: {scenario.get('id', 'unknown')}
- **难度**: {scenario.get('difficulty', 'unknown')}
- **天气**: {scenario.get('environment', {}).get('weather', 'unknown')}
- **间隙时间**: {scenario.get('parameters', {}).get('gap_time', 'N/A')} 秒
- **主车速度**: {scenario.get('ego_vehicle', {}).get('initial_speed', 'N/A')} km/h
- **对向来车速度**: {scenario.get('parameters', {}).get('oncoming_speed', 'N/A')} km/h
- **碰撞时间**: {result.get('collision_time', 'N/A')} 秒
- **响应时间**: {result.get('response_time', 'N/A')} 秒
"""
    
    report += f"""
### 超时案例
"""
    
    # 添加超时案例
    timeout_count = 0
    for i, result in enumerate(results):
        if result.get('timeout'):
            scenario = scenarios[i] if i < len(scenarios) else {}
            timeout_count += 1
            if timeout_count <= 10:  # 只显示前10个
                report += f"""
#### 案例 {timeout_count}: {scenario.get('id', 'unknown')}
- **场景ID**: {scenario.get('id', 'unknown')}
- **难度**: {scenario.get('difficulty', 'unknown')}
- **天气**: {scenario.get('environment', {}).get('weather', 'unknown')}
- **间隙时间**: {scenario.get('parameters', {}).get('gap_time', 'N/A')} 秒
- **执行时间**: {result.get('execution_time', 'N/A')} 秒
"""
    
    report += """
## 结论

本次测试共执行了 {0} 个无保护左转场景，成功率为 {1:.1f}%。主要失败原因包括碰撞和超时，需要进一步分析失败模式并优化算法。

---
*报告生成时间: {2}*
""".format(
        summary['total_results'],
        summary['success_rate'] * 100,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    return report

if __name__ == '__main__':
    main()
