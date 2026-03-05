#!/usr/bin/env python3
"""
CARLA执行器模块 - 增强版
支持无保护左转场景的CARLA仿真执行
"""

import os
import sys
import json
import time
import math
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from .unprotected_left_turn_scenario import UnprotectedLeftTurnScenario

logger = logging.getLogger('CarlaExecutorEnhanced')

class CarlaExecutorEnhanced:
    """CARLA执行器增强版 - 支持无保护左转场景"""
    
    def __init__(self, config_path=None):
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
        self.carla_path = self.carla_config.get('carla_path', 
            '/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA')
        
        self.client = None
        self.world = None
        self.ego_vehicle = None
        self.spectator = None
        self.actors = []
        
        self.collision_sensor = None
        self.collision_detected = False
        self.collision_data = []
        
        self._connect()
    
    def _load_config(self, config_path):
        """加载配置文件"""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        return {
            'carla': {
                'host': 'localhost',
                'port': 2000,
                'town': 'Town05',
                'timeout': 10.0,
                'carla_path': '/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA'
            }
        }
    
    def _connect(self):
        """连接到CARLA服务器"""
        try:
            import carla
            
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(self.timeout)
            self.world = self.client.load_world(self.town)
            self.spectator = self.world.get_spectator()
            
            settings = self.world.get_settings()
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = 0.05
            self.world.apply_settings(settings)
            
            logger.info(f"成功连接到CARLA服务器，加载世界: {self.town}")
        except ImportError:
            logger.error("CARLA Python API未安装")
            logger.info(f"请添加CARLA Python API到Python路径:")
            logger.info(f"export PYTHONPATH=$PYTHONPATH:{self.carla_path}/PythonAPI/carla/dist/carla-0.9.13-py3.7-linux-x86_64.egg")
            raise
        except Exception as e:
            logger.error(f"连接CARLA服务器失败: {e}")
            logger.info(f"请确保CARLA服务器正在运行:")
            logger.info(f"cd {self.carla_path} && ./CarlaUE4.sh")
            raise
    
    def _setup_weather(self, weather_type: str):
        """设置天气
        
        参数:
            weather_type: 天气类型 (clear, rain, fog, night)
        """
        try:
            import carla
            
            if weather_type == 'clear':
                weather_params = carla.WeatherParameters.ClearNoon
            elif weather_type == 'rain':
                weather_params = carla.WeatherParameters.HardRainNoon
            elif weather_type == 'fog':
                weather_params = carla.WeatherParameters.FoggyNoon
            elif weather_type == 'night':
                weather_params = carla.WeatherParameters.ClearNight
            else:
                weather_params = carla.WeatherParameters.ClearNoon
            
            self.world.set_weather(weather_params)
            logger.info(f"设置天气: {weather_type}")
        except Exception as e:
            logger.error(f"设置天气失败: {e}")
    
    def _get_vehicle_blueprint(self, vehicle_type: str):
        """获取车辆蓝图
        
        参数:
            vehicle_type: 车辆类型 (sedan, truck, bus)
            
        返回:
            车辆蓝图
        """
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            if vehicle_type == 'truck':
                vehicle_bp = blueprint_library.filter('vehicle.carlamotors.*')[0]
            elif vehicle_type == 'bus':
                vehicle_bp = blueprint_library.filter('vehicle.volkswagen.*')[0]
            else:
                vehicle_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
            
            return vehicle_bp
        except Exception as e:
            logger.error(f"获取车辆蓝图失败: {e}")
            return None
    
    def _spawn_vehicle(self, blueprint, transform: 'carla.Transform', 
                      autopilot: bool = False):
        """生成车辆
        
        参数:
            blueprint: 车辆蓝图
            transform: 变换矩阵
            autopilot: 是否启用自动驾驶
            
        返回:
            车辆Actor
        """
        try:
            import carla
            
            vehicle = self.world.spawn_actor(blueprint, transform)
            self.actors.append(vehicle)
            
            if autopilot:
                vehicle.set_autopilot(True)
            
            logger.info(f"生成车辆: {vehicle.type_id}")
            return vehicle
        except Exception as e:
            logger.error(f"生成车辆失败: {e}")
            return None
    
    def _setup_collision_sensor(self, vehicle):
        """设置碰撞传感器
        
        参数:
            vehicle: 要监控的车辆
        """
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            collision_bp = blueprint_library.find('sensor.other.collision')
            
            collision_sensor = self.world.spawn_actor(
                collision_bp,
                carla.Transform(carla.Location(x=0, y=0, z=2)),
                attach_to=vehicle
            )
            self.actors.append(collision_sensor)
            
            def on_collision(event):
                self.collision_detected = True
                # 将Vector3D转换为可序列化的字典
                impulse = event.normal_impulse
                self.collision_data.append({
                    'time': time.time(),
                    'other_actor': str(event.other_actor.type_id) if event.other_actor else 'unknown',
                    'impulse': {
                        'x': impulse.x,
                        'y': impulse.y,
                        'z': impulse.z
                    }
                })
                logger.warning(f"检测到碰撞: {event.other_actor}")
            
            collision_sensor.listen(on_collision)
            self.collision_sensor = collision_sensor
            
            logger.info("碰撞传感器已设置")
        except Exception as e:
            logger.error(f"设置碰撞传感器失败: {e}")
    
    def _setup_spectator_camera(self, vehicle):
        """设置观察相机跟随车辆
        
        参数:
            vehicle: 要跟随的车辆
        """
        try:
            import carla
            
            # 获取spectator（观察相机）
            spectator = self.world.get_spectator()
            
            # 获取车辆当前位置
            vehicle_transform = vehicle.get_transform()
            
            # 设置相机位置：车辆后方10米，上方5米，俯视角度
            camera_location = carla.Location(
                x=vehicle_transform.location.x - 15,
                y=vehicle_transform.location.y,
                z=vehicle_transform.location.z + 10
            )
            
            # 设置相机朝向车辆
            camera_rotation = carla.Rotation(
                pitch=-30,  # 向下看30度
                yaw=0,
                roll=0
            )
            
            camera_transform = carla.Transform(camera_location, camera_rotation)
            spectator.set_transform(camera_transform)
            
            logger.info("观察相机已设置，跟随主车")
            
            # 保存spectator引用以便后续更新
            self.spectator = spectator
            
        except Exception as e:
            logger.error(f"设置观察相机失败: {e}")
    
    def _update_spectator_camera(self, vehicle):
        """更新观察相机位置跟随车辆
        
        参数:
            vehicle: 要跟随的车辆
        """
        try:
            import carla
            
            if not hasattr(self, 'spectator') or self.spectator is None:
                return
            
            # 获取车辆当前位置
            vehicle_transform = vehicle.get_transform()
            
            # 计算相机位置：车辆后方15米，上方10米
            # 根据车辆朝向计算后方位置
            yaw_rad = math.radians(vehicle_transform.rotation.yaw)
            offset_x = -15 * math.cos(yaw_rad)
            offset_y = -15 * math.sin(yaw_rad)
            
            camera_location = carla.Location(
                x=vehicle_transform.location.x + offset_x,
                y=vehicle_transform.location.y + offset_y,
                z=vehicle_transform.location.z + 10
            )
            
            # 设置相机朝向车辆
            camera_rotation = carla.Rotation(
                pitch=-30,
                yaw=vehicle_transform.rotation.yaw,
                roll=0
            )
            
            camera_transform = carla.Transform(camera_location, camera_rotation)
            self.spectator.set_transform(camera_transform)
            
        except Exception as e:
            logger.warning(f"更新观察相机失败: {e}")
    
    def _get_intersection_transform(self) -> 'carla.Transform':
        """获取路口变换矩阵
        
        返回:
            路口变换矩阵
        """
        try:
            import carla
            
            spawn_points = self.world.get_map().get_spawn_points()
            
            for i, spawn_point in enumerate(spawn_points):
                if i % 10 == 0:
                    return spawn_point
            
            return spawn_points[0]
        except Exception as e:
            logger.error(f"获取路口变换矩阵失败: {e}")
            return None
    
    def _execute_unprotected_left_turn(self, scenario: Dict) -> Dict:
        """执行无保护左转场景 - 使用新的场景类
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        try:
            import carla
            
            params = scenario.get('parameters', {})
            
            # 创建场景实例
            scenario_executor = UnprotectedLeftTurnScenario(self.world, self.client)
            
            # 设置场景
            if not scenario_executor.setup_scenario(params):
                raise Exception("场景设置失败")
            
            # 执行场景
            result = scenario_executor.execute(max_duration=30.0)
            
            # 添加场景信息
            result['scenario_id'] = scenario.get('id')
            result['scenario_type'] = scenario.get('type', 'unprotected_left_turn')
            result['parameters'] = params
            result['timestamp'] = datetime.now().isoformat()
            result['environment'] = 'CARLA'
            
            # 清理场景
            scenario_executor.cleanup()
            
            return result
            
        except Exception as e:
            logger.error(f"执行无保护左转场景失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'scenario_id': scenario.get('id'),
                'timestamp': datetime.now().isoformat(),
                'environment': 'CARLA'
            }
    
    def execute(self, scenario: Dict) -> Dict:
        """执行场景测试
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        try:
            scenario_type = scenario.get('type', 'unprotected_left_turn')
            
            # 支持多种场景类型命名格式
            if scenario_type in ['unprotected_left_turn', 'unprotected-left-turn']:
                result = self._execute_unprotected_left_turn(scenario)
            else:
                logger.warning(f"不支持的场景类型: {scenario_type}")
                result = {
                    'success': False,
                    'error': f'不支持的场景类型: {scenario_type}',
                    'scenario_id': scenario.get('id')
                }
            
            return result
            
        except Exception as e:
            logger.error(f"执行场景测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'scenario_id': scenario.get('id'),
                'timestamp': datetime.now().isoformat(),
                'environment': 'CARLA'
            }
    
    def cleanup(self):
        """清理资源"""
        try:
            import carla
            
            for actor in self.actors:
                if actor.is_alive:
                    actor.destroy()
            
            self.actors.clear()
            
            if self.ego_vehicle and self.ego_vehicle.is_alive:
                self.ego_vehicle.destroy()
                self.ego_vehicle = None
            
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    def start_carla_server(self) -> bool:
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
            
            import subprocess
            subprocess.Popen([carla_script], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            
            time.sleep(10)
            
            self._connect()
            
            logger.info("CARLA服务器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动CARLA服务器失败: {e}")
            return False
    
    def is_carla_running(self) -> bool:
        """检查CARLA是否正在运行
        
        返回:
            是否正在运行
        """
        try:
            if self.client:
                self.client.get_world()
                return True
            return False
        except Exception as e:
            logger.debug(f"CARLA未运行: {e}")
            return False
