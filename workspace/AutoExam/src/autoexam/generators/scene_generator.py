#!/usr/bin/env python3
"""
场景生成器模块
使用智能体生成多样化的自动驾驶高危场景
"""

import random
import json
import logging
from datetime import datetime
from autoexam.integrations.agent_interface import AgentInterface

logger = logging.getLogger('SceneGenerator')

class SceneGenerator:
    """场景生成器"""
    
    def __init__(self, config=None, use_agents=True):
        """初始化场景生成器
        
        参数:
            config: 配置字典
            use_agents: 是否使用智能体生成场景
        """
        self.config = config or {}
        self.use_agents = use_agents
        self.scenario_types = self.config.get('scenario_types', [
            'cut-in', 'emergency-brake', 'occlusion', 
            'pedestrian-crossing', 'multi-vehicle', 'adverse-weather'
        ])
        self.risk_levels = self.config.get('risk_levels', ['low', 'medium', 'high', 'extreme'])
        
        if self.use_agents:
            self.agent_interface = AgentInterface()
            logger.info("场景生成器使用智能体模式")
        else:
            logger.info("场景生成器使用传统模式")
    
    def generate(self, scenario_type=None, risk_level='high'):
        """生成场景
        
        参数:
            scenario_type: 场景类型，None表示随机选择
            risk_level: 风险等级
            
        返回:
            场景字典
        """
        if scenario_type is None:
            scenario_type = random.choice(self.scenario_types)
        
        if self.use_agents:
            return self._generate_with_agent(scenario_type, risk_level)
        else:
            return self._generate_traditional(scenario_type, risk_level)
    
    def _generate_with_agent(self, scenario_type, risk_level):
        """使用智能体生成场景
        
        参数:
            scenario_type: 场景类型
            risk_level: 风险等级
            
        返回:
            场景字典
        """
        logger.info(f"使用智能体生成场景: {scenario_type}, 风险等级: {risk_level}")
        
        result = self.agent_interface.generate_scenario(scenario_type, risk_level)
        
        if result['success']:
            scenario = result['scenario']
            scenario['id'] = f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}"
            scenario['created_at'] = datetime.now().isoformat()
            logger.info(f"智能体生成场景成功: {scenario['id']}")
            return scenario
        else:
            logger.error(f"智能体生成场景失败: {result.get('error')}")
            return self._generate_traditional(scenario_type, risk_level)
    
    def _generate_traditional(self, scenario_type, risk_level):
        """使用传统方法生成场景（备用方案）
        
        参数:
            scenario_type: 场景类型
            risk_level: 风险等级
            
        返回:
            场景字典
        """
        logger.info(f"使用传统方法生成场景: {scenario_type}, 风险等级: {risk_level}")
        
        if scenario_type == 'cut-in':
            return self._generate_cut_in_scenario(risk_level)
        elif scenario_type == 'emergency-brake':
            return self._generate_emergency_brake_scenario(risk_level)
        elif scenario_type == 'occlusion':
            return self._generate_occlusion_scenario(risk_level)
        elif scenario_type == 'pedestrian-crossing':
            return self._generate_pedestrian_crossing_scenario(risk_level)
        elif scenario_type == 'multi-vehicle':
            return self._generate_multi_vehicle_scenario(risk_level)
        elif scenario_type == 'adverse-weather':
            return self._generate_adverse_weather_scenario(risk_level)
        else:
            return self._generate_default_scenario(risk_level)
    
    def _generate_cut_in_scenario(self, risk_level):
        """生成切入场景"""
        # 根据风险等级调整参数
        if risk_level == 'low':
            angle = random.uniform(15, 25)
            speed_diff = random.uniform(20, 30)
            distance = random.uniform(50, 70)
        elif risk_level == 'medium':
            angle = random.uniform(20, 35)
            speed_diff = random.uniform(30, 45)
            distance = random.uniform(30, 50)
        elif risk_level == 'high':
            angle = random.uniform(30, 40)
            speed_diff = random.uniform(45, 55)
            distance = random.uniform(20, 30)
        else:  # extreme
            angle = random.uniform(35, 45)
            speed_diff = random.uniform(55, 60)
            distance = random.uniform(10, 20)
        
        return {
            'type': 'cut-in',
            'risk_level': risk_level,
            'parameters': {
                'angle': angle,  # 切入角度 (度)
                'speed_diff': speed_diff,  # 速度差 (km/h)
                'distance': distance,  # 初始距离 (m)
                'vehicle_type': random.choice(['car', 'truck', 'bus']),
                'lane_change_duration': random.uniform(1.0, 2.0)  # 变道持续时间 (s)
            },
            'environment': {
                'weather': random.choice(['clear', 'rain', 'fog']),
                'road_condition': random.choice(['dry', 'wet']),
                'time_of_day': random.choice(['day', 'night'])
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_emergency_brake_scenario(self, risk_level):
        """生成紧急制动场景"""
        if risk_level == 'low':
            deceleration = random.uniform(-4, -5)
            distance = random.uniform(60, 80)
            initial_speed = random.uniform(40, 60)
        elif risk_level == 'medium':
            deceleration = random.uniform(-5, -6)
            distance = random.uniform(40, 60)
            initial_speed = random.uniform(60, 80)
        elif risk_level == 'high':
            deceleration = random.uniform(-6, -7)
            distance = random.uniform(25, 40)
            initial_speed = random.uniform(80, 100)
        else:  # extreme
            deceleration = random.uniform(-7, -8)
            distance = random.uniform(15, 25)
            initial_speed = random.uniform(100, 120)
        
        return {
            'type': 'emergency-brake',
            'risk_level': risk_level,
            'parameters': {
                'deceleration': deceleration,  # 减速度 (m/s²)
                'distance': distance,  # 初始距离 (m)
                'initial_speed': initial_speed,  # 初始速度 (km/h)
                'brake_duration': random.uniform(1.0, 3.0),  # 制动持续时间 (s)
                'obstacle_type': random.choice(['vehicle', 'pedestrian', 'static'])
            },
            'environment': {
                'weather': random.choice(['clear', 'rain', 'fog']),
                'road_condition': random.choice(['dry', 'wet']),
                'time_of_day': random.choice(['day', 'night'])
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_occlusion_scenario(self, risk_level):
        """生成遮挡场景"""
        if risk_level == 'low':
            occlusion_duration = random.uniform(1.0, 2.0)
            obstacle_size = random.uniform(2.0, 4.0)
            distance = random.uniform(50, 70)
        elif risk_level == 'medium':
            occlusion_duration = random.uniform(2.0, 3.0)
            obstacle_size = random.uniform(4.0, 6.0)
            distance = random.uniform(30, 50)
        elif risk_level == 'high':
            occlusion_duration = random.uniform(3.0, 4.0)
            obstacle_size = random.uniform(6.0, 8.0)
            distance = random.uniform(20, 30)
        else:  # extreme
            occlusion_duration = random.uniform(4.0, 5.0)
            obstacle_size = random.uniform(8.0, 10.0)
            distance = random.uniform(10, 20)
        
        return {
            'type': 'occlusion',
            'risk_level': risk_level,
            'parameters': {
                'occlusion_duration': occlusion_duration,  # 遮挡持续时间 (s)
                'obstacle_size': obstacle_size,  # 障碍物尺寸 (m)
                'distance': distance,  # 初始距离 (m)
                'hidden_object_speed': random.uniform(10, 30),  # 隐藏物体速度 (km/h)
                'obstacle_type': random.choice(['truck', 'bus', 'wall'])
            },
            'environment': {
                'weather': random.choice(['clear', 'rain', 'fog']),
                'road_condition': random.choice(['dry', 'wet']),
                'time_of_day': random.choice(['day', 'night'])
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_pedestrian_crossing_scenario(self, risk_level):
        """生成行人横穿场景"""
        if risk_level == 'low':
            crossing_speed = random.uniform(3.0, 4.0)
            distance = random.uniform(40, 60)
            reaction_time = random.uniform(1.0, 1.5)
        elif risk_level == 'medium':
            crossing_speed = random.uniform(2.5, 3.5)
            distance = random.uniform(25, 40)
            reaction_time = random.uniform(0.7, 1.2)
        elif risk_level == 'high':
            crossing_speed = random.uniform(2.0, 3.0)
            distance = random.uniform(15, 25)
            reaction_time = random.uniform(0.5, 0.9)
        else:  # extreme
            crossing_speed = random.uniform(1.5, 2.5)
            distance = random.uniform(5, 15)
            reaction_time = random.uniform(0.3, 0.6)
        
        return {
            'type': 'pedestrian-crossing',
            'risk_level': risk_level,
            'parameters': {
                'crossing_speed': crossing_speed,  # 横穿速度 (m/s)
                'distance': distance,  # 初始距离 (m)
                'reaction_time': reaction_time,  # 反应时间 (s)
                'pedestrian_count': random.randint(1, 3),
                'crossing_angle': random.uniform(60, 120)  # 横穿角度 (度)
            },
            'environment': {
                'weather': random.choice(['clear', 'rain', 'fog']),
                'road_condition': random.choice(['dry', 'wet']),
                'time_of_day': random.choice(['day', 'night'])
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_multi_vehicle_scenario(self, risk_level):
        """生成多车协同场景"""
        if risk_level == 'low':
            vehicle_count = random.randint(2, 3)
            distance = random.uniform(60, 80)
            speed_diff = random.uniform(10, 20)
        elif risk_level == 'medium':
            vehicle_count = random.randint(3, 4)
            distance = random.uniform(40, 60)
            speed_diff = random.uniform(20, 30)
        elif risk_level == 'high':
            vehicle_count = random.randint(4, 5)
            distance = random.uniform(25, 40)
            speed_diff = random.uniform(30, 40)
        else:  # extreme
            vehicle_count = random.randint(5, 6)
            distance = random.uniform(15, 25)
            speed_diff = random.uniform(40, 50)
        
        return {
            'type': 'multi-vehicle',
            'risk_level': risk_level,
            'parameters': {
                'vehicle_count': vehicle_count,  # 车辆数量
                'distance': distance,  # 初始距离 (m)
                'speed_diff': speed_diff,  # 速度差 (km/h)
                'formation': random.choice(['platoon', 'scattered', 'opposite']),
                'reaction_delay': random.uniform(0.5, 1.5)  # 反应延迟 (s)
            },
            'environment': {
                'weather': random.choice(['clear', 'rain', 'fog']),
                'road_condition': random.choice(['dry', 'wet']),
                'time_of_day': random.choice(['day', 'night'])
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_adverse_weather_scenario(self, risk_level):
        """生成恶劣天气场景"""
        weather_conditions = {
            'low': ['light_rain', 'light_fog'],
            'medium': ['moderate_rain', 'moderate_fog'],
            'high': ['heavy_rain', 'heavy_fog', 'light_snow'],
            'extreme': ['heavy_snow', 'thunderstorm', 'blizzard']
        }
        
        road_conditions = {
            'low': ['dry', 'slightly_wet'],
            'medium': ['wet', 'slightly_icy'],
            'high': ['very_wet', 'icy'],
            'extreme': ['flooded', 'very_icy']
        }
        
        visibility = {
            'low': random.uniform(200, 300),
            'medium': random.uniform(100, 200),
            'high': random.uniform(50, 100),
            'extreme': random.uniform(20, 50)
        }
        
        return {
            'type': 'adverse-weather',
            'risk_level': risk_level,
            'parameters': {
                'visibility': visibility[risk_level],  # 能见度 (m)
                'weather_condition': random.choice(weather_conditions[risk_level]),
                'road_condition': random.choice(road_conditions[risk_level]),
                'wind_speed': random.uniform(10, 30),  # 风速 (km/h)
                'initial_speed': random.uniform(60, 100)  # 初始速度 (km/h)
            },
            'environment': {
                'weather': random.choice(['rain', 'fog', 'snow']),
                'road_condition': random.choice(['wet', 'icy']),
                'time_of_day': random.choice(['day', 'night'])
            },
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_default_scenario(self, risk_level):
        """生成默认场景"""
        return {
            'type': 'default',
            'risk_level': risk_level,
            'parameters': {
                'initial_speed': random.uniform(60, 100),
                'distance': random.uniform(30, 50),
                'reaction_time': random.uniform(0.5, 1.5)
            },
            'environment': {
                'weather': 'clear',
                'road_condition': 'dry',
                'time_of_day': 'day'
            },
            'created_at': datetime.now().isoformat()
        }
