#!/usr/bin/env python3
"""
场景难度评级系统
根据场景参数评估场景难度等级
"""

import logging
from typing import Dict, List

logger = logging.getLogger('DifficultyRater')

class DifficultyRater:
    """场景难度评级器"""
    
    def __init__(self):
        """初始化评级器"""
        # 难度权重
        self.weights = {
            'gap_time': 0.3,  # 间隙时间权重
            'speed_difference': 0.25,  # 速度差权重
            'oncoming_vehicle_count': 0.2,  # 对向来车数量权重
            'cross_traffic': 0.1,  # 横向交通权重
            'pedestrian_present': 0.1,  # 行人权重
            'weather': 0.05,  # 天气权重
            'visibility': 0.0  # 能见度权重（包含在天气中）
        }
        
        logger.info("场景难度评级器初始化完成")
    
    def rate(self, scenario: Dict) -> Dict:
        """评估场景难度
        
        参数:
            scenario: 场景字典
            
        返回:
            评级结果，包含难度分数和等级
        """
        params = scenario.get('parameters', {})
        environment = scenario.get('environment', {})
        
        # 计算各项难度分数
        scores = {}
        
        # 间隙时间分数（越小越难）
        scores['gap_time'] = self._rate_gap_time(params.get('gap_time', 3.0))
        
        # 速度差分数（越大越难）
        ego_speed = scenario.get('ego_vehicle', {}).get('initial_speed', 50)
        oncoming_speed = params.get('oncoming_speed', 60)
        scores['speed_difference'] = self._rate_speed_difference(ego_speed, oncoming_speed)
        
        # 对向来车数量分数（越多越难）
        scores['oncoming_vehicle_count'] = self._rate_vehicle_count(
            params.get('oncoming_vehicle_count', 1)
        )
        
        # 横向交通分数
        scores['cross_traffic'] = self._rate_cross_traffic(
            params.get('cross_traffic', False)
        )
        
        # 行人分数
        scores['pedestrian_present'] = self._rate_pedestrian(
            params.get('pedestrian_present', False)
        )
        
        # 天气分数
        weather = environment.get('weather', 'clear')
        scores['weather'] = self._rate_weather(weather)
        
        # 能见度分数（越低越难）
        scores['visibility'] = self._rate_visibility(
            environment.get('visibility', 200)
        )
        
        # 计算加权总分
        total_score = sum(
            scores[key] * self.weights[key]
            for key in scores
        )
        
        # 确定难度等级
        difficulty_level = self._classify_difficulty(total_score)
        
        result = {
            'total_score': total_score,
            'difficulty_level': difficulty_level,
            'scores': scores,
            'factors': self._identify_difficulty_factors(scores)
        }
        
        logger.info(f"场景 {scenario.get('id')} 难度评级: {difficulty_level} (分数: {total_score:.2f})")
        
        return result
    
    def _rate_gap_time(self, gap_time: float) -> float:
        """评估间隙时间难度"""
        if gap_time >= 4.5:
            return 0.0  # 很容易
        elif gap_time >= 3.5:
            return 0.2  # 容易
        elif gap_time >= 3.0:
            return 0.4  # 中等
        elif gap_time >= 2.5:
            return 0.7  # 困难
        else:
            return 1.0  # 极端困难
    
    def _rate_speed_difference(self, ego_speed: float, oncoming_speed: float) -> float:
        """评估速度差难度"""
        speed_diff = abs(ego_speed - oncoming_speed)
        
        if speed_diff <= 10:
            return 0.0  # 很容易
        elif speed_diff <= 20:
            return 0.2  # 容易
        elif speed_diff <= 30:
            return 0.4  # 中等
        elif speed_diff <= 40:
            return 0.7  # 困难
        else:
            return 1.0  # 极端困难
    
    def _rate_vehicle_count(self, count: int) -> float:
        """评估车辆数量难度"""
        if count == 1:
            return 0.0  # 很容易
        elif count == 2:
            return 0.5  # 中等
        else:
            return 1.0  # 困难
    
    def _rate_cross_traffic(self, has_cross_traffic: bool) -> float:
        """评估横向交通难度"""
        return 1.0 if has_cross_traffic else 0.0
    
    def _rate_pedestrian(self, has_pedestrian: bool) -> float:
        """评估行人难度"""
        return 1.0 if has_pedestrian else 0.0
    
    def _rate_weather(self, weather: str) -> float:
        """评估天气难度"""
        weather_difficulty = {
            'clear': 0.0,
            'rain': 0.5,
            'fog': 0.7,
            'night': 0.6,
            'rain_night': 0.9
        }
        return weather_difficulty.get(weather, 0.0)
    
    def _rate_visibility(self, visibility: float) -> float:
        """评估能见度难度"""
        if visibility >= 250:
            return 0.0  # 很好
        elif visibility >= 200:
            return 0.2  # 好
        elif visibility >= 150:
            return 0.4  # 中等
        elif visibility >= 100:
            return 0.7  # 差
        else:
            return 1.0  # 很差
    
    def _classify_difficulty(self, total_score: float) -> str:
        """分类难度等级"""
        if total_score < 0.2:
            return 'easy'
        elif total_score < 0.4:
            return 'medium'
        elif total_score < 0.7:
            return 'hard'
        else:
            return 'extreme'
    
    def _identify_difficulty_factors(self, scores: Dict) -> List[str]:
        """识别难度因素"""
        factors = []
        
        # 找出高分项
        high_score_items = [
            (name, score) for name, score in scores.items()
            if score >= 0.7
        ]
        
        # 映射到描述
        factor_descriptions = {
            'gap_time': '间隙时间短',
            'speed_difference': '速度差大',
            'oncoming_vehicle_count': '对向来车多',
            'cross_traffic': '有横向交通',
            'pedestrian_present': '有行人',
            'weather': '恶劣天气',
            'visibility': '能见度低'
        }
        
        for name, score in high_score_items:
            if name in factor_descriptions:
                factors.append(factor_descriptions[name])
        
        return factors
    
    def rate_batch(self, scenarios: List[Dict]) -> List[Dict]:
        """批量评估场景难度
        
        参数:
            scenarios: 场景列表
            
        返回:
            评级结果列表
        """
        results = []
        
        for scenario in scenarios:
            result = self.rate(scenario)
            results.append(result)
        
        logger.info(f"批量评级完成，共 {len(scenarios)} 个场景")
        
        return results
    
    def get_statistics(self, scenarios: List[Dict]) -> Dict:
        """获取场景难度统计信息
        
        参数:
            scenarios: 场景列表
            
        返回:
            统计信息
        """
        ratings = self.rate_batch(scenarios)
        
        # 统计各难度等级数量
        difficulty_counts = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'extreme': 0
        }
        
        for rating in ratings:
            level = rating['difficulty_level']
            difficulty_counts[level] += 1
        
        # 计算平均分数
        avg_score = sum(r['total_score'] for r in ratings) / len(ratings)
        
        # 统计难度因素
        all_factors = []
        for rating in ratings:
            all_factors.extend(rating['factors'])
        
        factor_counts = {}
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        return {
            'total_scenarios': len(scenarios),
            'difficulty_distribution': difficulty_counts,
            'average_score': avg_score,
            'factor_distribution': factor_counts
        }
