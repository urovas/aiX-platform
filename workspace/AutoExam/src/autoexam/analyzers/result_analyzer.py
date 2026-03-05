#!/usr/bin/env python3
"""
结果分析器模块
负责分析测试结果，识别失败模式，提供改进建议
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger('ResultAnalyzer')

class ResultAnalyzer:
    """结果分析器"""
    
    def __init__(self):
        """初始化结果分析器"""
        self.failure_patterns = {
            'collision': '碰撞',
            'late_response': '响应延迟',
            'insufficient_deceleration': '制动不足',
            'lane_departure': '车道偏离',
            'false_positive': '误报',
            'false_negative': '漏报'
        }
        
        self.improvement_suggestions = {
            'collision': '优化感知算法，提高障碍物检测精度',
            'late_response': '优化决策算法，减少响应延迟',
            'insufficient_deceleration': '调整制动策略，提高最大减速度',
            'lane_departure': '优化车道保持算法',
            'false_positive': '调整感知阈值，减少误报',
            'false_negative': '增强感知系统，提高检测率'
        }
    
    def analyze(self, result):
        """分析测试结果
        
        参数:
            result: 测试结果字典
            
        返回:
            分析结果字典
        """
        if not result.get('success', False):
            return {
                'status': 'error',
                'error': result.get('error', '未知错误'),
                'analysis_time': datetime.now().isoformat()
            }
        
        # 基本分析
        analysis = {
            'status': 'success',
            'scenario_id': result.get('scenario_id'),
            'scenario_type': result.get('scenario_type'),
            'risk_level': result.get('risk_level'),
            'collision': result.get('collision', False),
            'response_time': result.get('response_time', 0),
            'max_deceleration': result.get('max_deceleration', 0),
            'analysis_time': datetime.now().isoformat()
        }
        
        # 失败模式分析
        failure_modes = []
        if result.get('collision', False):
            failure_modes.append('collision')
        
        # 响应时间分析
        response_time = result.get('response_time', 0)
        if response_time > 1.5:
            failure_modes.append('late_response')
        
        # 减速度分析
        max_deceleration = result.get('max_deceleration', 0)
        if max_deceleration > -3.0:
            failure_modes.append('insufficient_deceleration')
        
        # 车道偏离分析
        if result.get('lane_departure', False):
            failure_modes.append('lane_departure')
        
        # 误报/漏报分析
        if result.get('false_positive', False):
            failure_modes.append('false_positive')
        if result.get('false_negative', False):
            failure_modes.append('false_negative')
        
        # 更新分析结果
        if failure_modes:
            analysis['status'] = 'failure'
            analysis['failure_modes'] = failure_modes
            analysis['failure_reason'] = self._get_failure_reason(failure_modes)
            analysis['improvement_suggestion'] = self._get_improvement_suggestion(failure_modes)
        
        # 风险评估
        analysis['risk_assessment'] = self._assess_risk(result)
        
        # 性能指标
        analysis['performance_metrics'] = self._calculate_performance_metrics(result)
        
        return analysis
    
    def _get_failure_reason(self, failure_modes):
        """获取失败原因"""
        reasons = []
        for mode in failure_modes:
            reasons.append(self.failure_patterns.get(mode, mode))
        return '; '.join(reasons)
    
    def _get_improvement_suggestion(self, failure_modes):
        """获取改进建议"""
        suggestions = []
        for mode in failure_modes:
            suggestions.append(self.improvement_suggestions.get(mode, '需要进一步分析'))
        return '; '.join(suggestions)
    
    def _assess_risk(self, result):
        """评估风险等级"""
        risk_level = result.get('risk_level', 'medium')
        collision = result.get('collision', False)
        response_time = result.get('response_time', 0)
        
        if collision:
            return 'critical'
        elif response_time > 2.0:
            return 'high'
        elif risk_level == 'extreme':
            return 'high'
        elif risk_level == 'high':
            return 'medium'
        else:
            return 'low'
    
    def _calculate_performance_metrics(self, result):
        """计算性能指标"""
        metrics = {
            'response_time': result.get('response_time', 0),
            'max_deceleration': result.get('max_deceleration', 0),
            'success_rate': 1.0 if result.get('success', False) else 0.0,
            'collision_rate': 1.0 if result.get('collision', False) else 0.0
        }
        
        # 计算综合得分
        base_score = 100
        if result.get('collision', False):
            base_score -= 50
        if result.get('response_time', 0) > 1.5:
            base_score -= (result['response_time'] - 1.5) * 10
        if result.get('max_deceleration', 0) > -3.0:
            base_score -= (-3.0 - result['max_deceleration']) * 5
        
        metrics['score'] = max(0, base_score)
        
        return metrics
    
    def analyze_batch(self, results):
        """批量分析结果
        
        参数:
            results: 测试结果列表
            
        返回:
            批量分析结果
        """
        batch_analysis = {
            'total_tests': len(results),
            'success_count': 0,
            'failure_count': 0,
            'error_count': 0,
            'failure_modes': {},
            'average_metrics': {
                'response_time': 0,
                'max_deceleration': 0,
                'score': 0
            },
            'analysis_time': datetime.now().isoformat()
        }
        
        total_response_time = 0
        total_deceleration = 0
        total_score = 0
        valid_results = 0
        
        for result in results:
            analysis = self.analyze(result)
            
            if analysis['status'] == 'success':
                batch_analysis['success_count'] += 1
            elif analysis['status'] == 'failure':
                batch_analysis['failure_count'] += 1
                # 统计失败模式
                for mode in analysis.get('failure_modes', []):
                    batch_analysis['failure_modes'][mode] = batch_analysis['failure_modes'].get(mode, 0) + 1
            else:
                batch_analysis['error_count'] += 1
            
            # 计算平均指标
            if 'performance_metrics' in analysis:
                total_response_time += analysis['performance_metrics'].get('response_time', 0)
                total_deceleration += analysis['performance_metrics'].get('max_deceleration', 0)
                total_score += analysis['performance_metrics'].get('score', 0)
                valid_results += 1
        
        # 计算平均值
        if valid_results > 0:
            batch_analysis['average_metrics']['response_time'] = total_response_time / valid_results
            batch_analysis['average_metrics']['max_deceleration'] = total_deceleration / valid_results
            batch_analysis['average_metrics']['score'] = total_score / valid_results
        
        # 计算成功率
        if batch_analysis['total_tests'] > 0:
            batch_analysis['success_rate'] = batch_analysis['success_count'] / batch_analysis['total_tests']
        
        return batch_analysis
    
    def generate_report(self, analysis):
        """生成分析报告
        
        参数:
            analysis: 分析结果
            
        返回:
            报告字符串
        """
        report = []
        report.append(f"# 测试分析报告")
        report.append(f"分析时间: {analysis.get('analysis_time')}")
        report.append(f"场景ID: {analysis.get('scenario_id')}")
        report.append(f"场景类型: {analysis.get('scenario_type')}")
        report.append(f"风险等级: {analysis.get('risk_level')}")
        report.append(f"测试状态: {analysis.get('status')}")
        
        if analysis.get('status') == 'failure':
            report.append(f"失败原因: {analysis.get('failure_reason')}")
            report.append(f"改进建议: {analysis.get('improvement_suggestion')}")
        
        report.append(f"\n## 性能指标")
        if 'performance_metrics' in analysis:
            metrics = analysis['performance_metrics']
            report.append(f"响应时间: {metrics.get('response_time', 0):.2f}s")
            report.append(f"最大减速度: {metrics.get('max_deceleration', 0):.2f}m/s²")
            report.append(f"综合得分: {metrics.get('score', 0):.1f}")
        
        report.append(f"\n## 风险评估")
        report.append(f"风险等级: {analysis.get('risk_assessment')}")
        
        return '\n'.join(report)
