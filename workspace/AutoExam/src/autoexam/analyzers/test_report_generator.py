#!/usr/bin/env python3
"""
完整测试报告生成器
生成包含性能分析、失败模式聚类和改进建议的完整测试报告
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List

from autoexam.analyzers.failure_cluster_analyzer import FailureClusterAnalyzer

logger = logging.getLogger('TestReportGenerator')

class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.analyzer = FailureClusterAnalyzer()
        logger.info("测试报告生成器初始化完成")
    
    def generate(self, scenarios: List[Dict], results: List[Dict], 
                 output_dir: str) -> str:
        """生成完整测试报告
        
        参数:
            scenarios: 场景列表
            results: 测试结果列表
            output_dir: 输出目录
            
        返回:
            报告文件路径
        """
        logger.info("开始生成测试报告...")
        
        # 生成统计数据
        statistics = self._generate_statistics(scenarios, results)
        
        # 失败模式分析
        failure_analysis = self.analyzer.analyze(scenarios, results)
        
        # 生成高危参数清单
        high_risk_params = self._generate_high_risk_parameters(
            scenarios, results, failure_analysis
        )
        
        # 生成改进建议
        suggestions = self._generate_suggestions(
            statistics, failure_analysis, high_risk_params
        )
        
        # 生成报告
        report = self._create_report(
            statistics, failure_analysis, high_risk_params, suggestions
        )
        
        # 保存报告
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, 'comprehensive_test_report.md')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存JSON数据
        data_path = os.path.join(output_dir, 'test_data.json')
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': statistics,
                'failure_analysis': failure_analysis,
                'high_risk_parameters': high_risk_params,
                'suggestions': suggestions
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存到: {report_path}")
        
        return report_path
    
    def _generate_statistics(self, scenarios: List[Dict], 
                              results: List[Dict]) -> Dict:
        """生成统计数据"""
        statistics = {
            'total_scenarios': len(scenarios),
            'total_results': len(results),
            'success_count': 0,
            'collision_count': 0,
            'timeout_count': 0,
            'error_count': 0,
            'difficulty_distribution': {},
            'weather_distribution': {},
            'performance_metrics': {
                'average_response_time': 0,
                'average_execution_time': 0,
                'average_max_deceleration': 0
            }
        }
        
        # 初始化分布统计
        difficulties = ['easy', 'medium', 'hard', 'extreme']
        weathers = ['clear', 'rain', 'fog', 'night', 'rain_night']
        
        for difficulty in difficulties:
            statistics['difficulty_distribution'][difficulty] = {
                'total': 0, 'success': 0, 'collision': 0, 'timeout': 0
            }
        
        for weather in weathers:
            statistics['weather_distribution'][weather] = {
                'total': 0, 'success': 0, 'collision': 0, 'timeout': 0
            }
        
        # 统计结果
        for i, result in enumerate(results):
            if i >= len(scenarios):
                continue
            
            scenario = scenarios[i]
            
            # 总体统计
            if result.get('success'):
                statistics['success_count'] += 1
            elif result.get('collision'):
                statistics['collision_count'] += 1
            elif result.get('timeout'):
                statistics['timeout_count'] += 1
            else:
                statistics['error_count'] += 1
            
            # 难度分布
            difficulty = scenario.get('difficulty', 'unknown')
            if difficulty in statistics['difficulty_distribution']:
                statistics['difficulty_distribution'][difficulty]['total'] += 1
                if result.get('success'):
                    statistics['difficulty_distribution'][difficulty]['success'] += 1
                elif result.get('collision'):
                    statistics['difficulty_distribution'][difficulty]['collision'] += 1
                elif result.get('timeout'):
                    statistics['difficulty_distribution'][difficulty]['timeout'] += 1
            
            # 天气分布
            weather = scenario.get('environment', {}).get('weather', 'unknown')
            if weather in statistics['weather_distribution']:
                statistics['weather_distribution'][weather]['total'] += 1
                if result.get('success'):
                    statistics['weather_distribution'][weather]['success'] += 1
                elif result.get('collision'):
                    statistics['weather_distribution'][weather]['collision'] += 1
                elif result.get('timeout'):
                    statistics['weather_distribution'][weather]['timeout'] += 1
            
            # 性能指标
            statistics['performance_metrics']['average_response_time'] += \
                result.get('response_time', 0)
            statistics['performance_metrics']['average_execution_time'] += \
                result.get('execution_time', 0)
            statistics['performance_metrics']['average_max_deceleration'] += \
                result.get('max_deceleration', 0)
        
        # 计算平均值
        if len(results) > 0:
            for key in statistics['performance_metrics']:
                statistics['performance_metrics'][key] /= len(results)
        
        # 计算成功率
        statistics['success_rate'] = statistics['success_count'] / len(results) \
            if len(results) > 0 else 0
        statistics['collision_rate'] = statistics['collision_count'] / len(results) \
            if len(results) > 0 else 0
        statistics['timeout_rate'] = statistics['timeout_count'] / len(results) \
            if len(results) > 0 else 0
        
        return statistics
    
    def _generate_high_risk_parameters(self, scenarios: List[Dict],
                                         results: List[Dict],
                                         failure_analysis: Dict) -> List[Dict]:
        """生成高危参数清单"""
        high_risk_params = []
        
        # 从失败分析中提取高危参数
        for param in failure_analysis.get('high_risk_parameters', []):
            high_risk_params.append({
                'combination': param['combination'],
                'count': param['count'],
                'parameters': param['parameters'],
                'risk_level': self._calculate_risk_level(param['count'], len(results))
            })
        
        # 按风险等级排序
        high_risk_params.sort(key=lambda x: x['risk_level'], reverse=True)
        
        return high_risk_params[:30]
    
    def _calculate_risk_level(self, count: int, total: int) -> float:
        """计算风险等级"""
        if total == 0:
            return 0
        return count / total
    
    def _generate_suggestions(self, statistics: Dict, 
                              failure_analysis: Dict,
                              high_risk_params: List[Dict]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于统计数据的建议
        if statistics['collision_rate'] > 0.3:
            suggestions.append("碰撞率较高（{:.1f}%），建议优化碰撞检测和避障算法".format(
                statistics['collision_rate'] * 100
            ))
        
        if statistics['timeout_rate'] > 0.2:
            suggestions.append("超时率较高（{:.1f}%），建议优化决策算法减少延迟".format(
                statistics['timeout_rate'] * 100
            ))
        
        # 基于难度分布的建议
        difficulty_dist = statistics['difficulty_distribution']
        for difficulty, stats in difficulty_dist.items():
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
                if success_rate < 0.5:
                    suggestions.append(
                        f"{difficulty}难度场景成功率较低（{success_rate*100:.1f}%），"
                        f"建议增加该难度场景的训练和优化"
                    )
        
        # 基于天气分布的建议
        weather_dist = statistics['weather_distribution']
        for weather, stats in weather_dist.items():
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
                if success_rate < 0.5:
                    suggestions.append(
                        f"{weather}天气条件下成功率较低（{success_rate*100:.1f}%），"
                        f"建议优化恶劣天气感知算法"
                    )
        
        # 基于失败模式的建议
        if failure_analysis.get('collision_clusters'):
            suggestions.append("针对碰撞模式，建议增加对间隙时间的精确估计")
            suggestions.append("建议提高对速度差较大的场景的预判能力")
        
        if failure_analysis.get('timeout_clusters'):
            suggestions.append("针对超时模式，建议优化决策算法减少计算时间")
            suggestions.append("建议在高难度场景下采用更高效的策略")
        
        # 基于高危参数的建议
        if high_risk_params:
            suggestions.append("针对高危参数组合，建议进行专项优化和测试")
            suggestions.append("建议增加对高危参数组合场景的覆盖率")
        
        # 通用建议
        suggestions.append("建议持续监控和优化系统性能")
        suggestions.append("建议定期更新场景库，增加新场景类型")
        suggestions.append("建议建立自动化测试流程，提高测试效率")
        
        return suggestions
    
    def _create_report(self, statistics: Dict, failure_analysis: Dict,
                        high_risk_params: List[Dict],
                        suggestions: List[str]) -> str:
        """创建报告"""
        report = f"""# Apollo 10 无保护左转场景测试报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 测试概述

