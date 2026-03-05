#!/usr/bin/env python3
"""
失败模式聚类分析器
分析测试结果中的失败模式并进行聚类
"""

import os
import json
import logging
from typing import Dict, List
from collections import defaultdict

logger = logging.getLogger('FailureClusterAnalyzer')

class FailureClusterAnalyzer:
    """失败模式聚类分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.clusters = []
        logger.info("失败模式聚类分析器初始化完成")
    
    def analyze(self, scenarios: List[Dict], results: List[Dict]) -> Dict:
        """分析失败模式
        
        参数:
            scenarios: 场景列表
            results: 测试结果列表
            
        返回:
            分析结果
        """
        logger.info("开始分析失败模式...")
        
        # 提取失败案例
        failure_cases = self._extract_failure_cases(scenarios, results)
        logger.info(f"找到 {len(failure_cases)} 个失败案例")
        
        # 按失败类型分类
        collision_cases = [c for c in failure_cases if c['failure_type'] == 'collision']
        timeout_cases = [c for c in failure_cases if c['failure_type'] == 'timeout']
        
        # 聚类分析
        collision_clusters = self._cluster_collision_cases(collision_cases)
        timeout_clusters = self._cluster_timeout_cases(timeout_cases)
        
        # 生成高危参数组合
        high_risk_params = self._identify_high_risk_parameters(failure_cases)
        
        # 生成改进建议
        suggestions = self._generate_suggestions(collision_clusters, timeout_clusters, high_risk_params)
        
        analysis_result = {
            'total_failures': len(failure_cases),
            'collision_count': len(collision_cases),
            'timeout_count': len(timeout_cases),
            'collision_clusters': collision_clusters,
            'timeout_clusters': timeout_clusters,
            'high_risk_parameters': high_risk_params,
            'suggestions': suggestions
        }
        
        logger.info("失败模式分析完成")
        
        return analysis_result
    
    def _extract_failure_cases(self, scenarios: List[Dict], results: List[Dict]) -> List[Dict]:
        """提取失败案例"""
        failure_cases = []
        
        for i, result in enumerate(results):
            if i >= len(scenarios):
                continue
            
            scenario = scenarios[i]
            
            if result.get('collision'):
                failure_cases.append({
                    'index': i,
                    'scenario_id': scenario.get('id'),
                    'failure_type': 'collision',
                    'scenario': scenario,
                    'result': result,
                    'features': self._extract_features(scenario, result)
                })
            elif result.get('timeout'):
                failure_cases.append({
                    'index': i,
                    'scenario_id': scenario.get('id'),
                    'failure_type': 'timeout',
                    'scenario': scenario,
                    'result': result,
                    'features': self._extract_features(scenario, result)
                })
        
        return failure_cases
    
    def _extract_features(self, scenario: Dict, result: Dict) -> Dict:
        """提取特征"""
        params = scenario.get('parameters', {})
        environment = scenario.get('environment', {})
        ego_vehicle = scenario.get('ego_vehicle', {})
        
        return {
            'gap_time': params.get('gap_time', 3.0),
            'oncoming_speed': params.get('oncoming_speed', 60),
            'ego_speed': ego_vehicle.get('initial_speed', 50),
            'oncoming_vehicle_count': params.get('oncoming_vehicle_count', 1),
            'cross_traffic': params.get('cross_traffic', False),
            'pedestrian_present': params.get('pedestrian_present', False),
            'weather': environment.get('weather', 'clear'),
            'visibility': environment.get('visibility', 200),
            'difficulty': scenario.get('difficulty', 'medium'),
            'response_time': result.get('response_time', 0),
            'execution_time': result.get('execution_time', 0),
            'max_deceleration': result.get('max_deceleration', 0)
        }
    
    def _cluster_collision_cases(self, cases: List[Dict]) -> List[Dict]:
        """聚类碰撞案例"""
        if not cases:
            return []
        
        clusters = []
        
        # 按间隙时间分组
        gap_time_groups = defaultdict(list)
        for case in cases:
            gap_time = case['features']['gap_time']
            if gap_time < 2.5:
                gap_time_groups['very_short'].append(case)
            elif gap_time < 3.0:
                gap_time_groups['short'].append(case)
            elif gap_time < 3.5:
                gap_time_groups['medium'].append(case)
            else:
                gap_time_groups['long'].append(case)
        
        # 按速度差分组
        speed_diff_groups = defaultdict(list)
        for case in cases:
            ego_speed = case['features']['ego_speed']
            oncoming_speed = case['features']['oncoming_speed']
            speed_diff = abs(ego_speed - oncoming_speed)
            
            if speed_diff < 15:
                speed_diff_groups['low'].append(case)
            elif speed_diff < 30:
                speed_diff_groups['medium'].append(case)
            else:
                speed_diff_groups['high'].append(case)
        
        # 按天气分组
        weather_groups = defaultdict(list)
        for case in cases:
            weather = case['features']['weather']
            weather_groups[weather].append(case)
        
        # 生成聚类
        for gap_time_key, gap_time_cases in gap_time_groups.items():
            if len(gap_time_cases) >= 3:
                clusters.append({
                    'type': 'collision',
                    'name': f'间隙时间{gap_time_key}',
                    'count': len(gap_time_cases),
                    'description': f'间隙时间{gap_time_key}导致的碰撞',
                    'gap_time_range': self._get_gap_time_range(gap_time_key),
                    'cases': [c['scenario_id'] for c in gap_time_cases]
                })
        
        for speed_diff_key, speed_diff_cases in speed_diff_groups.items():
            if len(speed_diff_cases) >= 3:
                clusters.append({
                    'type': 'collision',
                    'name': f'速度差{speed_diff_key}',
                    'count': len(speed_diff_cases),
                    'description': f'速度差{speed_diff_key}导致的碰撞',
                    'speed_diff_range': self._get_speed_diff_range(speed_diff_key),
                    'cases': [c['scenario_id'] for c in speed_diff_cases]
                })
        
        for weather_key, weather_cases in weather_groups.items():
            if len(weather_cases) >= 3:
                clusters.append({
                    'type': 'collision',
                    'name': f'{weather_key}天气',
                    'count': len(weather_cases),
                    'description': f'{weather_key}天气条件下的碰撞',
                    'weather': weather_key,
                    'cases': [c['scenario_id'] for c in weather_cases]
                })
        
        return clusters
    
    def _cluster_timeout_cases(self, cases: List[Dict]) -> List[Dict]:
        """聚类超时案例"""
        if not cases:
            return []
        
        clusters = []
        
        # 按难度分组
        difficulty_groups = defaultdict(list)
        for case in cases:
            difficulty = case['features']['difficulty']
            difficulty_groups[difficulty].append(case)
        
        # 按天气分组
        weather_groups = defaultdict(list)
        for case in cases:
            weather = case['features']['weather']
            weather_groups[weather].append(case)
        
        # 按对向来车数量分组
        vehicle_count_groups = defaultdict(list)
        for case in cases:
            count = case['features']['oncoming_vehicle_count']
            if count == 1:
                vehicle_count_groups['single'].append(case)
            elif count == 2:
                vehicle_count_groups['double'].append(case)
            else:
                vehicle_count_groups['multiple'].append(case)
        
        # 生成聚类
        for difficulty_key, difficulty_cases in difficulty_groups.items():
            if len(difficulty_cases) >= 3:
                clusters.append({
                    'type': 'timeout',
                    'name': f'{difficulty_key}难度',
                    'count': len(difficulty_cases),
                    'description': f'{difficulty_key}难度场景下的超时',
                    'difficulty': difficulty_key,
                    'cases': [c['scenario_id'] for c in difficulty_cases]
                })
        
        for weather_key, weather_cases in weather_groups.items():
            if len(weather_cases) >= 3:
                clusters.append({
                    'type': 'timeout',
                    'name': f'{weather_key}天气',
                    'count': len(weather_cases),
                    'description': f'{weather_key}天气条件下的超时',
                    'weather': weather_key,
                    'cases': [c['scenario_id'] for c in weather_cases]
                })
        
        for vehicle_count_key, vehicle_count_cases in vehicle_count_groups.items():
            if len(vehicle_count_cases) >= 3:
                clusters.append({
                    'type': 'timeout',
                    'name': f'{vehicle_count_key}车辆',
                    'count': len(vehicle_count_cases),
                    'description': f'{vehicle_count_key}对向来车导致的超时',
                    'vehicle_count': vehicle_count_key,
                    'cases': [c['scenario_id'] for c in vehicle_count_cases]
                })
        
        return clusters
    
    def _identify_high_risk_parameters(self, failure_cases: List[Dict]) -> List[Dict]:
        """识别高危参数组合"""
        high_risk_params = []
        
        # 统计参数组合
        param_combinations = defaultdict(int)
        
        for case in failure_cases:
            features = case['features']
            
            # 间隙时间 + 天气
            key1 = f"gap_time_{features['gap_time']:.1f}_weather_{features['weather']}"
            param_combinations[key1] += 1
            
            # 间隙时间 + 难度
            key2 = f"gap_time_{features['gap_time']:.1f}_difficulty_{features['difficulty']}"
            param_combinations[key2] += 1
            
            # 速度差 + 天气
            speed_diff = abs(features['ego_speed'] - features['oncoming_speed'])
            key3 = f"speed_diff_{speed_diff:.0f}_weather_{features['weather']}"
            param_combinations[key3] += 1
            
            # 难度 + 天气
            key4 = f"difficulty_{features['difficulty']}_weather_{features['weather']}"
            param_combinations[key4] += 1
        
        # 筛选高危组合（出现次数 >= 5）
        for key, count in param_combinations.items():
            if count >= 5:
                params = key.split('_')
                high_risk_params.append({
                    'combination': key,
                    'count': count,
                    'parameters': self._parse_param_key(key)
                })
        
        # 按出现次数排序
        high_risk_params.sort(key=lambda x: x['count'], reverse=True)
        
        return high_risk_params[:20]  # 返回前20个高危组合
    
    def _parse_param_key(self, key: str) -> Dict:
        """解析参数键"""
        params = {}
        parts = key.split('_')
        
        i = 0
        while i < len(parts):
            if i + 1 < len(parts):
                param_name = parts[i]
                param_value = parts[i + 1]
                params[param_name] = param_value
                i += 2
            else:
                i += 1
        
        return params
    
    def _get_gap_time_range(self, key: str) -> str:
        """获取间隙时间范围"""
        ranges = {
            'very_short': '< 2.5s',
            'short': '2.5-3.0s',
            'medium': '3.0-3.5s',
            'long': '> 3.5s'
        }
        return ranges.get(key, 'unknown')
    
    def _get_speed_diff_range(self, key: str) -> str:
        """获取速度差范围"""
        ranges = {
            'low': '< 15 km/h',
            'medium': '15-30 km/h',
            'high': '> 30 km/h'
        }
        return ranges.get(key, 'unknown')
    
    def _generate_suggestions(self, collision_clusters: List[Dict], 
                               timeout_clusters: List[Dict],
                               high_risk_params: List[Dict]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 碰撞相关建议
        if collision_clusters:
            suggestions.append("建议优化碰撞检测算法，提高对间隙时间的敏感度")
            suggestions.append("建议增加对速度差较大的场景的预判能力")
            suggestions.append("建议在恶劣天气条件下降低车速，增加安全距离")
        
        # 超时相关建议
        if timeout_clusters:
            suggestions.append("建议优化决策算法，减少决策延迟")
            suggestions.append("建议在高难度场景下采用更保守的策略")
            suggestions.append("建议增加对多车辆场景的处理能力")
        
        # 高危参数相关建议
        if high_risk_params:
            suggestions.append("建议针对高危参数组合进行专项优化")
            suggestions.append("建议增加对特定天气和难度组合的训练")
            suggestions.append("建议在测试中增加高危参数组合的覆盖率")
        
        # 通用建议
        suggestions.append("建议增加传感器融合算法的鲁棒性")
        suggestions.append("建议优化路径规划算法，提高对复杂场景的处理能力")
        suggestions.append("建议增加对行人检测的准确性")
        
        return suggestions
    
    def save_analysis(self, analysis: Dict, output_path: str):
        """保存分析结果"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        logger.info(f"分析结果已保存到: {output_path}")
    
    def generate_report(self, analysis: Dict) -> str:
        """生成分析报告"""
        report = f"""# 失败模式聚类分析报告

## 概述

- **总失败数**: {analysis['total_failures']}
- **碰撞数**: {analysis['collision_count']}
- **超时数**: {analysis['timeout_count']}

## 碰撞模式聚类

"""
        
        for cluster in analysis['collision_clusters']:
            report += f"""
### {cluster['name']}

- **数量**: {cluster['count']}
- **描述**: {cluster['description']}
- **案例数**: {len(cluster['cases'])}
"""
        
        report += "\n## 超时模式聚类\n\n"
        
        for cluster in analysis['timeout_clusters']:
            report += f"""
### {cluster['name']}

- **数量**: {cluster['count']}
- **描述**: {cluster['description']}
- **案例数**: {len(cluster['cases'])}
"""
        
        report += "\n## 高危参数组合\n\n"
        report += "| 组合 | 数量 | 参数 |\n"
        report += "|------|------|------|\n"
        
        for param in analysis['high_risk_params'][:10]:
            params_str = ', '.join([f"{k}={v}" for k, v in param['parameters'].items()])
            report += f"| {param['combination']} | {param['count']} | {params_str} |\n"
        
        report += "\n## 改进建议\n\n"
        
        for i, suggestion in enumerate(analysis['suggestions'], 1):
            report += f"{i}. {suggestion}\n"
        
        return report
