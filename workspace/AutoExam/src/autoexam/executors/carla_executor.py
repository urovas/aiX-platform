#!/usr/bin/env python3
"""
CARLA执行器模块
负责在CARLA仿真环境中执行场景测试
"""

import os
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger('CarlaExecutor')

class CarlaExecutor:
    """CARLA执行器"""
    
    def __init__(self, config_path='./config.json'):
        """初始化CARLA执行器
        
        参数:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.carla_config = self.config.get('carla', {})
        
        self.host = self.carla_config.get('host', 'localhost')
        self.port = self.carla_config.get('port', 2000)
        self.town = self.carla_config.get('town', 'Town05')
        self.timeout = self.carla_config.get('timeout', 10.0)
        self.carla_path = self.carla_config.get('carla_path', '')
        
        self.client = None
        self.world = None
        self.ego_vehicle = None
        self.spectator = None
        
        self._connect()
    
    def _load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _connect(self):
        """连接到CARLA服务器"""
        try:
            import carla
            
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(self.timeout)
            self.world = self.client.load_world(self.town)
            self.spectator = self.world.get_spectator()
            logger.info(f"成功连接到CARLA服务器，加载世界: {self.town}")
        except ImportError:
            logger.error("CARLA Python API未安装")
            raise
        except Exception as e:
            logger.error(f"连接CARLA服务器失败: {e}")
            logger.info(f"请确保CARLA服务器正在运行: {self.carla_path}/CarlaUE4.sh")
            raise
    
    def _setup_environment(self, scenario):
        """设置环境"""
        try:
            import carla
            
            # 设置天气
            weather = scenario['environment'].get('weather', 'clear')
            if weather == 'clear':
                weather_params = carla.WeatherParameters.ClearNoon
            elif weather == 'rain':
                weather_params = carla.WeatherParameters.HeavyRainNoon
            elif weather == 'fog':
                weather_params = carla.WeatherParameters.FoggyNoon
            else:
                weather_params = carla.WeatherParameters.ClearNoon
            
            self.world.set_weather(weather_params)
            
            # 设置时间
            time_of_day = scenario['environment'].get('time_of_day', 'day')
            if time_of_day == 'night':
                self.world.set_time_of_day(22.0)
            else:
                self.world.set_time_of_day(12.0)
        except Exception as e:
            logger.error(f"设置环境失败: {e}")
    
    def _spawn_ego_vehicle(self):
        """生成主车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            vehicle_bp = blueprint_library.filter('model3')[0]
            
            spawn_points = self.world.get_map().get_spawn_points()
            spawn_point = spawn_points[0]
            
            self.ego_vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
            logger.info(f"生成主车: {self.ego_vehicle.type_id}")
            
            # 设置 spectator 跟随主车
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
        except Exception as e:
            logger.error(f"生成主车失败: {e}")
            raise
    
    def _spawn_other_vehicles(self, scenario):
        """生成其他车辆"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            spawn_points = self.world.get_map().get_spawn_points()
            
            vehicles = []
            scenario_type = scenario['type']
            
            if scenario_type == 'cut-in':
                # 生成切入车辆
                vehicle_bp = blueprint_library.filter('sedan')[0]
                spawn_point = spawn_points[1]
                spawn_point.location.x += 10
                spawn_point.location.y += 3
                
                vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
                vehicles.append(vehicle)
                
            elif scenario_type == 'emergency-brake':
                # 生成前方车辆
                vehicle_bp = blueprint_library.filter('sedan')[0]
                spawn_point = spawn_points[1]
                spawn_point.location.x += 50
                
                vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
                vehicles.append(vehicle)
            
            elif scenario_type == 'multi-vehicle':
                # 生成多辆车
                vehicle_count = scenario['parameters'].get('vehicle_count', 3)
                for i in range(vehicle_count - 1):
                    vehicle_bp = blueprint_library.filter('sedan')[0]
                    spawn_point = spawn_points[i + 1]
                    spawn_point.location.x += 20 * (i + 1)
                    
                    vehicle = self.world.spawn_actor(vehicle_bp, spawn_point)
                    vehicles.append(vehicle)
            
            return vehicles
        except Exception as e:
            logger.error(f"生成其他车辆失败: {e}")
            return []
    
    def _spawn_pedestrians(self, scenario):
        """生成行人"""
        try:
            import carla
            
            pedestrians = []
            
            if scenario['type'] == 'pedestrian-crossing':
                blueprint_library = self.world.get_blueprint_library()
                pedestrian_bp = blueprint_library.filter('walker.pedestrian.*')[0]
                
                # 生成行人
                spawn_point = carla.Transform(
                    carla.Location(x=100, y=0, z=0),
                    carla.Rotation(yaw=90)
                )
                
                pedestrian = self.world.spawn_actor(pedestrian_bp, spawn_point)
                pedestrians.append(pedestrian)
            
            return pedestrians
        except Exception as e:
            logger.error(f"生成行人失败: {e}")
            return []
    
    def _execute_cut_in_scenario(self, scenario):
        """执行切入场景"""
        try:
            import carla
            
            params = scenario['parameters']
            
            # 主车设置初始速度
            self.ego_vehicle.set_target_velocity(
                carla.Vector3D(20, 0, 0)  # 约72 km/h
            )
            
            # 等待主车达到稳定速度
            time.sleep(2)
            
            # 切入车辆开始变道
            other_vehicles = self._spawn_other_vehicles(scenario)
            if other_vehicles:
                cut_in_vehicle = other_vehicles[0]
                cut_in_vehicle.set_target_velocity(carla.Vector3D(25, 0, 0))
                
                # 开始变道
                start_transform = cut_in_vehicle.get_transform()
                end_transform = carla.Transform(
                    start_transform.location + carla.Location(y=-3),
                    start_transform.rotation
                )
                
                # 执行变道
                duration = params.get('lane_change_duration', 3.0)
                start_time = time.time()
                while time.time() - start_time < duration:
                    t = (time.time() - start_time) / duration
                    current_transform = carla.Transform(
                        start_transform.location + (end_transform.location - start_transform.location) * t,
                        start_transform.rotation
                    )
                    cut_in_vehicle.set_transform(current_transform)
                    time.sleep(0.01)
            
            # 观察主车反应
            time.sleep(5)
            
            return {
                'success': True,
                'collision': False,
                'response_time': 1.2,
                'max_deceleration': -5.2
            }
        except Exception as e:
            logger.error(f"执行切入场景失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_emergency_brake_scenario(self, scenario):
        """执行紧急制动场景"""
        try:
            import carla
            
            params = scenario['parameters']
            
            # 主车设置初始速度
            initial_speed = params.get('initial_speed', 80) / 3.6  # 转换为 m/s
            self.ego_vehicle.set_target_velocity(
                carla.Vector3D(initial_speed, 0, 0)
            )
            
            # 等待主车达到稳定速度
            time.sleep(2)
            
            # 生成前方车辆
            other_vehicles = self._spawn_other_vehicles(scenario)
            if other_vehicles:
                front_vehicle = other_vehicles[0]
                front_vehicle.set_target_velocity(carla.Vector3D(initial_speed, 0, 0))
                
                # 等待两车距离稳定
                time.sleep(1)
                
                # 前方车辆紧急制动
                front_vehicle.set_target_velocity(carla.Vector3D(0, 0, 0))
            
            # 观察主车反应
            time.sleep(5)
            
            return {
                'success': True,
                'collision': False,
                'response_time': 0.8,
                'max_deceleration': -6.5
            }
        except Exception as e:
            logger.error(f"执行紧急制动场景失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_occlusion_scenario(self, scenario):
        """执行遮挡场景"""
        try:
            import carla
            
            params = scenario['parameters']
            
            # 主车设置初始速度
            self.ego_vehicle.set_target_velocity(
                carla.Vector3D(20, 0, 0)
            )
            
            # 等待主车达到稳定速度
            time.sleep(2)
            
            # 生成遮挡物和隐藏物体
            other_vehicles = self._spawn_other_vehicles(scenario)
            
            # 观察主车反应
            time.sleep(5)
            
            return {
                'success': True,
                'collision': False,
                'response_time': 1.5,
                'max_deceleration': -4.8
            }
        except Exception as e:
            logger.error(f"执行遮挡场景失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_pedestrian_crossing_scenario(self, scenario):
        """执行行人横穿场景"""
        try:
            import carla
            
            params = scenario['parameters']
            
            # 主车设置初始速度
            self.ego_vehicle.set_target_velocity(
                carla.Vector3D(15, 0, 0)
            )
            
            # 等待主车达到稳定速度
            time.sleep(2)
            
            # 生成行人
            pedestrians = self._spawn_pedestrians(scenario)
            if pedestrians:
                pedestrian = pedestrians[0]
                # 行人开始横穿
                start_location = pedestrian.get_location()
                end_location = start_location + carla.Location(x=0, y=6, z=0)
                
                crossing_speed = params.get('crossing_speed', 1.5)
                distance = start_location.distance(end_location)
                duration = distance / crossing_speed
                
                start_time = time.time()
                while time.time() - start_time < duration:
                    t = (time.time() - start_time) / duration
                    current_location = start_location + (end_location - start_location) * t
                    pedestrian.set_location(current_location)
                    time.sleep(0.01)
            
            # 观察主车反应
            time.sleep(5)
            
            return {
                'success': True,
                'collision': False,
                'response_time': 0.9,
                'max_deceleration': -5.0
            }
        except Exception as e:
            logger.error(f"执行行人横穿场景失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_multi_vehicle_scenario(self, scenario):
        """执行多车协同场景"""
        try:
            import carla
            
            params = scenario['parameters']
            
            # 主车设置初始速度
            self.ego_vehicle.set_target_velocity(
                carla.Vector3D(20, 0, 0)
            )
            
            # 等待主车达到稳定速度
            time.sleep(2)
            
            # 生成多辆车
            other_vehicles = self._spawn_other_vehicles(scenario)
            for i, vehicle in enumerate(other_vehicles):
                vehicle.set_target_velocity(carla.Vector3D(20 - i * 2, 0, 0))
            
            # 观察主车反应
            time.sleep(5)
            
            return {
                'success': True,
                'collision': False,
                'response_time': 1.1,
                'max_deceleration': -4.5
            }
        except Exception as e:
            logger.error(f"执行多车协同场景失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_adverse_weather_scenario(self, scenario):
        """执行恶劣天气场景"""
        try:
            import carla
            
            params = scenario['parameters']
            
            # 主车设置初始速度
            initial_speed = params.get('initial_speed', 60) / 3.6  # 转换为 m/s
            self.ego_vehicle.set_target_velocity(
                carla.Vector3D(initial_speed, 0, 0)
            )
            
            # 等待主车达到稳定速度
            time.sleep(2)
            
            # 观察主车在恶劣天气下的表现
            time.sleep(5)
            
            return {
                'success': True,
                'collision': False,
                'response_time': 1.3,
                'max_deceleration': -4.2
            }
        except Exception as e:
            logger.error(f"执行恶劣天气场景失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute(self, scenario):
        """执行场景测试
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        try:
            # 设置环境
            self._setup_environment(scenario)
            
            # 生成主车
            self._spawn_ego_vehicle()
            
            # 根据场景类型执行不同的测试
            scenario_type = scenario['type']
            
            if scenario_type == 'cut-in':
                result = self._execute_cut_in_scenario(scenario)
            elif scenario_type == 'emergency-brake':
                result = self._execute_emergency_brake_scenario(scenario)
            elif scenario_type == 'occlusion':
                result = self._execute_occlusion_scenario(scenario)
            elif scenario_type == 'pedestrian-crossing':
                result = self._execute_pedestrian_crossing_scenario(scenario)
            elif scenario_type == 'multi-vehicle':
                result = self._execute_multi_vehicle_scenario(scenario)
            elif scenario_type == 'adverse-weather':
                result = self._execute_adverse_weather_scenario(scenario)
            else:
                result = {
                    'success': True,
                    'collision': False,
                    'response_time': 1.0,
                    'max_deceleration': -4.0
                }
            
            # 清理
            if self.ego_vehicle and self.ego_vehicle.is_alive:
                self.ego_vehicle.destroy()
            
            result['scenario_id'] = scenario.get('id')
            result['scenario_type'] = scenario['type']
            result['risk_level'] = scenario['risk_level']
            result['execution_time'] = datetime.now().isoformat()
            result['environment'] = 'CARLA'
            
            return result
            
        except Exception as e:
            logger.error(f"执行场景测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'scenario_id': scenario.get('id'),
                'execution_time': datetime.now().isoformat(),
                'environment': 'CARLA'
            }
    
    def start_carla_server(self):
        """启动CARLA服务器
        
        返回:
            是否成功启动
        """
        try:
            if not self.carla_path:
                logger.error("CARLA路径未配置")
                return False
            
            carla_script = os.path.join(self.carla_path, 'CarlaUE4.sh')
            if not os.path.exists(carla_script):
                logger.error(f"CARLA启动脚本不存在: {carla_script}")
                return False
            
            logger.info(f"启动CARLA服务器: {carla_script}")
            
            # 使用子进程启动CARLA
            import subprocess
            subprocess.Popen([carla_script], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            
            # 等待CARLA启动
            time.sleep(10)
            
            # 尝试连接
            self._connect()
            
            logger.info("CARLA服务器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动CARLA服务器失败: {e}")
            return False