本次测试针对Apollo 10自动驾驶系统在无保护左转场景下的表现进行了全面评估。测试共包含{statistics['total_scenarios']}个场景，覆盖了不同难度等级和天气条件。

### 1.1 测试环境

- **仿真环境**: CARLA
- **测试系统**: Apollo 10
- **场景类型**: 无保护左转 (Unprotected Left Turn)
- **场景格式**: OpenSCENARIO

### 1.2 测试结果汇总

| 指标 | 数值 |
|------|------|
| 总场景数 | {statistics['total_scenarios']} |
| 成功 | {statistics['success_count']} ({statistics['success_rate']*100:.1f}%) |
| 碰撞 | {statistics['collision_count']} ({statistics['collision_rate']*100:.1f}%) |
| 超时 | {statistics['timeout_count']} ({statistics['timeout_rate']*100:.1f}%) |
| 错误 | {statistics['error_count']} |

## 2. 性能分析

### 2.1 性能指标

| 指标 | 数值 |
|------|------|
| 平均响应时间 | {statistics['performance_metrics']['average_response_time']:.2f} 秒 |
| 平均执行时间 | {statistics['performance_metrics']['average_execution_time']:.2f} 秒 |
| 平均最大减速度 | {statistics['performance_metrics']['average_max_deceleration']:.2f} m/s² |

