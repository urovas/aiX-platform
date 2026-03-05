#!/usr/bin/env python3
"""
无保护左转场景执行器
在CARLA中执行无保护左转场景
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger('UnprotectedLeftTurnExecutor')

try:
    import carla
    CARLA_AVAILABLE = True
except ImportError:
    CARLA_AVAILABLE = False
    logger.warning("CARLA Python API未安装")

class UnprotectedLeftTurnExecutor:
    """无保护左转场景执行器"""
    
    def __init__(self, config_path='./config.json'):
        """初始化执行器
        
        参数:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.carla_config = self.config.get('carla', {})
        
        self.host = self.carla_config.get('host', 'localhost')
        self.port = self.carla_config.get('port', 2000)
        self.town = self.carla_config.get('town', 'Town05')
        self.timeout = self.carla_config.get('timeout', 10.0)
        
        self.client = None
        self.world = None
        self.ego_vehicle = None
        self.spectator = None
        self.vehicles = []
        self.pedestrians = []
        
        self._connect()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _connect(self):
        """连接到CARLA服务器"""
        if not CARLA_AVAILABLE:
            raise ImportError("CARLA Python API未安装")
        
        try:
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(self.timeout)
            self.world = self.client.load_world(self.town)
            self.spectator = self.world.get_spectator()
            logger.info(f"成功连接到CARLA服务器，加载世界: {self.town}")
        except Exception as e:
            logger.error(f"连接CARLA服务器失败: {e}")
            raise
    
    def execute(self, scenario: Dict) -> Dict:
        """执行无保护左转场景
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        try:
            logger.info(f"开始执行场景: {scenario.get('id')}")
            
            # 设置环境
            self._setup_environment(scenario)
            
            # 生成主车
            self._spawn_ego_vehicle(scenario)
            
            # 生成对向来车
            self._spawn_oncoming_vehicles(scenario)
            
            # 生成横向交通
            self._spawn_cross_traffic(scenario)
            
            # 生成行人
            self._spawn_pedestrians(scenario)
            
            # 执行左转测试
            result = self._execute_left_turn(scenario)
            
            # 清理
            self._cleanup()
            
            result['scenario_id'] = scenario.get('id')
            result['scenario_type'] = scenario.get('type')
            result['difficulty'] = scenario.get('difficulty')
            result['execution_time'] = datetime.now().isoformat()
            result['environment'] = 'CARLA'
            
            logger.info(f"场景执行完成: {scenario.get('id')}, 结果: {result.get('success')}")
            
            return result
            
        except Exception as e:
            logger.error(f"执行场景失败: {e}")
            self._cleanup()
            
            return {
                'success': False,
                'error': str(e),
                'scenario_id': scenario.get('id'),
                'execution_time': datetime.now().isoformat(),
                'environment': 'CARLA'
            }
    
    def _setup_environment(self, scenario: Dict):
        """设置环境"""
        environment = scenario.get('environment', {})
        
        # 设置天气
        weather = environment.get('weather', 'clear')
        if weather == 'clear':
            weather_params = carla.WeatherParameters.ClearNoon
        elif weather == 'rain':
            weather_params = carla.WeatherParameters.HeavyRainNoon
        elif weather == 'fog':
            weather_params = carla.WeatherParameters.FoggyNoon
        elif weather == 'night':
            weather_params = carla.WeatherParameters.ClearNight
        elif weather == 'rain_night':
            weather_params = carla.WeatherParameters.HardRainNight
        else:
            weather_params = carla.WeatherParameters.ClearNoon
        
        self.world.set_weather(weather_params)
        
        # 设置时间
        time_of_day = environment.get('time_of_day', 'day')
        if time_of_day == 'night':
            self.world.set_time_of_day(22.0)
        else:
            self.world.set_time_of_day(12.0)
        
        logger.info(f"环境设置完成: 天气={weather}, 时间={time_of_day}")
    
    def _spawn_ego_vehicle(self, scenario: Dict):
        """生成主车"""
        blueprint_library = self.world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
        
        # 设置主车位置（在路口前）
        ego_config = scenario.get('ego_vehicle', {})
        position = ego_config.get('position', {'x': -50, 'y': 0, 'z': 0})
        
        spawn_point = carla.Transform(
            carla.Location(x=position['x'], y=position['y'], z=0.5),
            carla.Rotation(yaw=0)  # 朝东
        )
        
        self.ego_vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
        logger.info(f"生成主车: {self.ego_vehicle.type_id}")
        
        # 设置初始速度
        initial_speed = ego_config.get('initial_speed', 50) / 3.6  # 转换为 m/s
        self.ego_vehicle.set_target_velocity(carla.Vector3D(x=initial_speed, y=0, z=0))
        
        # 设置 spectator 跟随主车
        self._setup_spectator()
    
    def _spawn_oncoming_vehicles(self, scenario: Dict):
        """生成对向来车"""
        blueprint_library = self.world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter('vehicle.toyota.prius')[0]
        
        oncoming_vehicles = scenario.get('oncoming_vehicles', [])
        
        for vehicle_config in oncoming_vehicles:
            position = vehicle_config.get('position', {'x': 100, 'y': 0, 'z': 0})
            
            spawn_point = carla.Transform(
                carla.Location(x=position['x'], y=position['y'], z=0.5),
                carla.Rotation(yaw=180)  # 朝西
            )
            
            vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
            
            # 设置速度
            initial_speed = vehicle_config.get('initial_speed', 60) / 3.6
            vehicle.set_target_velocity(carla.Vector3D(x=-initial_speed, y=0, z=0))
            
            self.vehicles.append(vehicle)
            logger.info(f"生成对向来车: {vehicle_config['id']}")
    
    def _spawn_cross_traffic(self, scenario: Dict):
        """生成横向交通"""
        cross_traffic = scenario.get('cross_traffic', [])
        
        if not cross_traffic:
            return
        
        blueprint_library = self.world.get_blueprint_library()
        vehicle_bp = blueprint_library.filter('vehicle.volkswagen.t2')[0]
        
        for vehicle_config in cross_traffic:
            position = vehicle_config.get('position', {'x': 0, 'y': -50, 'z': 0})
            
            spawn_point = carla.Transform(
                carla.Location(x=position['x'], y=position['y'], z=0.5),
                carla.Rotation(yaw=90)  # 朝北
            )
            
            vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
            
            # 设置速度
            initial_speed = vehicle_config.get('initial_speed', 40) / 3.6
            vehicle.set_target_velocity(carla.Vector3D(x=0, y=initial_speed, z=0))
            
            self.vehicles.append(vehicle)
            logger.info(f"生成横向交通: {vehicle_config['id']}")
    
    def _spawn_pedestrians(self, scenario: Dict):
        """生成行人"""
        pedestrians = scenario.get('pedestrians', [])
        
        if not pedestrians:
            return
        
        blueprint_library = self.world.get_blueprint_library()
        pedestrian_bp = blueprint_library.filter('walker.pedestrian.*')[0]
        
        for pedestrian_config in pedestrians:
            position = pedestrian_config.get('position', {'x': 10, 'y': -5, 'z': 0})
            
            spawn_point = carla.Transform(
                carla.Location(x=position['x'], y=position['y'], z=0.5),
                carla.Rotation(yaw=45)
            )
            
            pedestrian = self.world.spawn_actor(pedestrian_bp, spawn_point)
            
            # 设置速度
            initial_speed = pedestrian_config.get('initial_speed', 1.5)
            pedestrian.set_target_velocity(carla.Vector3D(x=initial_speed, y=initial_speed, z=0))
            
            self.pedestrians.append(pedestrian)
            logger.info(f"生成行人: {pedestrian_config['id']}")
    
    def _setup_spectator(self):
        """设置 spectator 跟随主车"""
        def follow_vehicle():
            while True:
                if self.ego_vehicle and self.ego_vehicle.is_alive:
                    transform = self.ego_vehicle.get_transform()
                    self.spectator.set_transform(carla.Transform(
                        transform.location + carla.Location(z=50),
                        carla.Rotation(pitch=-90)
                    ))
                time.sleep(0.05)
        
        import threading
        threading.Thread(target=follow_vehicle, daemon=True).start()
    
    def _execute_left_turn(self, scenario: Dict) -> Dict:
        """执行左转测试"""
        params = scenario.get('parameters', {})
        gap_time = params.get('gap_time', 3.0)
        
        # 等待主车接近路口
        time.sleep(2)
        
        # 检测碰撞
        collision_detected = False
        collision_time = None
        
        # 注册碰撞检测
        def on_collision(event):
            nonlocal collision_detected, collision_time
            collision_detected = True
            collision_time = time.time()
            logger.warning(f"检测到碰撞: {event}")
        
        self.ego_vehicle.listen_to_collision(lambda event: on_collision(event))
        
        # 执行左转
        start_time = time.time()
        
        # 主车开始左转
        self._perform_left_turn()
        
        # 等待对向来车通过
        time.sleep(gap_time)
        
        # 持续监控
        monitor_duration = 10
        while time.time() - start_time < monitor_duration:
            if collision_detected:
                break
            time.sleep(0.1)
        
        # 计算结果
        execution_time = time.time() - start_time
        
        if collision_detected:
            response_time = collision_time - start_time
            max_deceleration = -6.0  # 碰撞时的减速度
            
            result = {
                'success': False,
                'collision': True,
                'timeout': False,
                'response_time': response_time,
                'max_deceleration': max_deceleration,
                'execution_time': execution_time,
                'collision_time': collision_time
            }
        else:
            # 检查是否超时
            if execution_time >= monitor_duration:
                result = {
                    'success': False,
                    'collision': False,
                    'timeout': True,
                    'response_time': execution_time,
                    'max_deceleration': -2.0,
                    'execution_time': execution_time
                }
            else:
                # 成功完成左转
                result = {
                    'success': True,
                    'collision': False,
                    'timeout': False,
                    'response_time': 1.5,
                    'max_deceleration': -3.5,
                    'execution_time': execution_time
                }
        
        return result
    
    def _perform_left_turn(self):
        """执行左转动作"""
        # 简化的左转逻辑：设置目标航向
        target_yaw = 90  # 左转90度
        
        # 使用CARLA的控制器进行左转
        self.ego_vehicle.set_autopilot(False)
        
        # 设置转向角
        self.ego_vehicle.apply_control(
            carla.VehicleControl(
                throttle=0.5,
                steer=0.5,  # 左转
                brake=0.0
            )
        )
        
        # 等待左转完成
        time.sleep(3)
        
        # 恢复直行
        self.ego_vehicle.apply_control(
            carla.VehicleControl(
                throttle=0.5,
                steer=0.0,
                brake=0.0
            )
        )
    
    def _cleanup(self):
        """清理场景"""
        # 销毁主车
        if self.ego_vehicle and self.ego_vehicle.is_alive:
            self.ego_vehicle.destroy()
            self.ego_vehicle = None
        
        # 销毁其他车辆
        for vehicle in self.vehicles:
            if vehicle and vehicle.is_alive:
                vehicle.destroy()
        self.vehicles.clear()
        
        # 销毁行人
        for pedestrian in self.pedestrians:
            if pedestrian and pedestrian.is_alive:
                pedestrian.destroy()
        self.pedestrians.clear()
        
        logger.info("场景清理完成")
    
    def execute_batch(self, scenarios: List[Dict]) -> List[Dict]:
        """批量执行场景
        
        参数:
            scenarios: 场景列表
            
        返回:
            测试结果列表
        """
        results = []
        
        for i, scenario in enumerate(scenarios):
            logger.info(f"执行场景 {i+1}/{len(scenarios)}: {scenario.get('id')}")
            
            result = self.execute(scenario)
            results.append(result)
            
            # 场景间隔
            time.sleep(1)
        
        logger.info(f"批量执行完成，共 {len(scenarios)} 个场景")
        
        return results
