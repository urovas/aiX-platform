#!/usr/bin/env python3
"""
无保护左转场景生成器
使用Qwen-72B大模型生成多样化的无保护左转场景
支持8个参数维度的变体生成
"""

import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger('UnprotectedLeftTurnGenerator')

class UnprotectedLeftTurnGenerator:
    """无保护左转场景生成器"""
    
    def __init__(self, use_llm=True):
        """初始化生成器
        
        参数:
            use_llm: 是否使用大模型生成
        """
        self.use_llm = use_llm
        self.scenario_count = 0
        
        # 8个参数维度的取值范围
        self.parameter_ranges = {
            # 1. 自车速度 (5-30 km/h) - 接近路口的速度
            'ego_speed': [5, 10, 15, 20, 25, 30],
            
            # 2. 对向车速 (30-80 km/h) - 对向直行车的速度
            'oncoming_speed': [30, 40, 50, 60, 70, 80],
            
            # 3. 时间间隙 (2-8秒) - 自车与对向车到达冲突点的时间差
            'gap_time': [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
            
            # 4. 对向车型 (轿车/卡车/公交车) - 不同车型影响博弈行为
            'oncoming_vehicle_type': ['sedan', 'truck', 'bus'],
            
            # 5. 天气 (晴/雨/雾/夜) - 影响感知难度
            'weather': ['clear', 'rain', 'fog', 'night'],
            
            # 6. 视野遮挡 (有/无) - 对向大车遮挡后面小车
            'view_blocked': [True, False],
            
            # 7. 交通流量 (低/中/高) - 多车道多辆车流
            'traffic_flow': ['low', 'medium', 'high'],
            
            # 8. 行人/非机动车 (有/无) - 增加复杂度
            'pedestrian_present': [True, False],
            
            # 额外参数
            'distance_to_intersection': [30, 40, 50, 60, 70, 80],  # 米
            'road_width': [3.0, 3.5, 4.0],  # 米
            'visibility': [50, 100, 150, 200, 300],  # 米
            'oncoming_vehicle_count': [1, 2, 3],  # 对向来车数量
        }
        
        # 车型参数映射
        self.vehicle_type_params = {
            'sedan': {
                'length': 4.5,
                'width': 1.8,
                'height': 1.5,
                'model': 'vehicle.tesla.model3',
                'deceleration': -6.0
            },
            'truck': {
                'length': 8.0,
                'width': 2.5,
                'height': 3.5,
                'model': 'vehicle.carlamotors.carlacola',
                'deceleration': -4.0
            },
            'bus': {
                'length': 12.0,
                'width': 2.5,
                'height': 3.2,
                'model': 'vehicle.tesla.cybertruck',
                'deceleration': -3.5
            }
        }
        
        logger.info(f"无保护左转场景生成器初始化完成，使用LLM: {use_llm}")
    
    def generate(self, count: int = 1, difficulty: str = 'medium', 
                weather: str = None) -> List[Dict]:
        """生成无保护左转场景
        
        参数:
            count: 生成场景数量
            difficulty: 难度等级 (easy/medium/hard/extreme)
            weather: 天气条件
            
        返回:
            场景列表
        """
        scenarios = []
        
        for i in range(count):
            scenario = self._generate_single_scenario(difficulty, weather)
            scenario['id'] = f"unprotected_left_turn_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.scenario_count:04d}"
            scenario['created_at'] = datetime.now().isoformat()
            scenario['difficulty'] = difficulty
            self.scenario_count += 1
            
            scenarios.append(scenario)
            logger.info(f"生成场景: {scenario['id']}, 难度: {difficulty}")
        
        return scenarios
    
    def _generate_single_scenario(self, difficulty: str, weather: str = None) -> Dict:
        """生成单个场景"""
        # 根据难度调整参数范围
        params = self._sample_parameters(difficulty)
        
        # 设置天气
        if weather:
            params['weather'] = weather
        
        # 根据天气调整能见度
        params['visibility'] = self._get_visibility_by_weather(params['weather'])
        
        # 根据交通流量设置对向来车数量
        params['oncoming_vehicle_count'] = self._get_vehicle_count_by_traffic_flow(params['traffic_flow'])
        
        # 构建场景
        scenario = {
            'type': 'unprotected-left-turn',
            'name': f'无保护左转场景_{params["weather"]}_{params["oncoming_vehicle_type"]}',
            'description': self._generate_description(params),
            'parameters': params,
            'environment': {
                'weather': params['weather'],
                'visibility': params['visibility'],
                'road_width': params['road_width'],
                'time_of_day': 'night' if params['weather'] == 'night' else 'day',
                'traffic_flow': params['traffic_flow'],
                'view_blocked': params['view_blocked']
            },
            'ego_vehicle': {
                'initial_speed': params['ego_speed'],
                'position': {
                    'x': -params['distance_to_intersection'],
                    'y': 0,
                    'z': 0
                },
                'heading': 0  # 朝东
            },
            'oncoming_vehicles': self._generate_oncoming_vehicles(params),
            'pedestrians': self._generate_pedestrians(params),
            'cross_traffic': self._generate_cross_traffic(params)
        }
        
        return scenario
    
    def _sample_parameters(self, difficulty: str) -> Dict:
        """根据难度采样参数"""
        params = {}
        
        if difficulty == 'easy':
            # 简单：低速、大间隙、好天气、无遮挡、低流量、无行人
            params['ego_speed'] = random.choice([5, 10, 15])
            params['oncoming_speed'] = random.choice([30, 40, 50])
            params['gap_time'] = random.choice([5.0, 6.0, 7.0, 8.0])
            params['oncoming_vehicle_type'] = random.choice(['sedan'])
            params['weather'] = random.choice(['clear'])
            params['view_blocked'] = False
            params['traffic_flow'] = 'low'
            params['pedestrian_present'] = False
            
        elif difficulty == 'medium':
            # 中等：中速、中等间隙、一般天气
            params['ego_speed'] = random.choice([10, 15, 20, 25])
            params['oncoming_speed'] = random.choice([40, 50, 60])
            params['gap_time'] = random.choice([3.0, 4.0, 5.0, 6.0])
            params['oncoming_vehicle_type'] = random.choice(['sedan', 'truck'])
            params['weather'] = random.choice(['clear', 'rain'])
            params['view_blocked'] = random.choice([True, False])
            params['traffic_flow'] = random.choice(['low', 'medium'])
            params['pedestrian_present'] = random.choice([True, False])
            
        elif difficulty == 'hard':
            # 困难：高速、小间隙、恶劣天气
            params['ego_speed'] = random.choice([20, 25, 30])
            params['oncoming_speed'] = random.choice([60, 70, 80])
            params['gap_time'] = random.choice([2.0, 3.0, 4.0])
            params['oncoming_vehicle_type'] = random.choice(['sedan', 'truck', 'bus'])
            params['weather'] = random.choice(['rain', 'fog', 'night'])
            params['view_blocked'] = random.choice([True, False])
            params['traffic_flow'] = random.choice(['medium', 'high'])
            params['pedestrian_present'] = random.choice([True, False])
            
        else:  # extreme
            # 地狱：高速、极小间隙、恶劣天气、有遮挡、高流量、有行人
            params['ego_speed'] = random.choice([25, 30])
            params['oncoming_speed'] = random.choice([70, 80])
            params['gap_time'] = random.choice([2.0, 3.0])
            params['oncoming_vehicle_type'] = random.choice(['truck', 'bus'])
            params['weather'] = random.choice(['fog', 'night'])
            params['view_blocked'] = True
            params['traffic_flow'] = 'high'
            params['pedestrian_present'] = True
        
        # 通用参数
        params['distance_to_intersection'] = random.choice(self.parameter_ranges['distance_to_intersection'])
        params['road_width'] = random.choice(self.parameter_ranges['road_width'])
        
        return params
    
    def _get_visibility_by_weather(self, weather: str) -> int:
        """根据天气获取能见度"""
        visibility_map = {
            'clear': 300,
            'rain': 150,
            'fog': 50,
            'night': 100
        }
        return visibility_map.get(weather, 200)
    
    def _get_vehicle_count_by_traffic_flow(self, traffic_flow: str) -> int:
        """根据交通流量获取车辆数量"""
        count_map = {
            'low': 1,
            'medium': random.choice([1, 2]),
            'high': random.choice([2, 3])
        }
        return count_map.get(traffic_flow, 1)
    
    def _generate_description(self, params: Dict) -> str:
        """生成场景描述"""
        descriptions = []
        
        # 天气描述
        weather_desc = {
            'clear': '晴天',
            'rain': '雨天',
            'fog': '雾天',
            'night': '夜间'
        }
        descriptions.append(f"{weather_desc.get(params['weather'], params['weather'])}条件下")
        
        # 自车描述
        descriptions.append(f"自车以{params['ego_speed']}km/h接近路口")
        
        # 对向来车描述
        vehicle_type_desc = {
            'sedan': '轿车',
            'truck': '卡车',
            'bus': '公交车'
        }
        descriptions.append(f"对向有{vehicle_type_desc.get(params['oncoming_vehicle_type'], params['oncoming_vehicle_type'])}以{params['oncoming_speed']}km/h驶来")
        
        # 间隙描述
        descriptions.append(f"时间间隙{params['gap_time']}秒")
        
        # 遮挡描述
        if params['view_blocked']:
            descriptions.append("有视野遮挡")
        
        # 交通流量描述
        traffic_flow_desc = {
            'low': '低交通流量',
            'medium': '中等交通流量',
            'high': '高交通流量'
        }
        descriptions.append(traffic_flow_desc.get(params['traffic_flow'], params['traffic_flow']))
        
        # 行人描述
        if params['pedestrian_present']:
            descriptions.append("有行人/非机动车")
        
        return "，".join(descriptions)
    
    def _generate_oncoming_vehicles(self, params: Dict) -> List[Dict]:
        """生成对向来车"""
        vehicles = []
        vehicle_type = params['oncoming_vehicle_type']
        vehicle_params = self.vehicle_type_params[vehicle_type]
        
        # 计算对向来车初始位置
        gap_time = params['gap_time']
        oncoming_speed = params['oncoming_speed'] / 3.6  # 转换为m/s
        distance = oncoming_speed * gap_time + 50  # 基础距离 + 间隙距离
        
        for i in range(params['oncoming_vehicle_count']):
            vehicle = {
                'id': f'oncoming_vehicle_{i}',
                'type': vehicle_type,
                'model': vehicle_params['model'],
                'initial_speed': params['oncoming_speed'],
                'position': {
                    'x': distance + i * 30,  # 每辆车间隔30米
                    'y': 0,
                    'z': 0
                },
                'heading': 180,  # 朝西
                'dimensions': {
                    'length': vehicle_params['length'],
                    'width': vehicle_params['width'],
                    'height': vehicle_params['height']
                },
                'deceleration': vehicle_params['deceleration']
            }
            vehicles.append(vehicle)
        
        # 如果有视野遮挡，添加被遮挡的小车
        if params['view_blocked'] and params['oncoming_vehicle_count'] >= 1:
            blocked_vehicle = {
                'id': 'blocked_vehicle',
                'type': 'sedan',
                'model': 'vehicle.tesla.model3',
                'initial_speed': params['oncoming_speed'] + 10,  # 更快
                'position': {
                    'x': distance - 15,  # 在大车后面
                    'y': 0,
                    'z': 0
                },
                'heading': 180,
                'dimensions': {
                    'length': 4.5,
                    'width': 1.8,
                    'height': 1.5
                },
                'deceleration': -6.0,
                'blocked': True  # 被遮挡标记
            }
            vehicles.append(blocked_vehicle)
        
        return vehicles
    
    def _generate_pedestrians(self, params: Dict) -> List[Dict]:
        """生成行人/非机动车"""
        pedestrians = []
        
        if not params['pedestrian_present']:
            return pedestrians
        
        # 在路口附近生成行人
        pedestrian = {
            'id': 'pedestrian_0',
            'type': 'pedestrian',
            'model': 'walker.pedestrian.0001',
            'initial_speed': 1.5,  # 步行速度 m/s
            'position': {
                'x': random.choice([-10, 10]),
                'y': random.choice([-10, 10]),
                'z': 0
            },
            'heading': random.randint(0, 360),
            'crossing_intent': True  # 有横穿意图
        }
        pedestrians.append(pedestrian)
        
        # 高流量时可能添加非机动车
        if params['traffic_flow'] == 'high' and random.random() < 0.5:
            cyclist = {
                'id': 'cyclist_0',
                'type': 'cyclist',
                'model': 'vehicle.bh.crossbike',
                'initial_speed': 15,  # km/h
                'position': {
                    'x': random.choice([-15, 15]),
                    'y': random.choice([-15, 15]),
                    'z': 0
                },
                'heading': random.randint(0, 360)
            }
            pedestrians.append(cyclist)
        
        return pedestrians
    
    def _generate_cross_traffic(self, params: Dict) -> List[Dict]:
        """生成横向交通"""
        cross_traffic = []
        
        # 高流量时添加横向交通
        if params['traffic_flow'] == 'high':
            for i in range(random.randint(1, 2)):
                vehicle = {
                    'id': f'cross_vehicle_{i}',
                    'type': 'sedan',
                    'model': 'vehicle.toyota.prius',
                    'initial_speed': random.randint(30, 50),
                    'position': {
                        'x': 0,
                        'y': random.choice([-60, 60]),
                        'z': 0
                    },
                    'heading': random.choice([90, 270])  # 南北方向
                }
                cross_traffic.append(vehicle)
        
        return cross_traffic
    
    def generate_from_natural_language(self, prompt: str) -> List[Dict]:
        """从自然语言生成场景
        
        参数:
            prompt: 自然语言提示，如"生成100个雨天无保护左转场景"
            
        返回:
            场景列表
        """
        logger.info(f"从自然语言生成场景: {prompt}")
        
        # 解析自然语言提示
        parsed = self._parse_natural_language(prompt)
        
        # 生成场景
        count = parsed.get('count', 1)
        difficulty = parsed.get('difficulty', 'medium')
        weather = parsed.get('weather')
        
        return self.generate(count, difficulty, weather)
    
    def _parse_natural_language(self, prompt: str) -> Dict:
        """解析自然语言"""
        import re
        
        result = {}
        
        # 解析数量
        count_match = re.search(r'(\d+)', prompt)
        if count_match:
            result['count'] = int(count_match.group(1))
        else:
            result['count'] = 1
        
        # 解析难度
        if '简单' in prompt or '容易' in prompt or 'easy' in prompt.lower():
            result['difficulty'] = 'easy'
        elif '困难' in prompt or '难' in prompt or 'hard' in prompt.lower():
            result['difficulty'] = 'hard'
        elif '地狱' in prompt or '极端' in prompt or 'extreme' in prompt.lower():
            result['difficulty'] = 'extreme'
        else:
            result['difficulty'] = 'medium'
        
        # 解析天气
        if '雨' in prompt or 'rain' in prompt.lower():
            result['weather'] = 'rain'
        elif '雾' in prompt or 'fog' in prompt.lower():
            result['weather'] = 'fog'
        elif '夜' in prompt or 'night' in prompt.lower():
            result['weather'] = 'night'
        elif '晴' in prompt or 'clear' in prompt.lower():
            result['weather'] = 'clear'
        
        # 解析车型
        if '卡车' in prompt or 'truck' in prompt.lower():
            result['vehicle_type'] = 'truck'
        elif '公交' in prompt or 'bus' in prompt.lower():
            result['vehicle_type'] = 'bus'
        
        # 解析遮挡
        if '遮挡' in prompt or 'block' in prompt.lower():
            result['view_blocked'] = True
        
        # 解析交通流量
        if '高流量' in prompt or '拥堵' in prompt:
            result['traffic_flow'] = 'high'
        elif '低流量' in prompt:
            result['traffic_flow'] = 'low'
        
        # 解析行人
        if '行人' in prompt or 'pedestrian' in prompt.lower():
            result['pedestrian_present'] = True
        
        return result
    
    def generate_adversarial(self, failure_analysis: Dict, count: int = 100) -> List[Dict]:
        """对抗性生成：在高危参数空间内密集采样
        
        核心闭环逻辑：
        1. 分析失败案例，找出高危参数组合
        2. 在高危参数空间内密集采样
        3. 生成针对性强的对抗性场景
        
        参数:
            failure_analysis: 失败分析结果，包含high_risk_parameters
            count: 生成场景数量
            
        返回:
            对抗性场景列表
        """
        logger.info(f"开始对抗性生成，基于失败分析生成 {count} 个高危场景...")
        
        scenarios = []
        
        # 提取高危参数组合
        high_risk_params = failure_analysis.get('high_risk_parameters', [])
        
        if not high_risk_params:
            logger.warning("未找到高危参数组合，使用随机生成")
            return self.generate(count, difficulty='hard')
        
        # 按风险等级排序
        high_risk_params.sort(key=lambda x: x.get('count', 0), reverse=True)
        
        # 为每个高危参数组合生成场景
        for i in range(count):
            # 选择高危参数组合（按风险权重采样）
            risk_combination = self._sample_by_risk_weight(high_risk_params)
            
            # 在高危参数空间内生成场景
            scenario = self._generate_in_risk_space(risk_combination)
            
            scenario['id'] = f"unprotected_left_turn_adv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.scenario_count:04d}"
            scenario['created_at'] = datetime.now().isoformat()
            scenario['difficulty'] = 'adversarial'
            scenario['adversarial'] = True
            scenario['risk_profile'] = risk_combination
            
            self.scenario_count += 1
            scenarios.append(scenario)
            
            if (i + 1) % 50 == 0:
                logger.info(f"已生成 {i + 1}/{count} 个对抗性场景")
        
        logger.info(f"对抗性生成完成，共生成 {len(scenarios)} 个高危场景")
        return scenarios
    
    def _sample_by_risk_weight(self, high_risk_params: List[Dict]) -> Dict:
        """按风险权重采样高危参数组合"""
        if not high_risk_params:
            return {}
        
        # 计算权重
        total_count = sum(p.get('count', 1) for p in high_risk_params)
        weights = [p.get('count', 1) / total_count for p in high_risk_params]
        
        # 加权随机选择
        import random
        selected = random.choices(high_risk_params, weights=weights, k=1)[0]
        
        return selected
    
    def _generate_in_risk_space(self, risk_combination: Dict) -> Dict:
        """在高危参数空间内生成场景"""
        params = {}
        
        # 解析高危参数组合
        combination = risk_combination.get('combination', '')
        
        # 根据组合类型设置参数范围
        if '间隙时间' in combination:
            # 小间隙场景
            if 'short' in combination or '小' in combination:
                params['gap_time'] = random.uniform(2.0, 3.5)
            elif 'medium' in combination or '中' in combination:
                params['gap_time'] = random.uniform(3.0, 4.5)
            else:
                params['gap_time'] = random.choice(self.parameter_ranges['gap_time'])
        else:
            params['gap_time'] = random.choice([2.0, 2.5, 3.0, 3.5])
        
        if '速度差' in combination or '车速' in combination:
            # 高速差场景
            if 'high' in combination or '大' in combination:
                params['ego_speed'] = random.choice([20, 25, 30])
                params['oncoming_speed'] = random.choice([70, 80])
            elif 'medium' in combination or '中' in combination:
                params['ego_speed'] = random.choice([15, 20, 25])
                params['oncoming_speed'] = random.choice([60, 70])
            else:
                params['ego_speed'] = random.choice(self.parameter_ranges['ego_speed'])
                params['oncoming_speed'] = random.choice(self.parameter_ranges['oncoming_speed'])
        else:
            params['ego_speed'] = random.choice([20, 25, 30])
            params['oncoming_speed'] = random.choice([60, 70, 80])
        
        if '天气' in combination or 'weather' in combination:
            # 恶劣天气
            if 'rain' in combination or '雨' in combination:
                params['weather'] = 'rain'
            elif 'fog' in combination or '雾' in combination:
                params['weather'] = 'fog'
            elif 'night' in combination or '夜' in combination:
                params['weather'] = 'night'
            else:
                params['weather'] = random.choice(['rain', 'fog', 'night'])
        else:
            params['weather'] = random.choice(['rain', 'fog', 'night'])
        
        # 高危场景的其他参数也倾向于高风险
        params['oncoming_vehicle_type'] = random.choice(['truck', 'bus'])
        params['view_blocked'] = random.choice([True, True, False])  # 更倾向于有遮挡
        params['traffic_flow'] = random.choice(['medium', 'high', 'high'])  # 更倾向于高流量
        params['pedestrian_present'] = random.choice([True, True, False])  # 更倾向于有行人
        
        # 通用参数
        params['distance_to_intersection'] = random.choice(self.parameter_ranges['distance_to_intersection'])
        params['road_width'] = random.choice(self.parameter_ranges['road_width'])
        params['visibility'] = self._get_visibility_by_weather(params['weather'])
        params['oncoming_vehicle_count'] = self._get_vehicle_count_by_traffic_flow(params['traffic_flow'])
        
        # 构建场景
        scenario = {
            'type': 'unprotected-left-turn',
            'name': f'对抗性无保护左转场景_{params["weather"]}',
            'description': self._generate_adversarial_description(params, risk_combination),
            'parameters': params,
            'environment': {
                'weather': params['weather'],
                'visibility': params['visibility'],
                'road_width': params['road_width'],
                'time_of_day': 'night' if params['weather'] == 'night' else 'day',
                'traffic_flow': params['traffic_flow'],
                'view_blocked': params['view_blocked']
            },
            'ego_vehicle': {
                'initial_speed': params['ego_speed'],
                'position': {
                    'x': -params['distance_to_intersection'],
                    'y': 0,
                    'z': 0
                },
                'heading': 0
            },
            'oncoming_vehicles': self._generate_oncoming_vehicles(params),
            'pedestrians': self._generate_pedestrians(params),
            'cross_traffic': self._generate_cross_traffic(params)
        }
        
        return scenario
    
    def _generate_adversarial_description(self, params: Dict, risk_combination: Dict) -> str:
        """生成对抗性场景描述"""
        base_desc = self._generate_description(params)
        risk_info = risk_combination.get('combination', '未知风险')
        return f"[对抗性] {base_desc} | 风险特征: {risk_info}"
    
    def iterative_adversarial_generation(self, initial_count: int = 500, 
                                        iterations: int = 3,
                                        test_executor=None) -> Dict:
        """迭代对抗性生成完整流程
        
        核心闭环：
        1. 初始阶段：随机生成场景，执行，记录结果
        2. 分析阶段：找出高危参数组合
        3. 聚焦阶段：在高危参数空间内密集采样
        4. 深度测试：执行高危场景
        5. 迭代：找到更细分的失败模式
        
        参数:
            initial_count: 初始随机生成场景数量
            iterations: 迭代次数
            test_executor: 测试执行器（可选）
            
        返回:
            包含所有迭代结果的字典
        """
        from analyzers.failure_cluster_analyzer import FailureClusterAnalyzer
        
        logger.info(f"开始迭代对抗性生成，初始场景数: {initial_count}, 迭代次数: {iterations}")
        
        all_results = {
            'iterations': [],
            'final_high_risk_params': None,
            'total_scenarios': 0,
            'total_failures': 0
        }
        
        analyzer = FailureClusterAnalyzer()
        
        # 第0轮：初始随机生成
        logger.info("="*60)
        logger.info("第0轮：初始随机生成")
        logger.info("="*60)
        
        initial_scenarios = self.generate(initial_count, difficulty='medium')
        
        # 模拟或实际执行测试
        if test_executor:
            initial_results = test_executor.execute_batch(initial_scenarios)
        else:
            # 模拟执行结果
            initial_results = self._simulate_test_results(initial_scenarios)
        
        # 分析失败模式
        initial_analysis = analyzer.analyze(initial_scenarios, initial_results)
        
        all_results['iterations'].append({
            'round': 0,
            'type': 'initial',
            'scenarios': initial_scenarios,
            'results': initial_results,
            'analysis': initial_analysis
        })
        
        all_results['total_scenarios'] += len(initial_scenarios)
        all_results['total_failures'] += initial_analysis.get('total_failures', 0)
        
        logger.info(f"第0轮完成: {len(initial_scenarios)} 个场景, "
                   f"{initial_analysis.get('total_failures', 0)} 个失败")
        
        # 迭代优化
        for iteration in range(1, iterations + 1):
            logger.info("="*60)
            logger.info(f"第{iteration}轮：对抗性聚焦生成")
            logger.info("="*60)
            
            # 基于上一轮分析结果生成对抗性场景
            prev_analysis = all_results['iterations'][-1]['analysis']
            
            adversarial_scenarios = self.generate_adversarial(
                prev_analysis, 
                count=initial_count // 2  # 每轮生成一半数量的对抗性场景
            )
            
            # 执行测试
            if test_executor:
                adversarial_results = test_executor.execute_batch(adversarial_scenarios)
            else:
                adversarial_results = self._simulate_test_results(adversarial_scenarios)
            
            # 分析失败模式
            adversarial_analysis = analyzer.analyze(adversarial_scenarios, adversarial_results)
            
            all_results['iterations'].append({
                'round': iteration,
                'type': 'adversarial',
                'scenarios': adversarial_scenarios,
                'results': adversarial_results,
                'analysis': adversarial_analysis
            })
            
            all_results['total_scenarios'] += len(adversarial_scenarios)
            all_results['total_failures'] += adversarial_analysis.get('total_failures', 0)
            
            logger.info(f"第{iteration}轮完成: {len(adversarial_scenarios)} 个场景, "
                       f"{adversarial_analysis.get('total_failures', 0)} 个失败")
            
            # 检查是否发现新的高危参数组合
            new_high_risk = adversarial_analysis.get('high_risk_parameters', [])
            if new_high_risk:
                logger.info(f"发现 {len(new_high_risk)} 个高危参数组合")
                for param in new_high_risk[:3]:  # 显示前3个
                    logger.info(f"  - {param['combination']}: {param['count']} 次失败")
        
        # 汇总最终结果
        all_results['final_high_risk_params'] = all_results['iterations'][-1]['analysis'].get('high_risk_parameters', [])
        
        logger.info("="*60)
        logger.info("迭代对抗性生成完成")
        logger.info("="*60)
        logger.info(f"总场景数: {all_results['total_scenarios']}")
        logger.info(f"总失败数: {all_results['total_failures']}")
        logger.info(f"最终高危参数组合数: {len(all_results['final_high_risk_params'])}")
        
        return all_results
    
    def _simulate_test_results(self, scenarios: List[Dict]) -> List[Dict]:
        """模拟测试执行结果（用于演示）"""
        import random
        results = []
        
        for scenario in scenarios:
            params = scenario['parameters']
            
            # 根据参数计算失败概率
            failure_prob = 0.1  # 基础失败率
            
            # 高危参数增加失败概率
            if params['gap_time'] < 3.0:
                failure_prob += 0.3
            if params['oncoming_speed'] > 70:
                failure_prob += 0.2
            if params['weather'] in ['fog', 'night']:
                failure_prob += 0.15
            if params['view_blocked']:
                failure_prob += 0.1
            if params['pedestrian_present']:
                failure_prob += 0.1
            if params['traffic_flow'] == 'high':
                failure_prob += 0.1
            
            # 判断是否失败
            is_failure = random.random() < failure_prob
            
            if is_failure:
                # 随机决定失败类型
                if random.random() < 0.7:
                    result = {
                        'scenario_id': scenario['id'],
                        'success': False,
                        'collision': True,
                        'timeout': False,
                        'collision_time': random.uniform(2.0, params['gap_time']),
                        'response_time': random.uniform(1.5, 3.0),
                        'max_deceleration': random.uniform(-8.0, -4.0)
                    }
                else:
                    result = {
                        'scenario_id': scenario['id'],
                        'success': False,
                        'collision': False,
                        'timeout': True,
                        'execution_time': 10.0,
                        'response_time': random.uniform(2.0, 4.0),
                        'max_deceleration': random.uniform(-4.0, -2.0)
                    }
            else:
                result = {
                    'scenario_id': scenario['id'],
                    'success': True,
                    'collision': False,
                    'timeout': False,
                    'execution_time': random.uniform(5.0, 8.0),
                    'response_time': random.uniform(1.0, 2.5),
                    'max_deceleration': random.uniform(-5.0, -3.0)
                }
            
            results.append(result)
        
        return results