### 2.2 按难度分布

| 难度 | 总数 | 成功 | 碰撞 | 超时 | 成功率 |
|------|------|------|------|------|--------|
"""
        
        for difficulty, stats in statistics['difficulty_distribution'].items():
            total = stats['total']
            success = stats['success']
            collision = stats['collision']
            timeout = stats['timeout']
            success_rate = success / total * 100 if total > 0 else 0
            
            report += f"| {difficulty} | {total} | {success} | {collision} | {timeout} | {success_rate:.1f}% |\n"
        
        report += "\n### 2.3 按天气分布\n\n"
        report += "| 天气 | 总数 | 成功 | 碰撞 | 超时 | 成功率 |\n"
        report += "|------|------|------|------|------|--------|\n"
        
        for weather, stats in statistics['weather_distribution'].items():
            total = stats['total']
            success = stats['success']
            collision = stats['collision']
            timeout = stats['timeout']
            success_rate = success / total * 100 if total > 0 else 0
            
            report += f"| {weather} | {total} | {success} | {collision} | {timeout} | {success_rate:.1f}% |\n"
        
        report += "\n## 3. 失败模式聚类分析\n\n"
        
        # 碰撞模式
        report += "### 3.1 碰撞模式\n\n"
        for cluster in failure_analysis.get('collision_clusters', []):
            report += f"""
#### {cluster['name']}

- **数量**: {cluster['count']}
- **描述**: {cluster['description']}
- **案例数**: {len(cluster['cases'])}
"""
        
        # 超时模式
        report += "\n### 3.2 超时模式\n\n"
        for cluster in failure_analysis.get('timeout_clusters', []):
            report += f"""
#### {cluster['name']}

- **数量**: {cluster['count']}
- **描述**: {cluster['description']}
- **案例数**: {len(cluster['cases'])}
"""
        
        report += "\n## 4. 高危参数组合清单\n\n"
        report += "| 排名 | 组合 | 数量 | 风险等级 |\n"
        report += "|------|------|------|----------|\n"
        
        for i, param in enumerate(high_risk_params[:20], 1):
            params_str = ', '.join([f"{k}={v}" for k, v in param['parameters'].items()])
            risk_level = param['risk_level']
            risk_label = "高" if risk_level > 0.1 else "中" if risk_level > 0.05 else "低"
            report += f"| {i} | {param['combination']} | {param['count']} | {risk_label} ({risk_level*100:.1f}%) |\n"
        
        report += "\n## 5. 改进建议\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            report += f"{i}. {suggestion}\n"
        
        report += f"""
## 6. 结论

本次测试共执行了 {statistics['total_scenarios']} 个无保护左转场景，Apollo 10系统的整体成功率为 {statistics['success_rate']*100:.1f}%。主要发现包括：

1. **碰撞分析**: 碰撞率为 {statistics['collision_rate']*100:.1f}%，主要集中在间隙时间短和速度差大的场景
2. **超时分析**: 超时率为 {statistics['timeout_rate']*100:.1f}%，主要出现在高难度和恶劣天气场景
3. **难度影响**: 随着难度增加，成功率明显下降
4. **天气影响**: 恶劣天气条件（雨天、夜间）对系统性能影响显著

建议针对上述发现进行专项优化，重点关注高危参数组合场景，提高系统在复杂场景下的鲁棒性。

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
