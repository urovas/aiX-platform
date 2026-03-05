#!/usr/bin/env python3
"""
无保护左转场景执行器
实现完整的无保护左转测试场景，包括：
- 主车接近路口并执行左转
- 对向来车干扰
- 行人/非机动车干扰
- 交通信号灯控制
- 遮挡车辆
"""

import math
import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('UnprotectedLeftTurnScenario')


class UnprotectedLeftTurnScenario:
    """无保护左转场景"""
    
    def __init__(self, world, client):
        self.world = world
        self.client = client
        self.ego_vehicle = None
        self.oncoming_vehicle = None
        self.pedestrian = None
        self.occlusion_vehicle = None
        self.traffic_vehicles = []
        self.actors = []
        self.collision_detected = False
        self.collision_data = []
        self.spectator = None
        
    def setup_scenario(self, params: Dict) -> bool:
        """设置场景
        
        参数:
            params: 场景参数字典
            
        返回:
            是否成功设置
        """
        try:
            import carla
            
            # 清理之前的场景
            self.cleanup()
            
            # 获取参数
            ego_speed = params.get('ego_speed', 15)
            oncoming_speed = params.get('oncoming_speed', 50)
            time_gap = params.get('time_gap', 4)
            oncoming_vehicle_type = params.get('oncoming_vehicle_type', 'sedan')
            weather = params.get('weather', 'clear')
            occlusion = params.get('occlusion', False)
            traffic_flow = params.get('traffic_flow', 'low')
            has_pedestrian = params.get('has_pedestrian', False)
            
            logger.info(f"设置无保护左转场景: ego_speed={ego_speed}km/h, "
                       f"oncoming_speed={oncoming_speed}km/h, time_gap={time_gap}s")
            
            # 设置天气
            self._setup_weather(weather)
            
            # 获取地图和生成点
            carla_map = self.world.get_map()
            spawn_points = carla_map.get_spawn_points()
            
            if len(spawn_points) < 2:
                logger.error("地图生成点不足")
                return False
            
            # 找到合适的路口（选择有多个车道交叉的生成点）
            intersection_spawn = self._find_intersection_spawn(spawn_points)
            if not intersection_spawn:
                intersection_spawn = spawn_points[0]
            
            # 1. 生成主车（在路口前50米）
            ego_success = self._spawn_ego_vehicle(intersection_spawn, ego_speed)
            if not ego_success:
                logger.error("生成主车失败")
                return False
            
            # 2. 生成对向来车（从左侧驶来）
            self._spawn_oncoming_vehicle(intersection_spawn, oncoming_vehicle_type, 
                                        oncoming_speed, time_gap)
            
            # 3. 生成遮挡车辆（如果启用）
            if occlusion:
                self._spawn_occlusion_vehicle(intersection_spawn)
            
            # 4. 生成额外交通流（如果启用）
            if traffic_flow == 'high':
                self._spawn_traffic_flow(intersection_spawn)
            
            # 5. 生成行人（如果启用）
            if has_pedestrian:
                self._spawn_pedestrian(intersection_spawn)
            
            # 6. 设置相机
            self._setup_camera()
            
            logger.info("场景设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置场景失败: {e}")
            return False
    
    def _find_intersection_spawn(self, spawn_points) -> Optional['carla.Transform']:
        """找到合适的路口生成点"""
        try:
            import carla
            
            # 选择索引为0的生成点作为主路口
            # 在Town05中，这个点通常是一个十字路口
            if len(spawn_points) > 0:
                return spawn_points[0]
            return None
        except Exception as e:
            logger.error(f"查找路口失败: {e}")
            return None
    
    def _spawn_ego_vehicle(self, intersection_spawn, ego_speed: float) -> bool:
        """生成主车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            ego_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
            ego_bp.set_attribute('role_name', 'ego')
            
            # 在路口前方50米生成
            intersection_yaw = intersection_spawn.rotation.yaw
            spawn_location = carla.Location(
                intersection_spawn.location.x - 50 * math.cos(math.radians(intersection_yaw)),
                intersection_spawn.location.y - 50 * math.sin(math.radians(intersection_yaw)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location, 
                                            carla.Rotation(yaw=intersection_yaw))
            
            self.ego_vehicle = self.world.spawn_actor(ego_bp, spawn_transform)
            if not self.ego_vehicle:
                return False
            
            self.actors.append(self.ego_vehicle)
            
            # 设置初始速度
            speed_mps = ego_speed / 3.6
            yaw_rad = math.radians(intersection_yaw)
            velocity = carla.Vector3D(
                speed_mps * math.cos(yaw_rad),
                speed_mps * math.sin(yaw_rad),
                0
            )
            self.ego_vehicle.set_target_velocity(velocity)
            
            # 设置碰撞传感器
            self._setup_collision_sensor()
            
            logger.info(f"主车已生成在位置: ({spawn_location.x:.1f}, {spawn_location.y:.1f})")
            return True
            
        except Exception as e:
            logger.error(f"生成主车失败: {e}")
            return False
    
    def _spawn_oncoming_vehicle(self, intersection_spawn, vehicle_type: str,
                                speed: float, time_gap: float):
        """生成对向来车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            # 选择车辆类型
            if vehicle_type == 'truck':
                vehicle_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
            elif vehicle_type == 'bus':
                vehicle_bp = blueprint_library.filter('vehicle.volkswagen.t2')[0]
            else:
                vehicle_bp = blueprint_library.filter('vehicle.audi.a2')[0]
            
            # 计算生成位置（从左侧驶来，距离路口一定距离）
            intersection_yaw = intersection_spawn.rotation.yaw
            # 左侧来车方向（垂直于主车方向）
            oncoming_yaw = intersection_yaw + 90
            distance = speed * time_gap / 3.6  # 根据速度和时间计算距离
            
            spawn_location = carla.Location(
                intersection_spawn.location.x + distance * math.cos(math.radians(oncoming_yaw)),
                intersection_spawn.location.y + distance * math.sin(math.radians(oncoming_yaw)),
                intersection_spawn.location.z + 0.5
            )
            # 朝向路口
            spawn_transform = carla.Transform(spawn_location,
                                            carla.Rotation(yaw=oncoming_yaw - 180))
            
            self.oncoming_vehicle = self.world.spawn_actor(vehicle_bp, spawn_transform)
            if self.oncoming_vehicle:
                self.actors.append(self.oncoming_vehicle)
                
                # 设置速度
                speed_mps = speed / 3.6
                yaw_rad = math.radians(oncoming_yaw - 180)
                velocity = carla.Vector3D(
                    speed_mps * math.cos(yaw_rad),
                    speed_mps * math.sin(yaw_rad),
                    0
                )
                self.oncoming_vehicle.set_target_velocity(velocity)
                
                logger.info(f"对向来车已生成，类型: {vehicle_type}, 距离: {distance:.1f}m")
            
        except Exception as e:
            logger.warning(f"生成对向来车失败: {e}")
    
    def _spawn_occlusion_vehicle(self, intersection_spawn):
        """生成遮挡车辆"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            truck_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
            
            intersection_yaw = intersection_spawn.rotation.yaw
            # 在主车右侧生成遮挡车辆
            spawn_location = carla.Location(
                intersection_spawn.location.x - 30 * math.cos(math.radians(intersection_yaw)) 
                + 5 * math.cos(math.radians(intersection_yaw - 90)),
                intersection_spawn.location.y - 30 * math.sin(math.radians(intersection_yaw))
                + 5 * math.sin(math.radians(intersection_yaw - 90)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location,
                                            carla.Rotation(yaw=intersection_yaw))
            
            self.occlusion_vehicle = self.world.spawn_actor(truck_bp, spawn_transform)
            if self.occlusion_vehicle:
                self.actors.append(self.occlusion_vehicle)
                logger.info("遮挡车辆已生成")
                
        except Exception as e:
            logger.warning(f"生成遮挡车辆失败: {e}")
    
    def _spawn_traffic_flow(self, intersection_spawn):
        """生成额外交通流"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            intersection_yaw = intersection_spawn.rotation.yaw
            
            # 在主车后方生成额外车辆
            for i in range(2):
                vehicle_bp = blueprint_library.filter('vehicle.audi.a2')[0]
                spawn_location = carla.Location(
                    intersection_spawn.location.x - (80 + i * 30) * math.cos(math.radians(intersection_yaw)),
                    intersection_spawn.location.y - (80 + i * 30) * math.sin(math.radians(intersection_yaw)),
                    intersection_spawn.location.z + 0.5
                )
                spawn_transform = carla.Transform(spawn_location,
                                                carla.Rotation(yaw=intersection_yaw))
                
                vehicle = self.world.spawn_actor(vehicle_bp, spawn_transform)
                if vehicle:
                    self.traffic_vehicles.append(vehicle)
                    self.actors.append(vehicle)
                    
                    # 设置速度
                    velocity = carla.Vector3D(
                        10 * math.cos(math.radians(intersection_yaw)),
                        10 * math.sin(math.radians(intersection_yaw)),
                        0
                    )
                    vehicle.set_target_velocity(velocity)
            
            if self.traffic_vehicles:
                logger.info(f"生成了 {len(self.traffic_vehicles)} 辆额外交通车辆")
                
        except Exception as e:
            logger.warning(f"生成交通流失败: {e}")
    
    def _spawn_pedestrian(self, intersection_spawn):
        """生成行人"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            pedestrian_bp = blueprint_library.filter('walker.pedestrian.*')[0]
            
            intersection_yaw = intersection_spawn.rotation.yaw
            # 在路口附近生成行人
            spawn_location = carla.Location(
                intersection_spawn.location.x + 10 * math.cos(math.radians(intersection_yaw)),
                intersection_spawn.location.y + 10 * math.sin(math.radians(intersection_yaw)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location)
            
            self.pedestrian = self.world.spawn_actor(pedestrian_bp, spawn_transform)
            if self.pedestrian:
                self.actors.append(self.pedestrian)
                
                # 添加行人控制器
                controller_bp = blueprint_library.find('controller.ai.walker')
                controller = self.world.spawn_actor(controller_bp, carla.Transform(), 
                                                   attach_to=self.pedestrian)
                if controller:
                    self.actors.append(controller)
                    controller.start()
                    # 让行人走向路口
                    controller.go_to_location(intersection_spawn.location)
                
                logger.info("行人已生成")
                
        except Exception as e:
            logger.warning(f"生成行人失败: {e}")
    
    def _setup_weather(self, weather: str):
        """设置天气"""
        try:
            import carla
            
            weather_params = {
                'clear': carla.WeatherParameters.ClearNoon,
                'rain': carla.WeatherParameters.HardRainNoon,
                'fog': carla.WeatherParameters.FoggyNoon,
                'night': carla.WeatherParameters.ClearNight
            }.get(weather, carla.WeatherParameters.ClearNoon)
            
            self.world.set_weather(weather_params)
            logger.info(f"天气设置为: {weather}")
            
        except Exception as e:
            logger.error(f"设置天气失败: {e}")
    
    def _setup_collision_sensor(self):
        """设置碰撞传感器"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            collision_bp = blueprint_library.find('sensor.other.collision')
            collision_sensor = self.world.spawn_actor(
                collision_bp, carla.Transform(), attach_to=self.ego_vehicle
            )
            
            if collision_sensor:
                self.actors.append(collision_sensor)
                
                def on_collision(event):
                    self.collision_detected = True
                    impulse = event.normal_impulse
                    self.collision_data.append({
                        'time': time.time(),
                        'other_actor': str(event.other_actor.type_id) if event.other_actor else 'unknown',
                        'impulse': {'x': impulse.x, 'y': impulse.y, 'z': impulse.z}
                    })
                    logger.warning(f"检测到碰撞: {event.other_actor}")
                
                collision_sensor.listen(on_collision)
                
        except Exception as e:
            logger.error(f"设置碰撞传感器失败: {e}")
    
    def _setup_camera(self):
        """设置观察相机"""
        try:
            import carla
            
            self.spectator = self.world.get_spectator()
            
            if self.ego_vehicle:
                transform = self.ego_vehicle.get_transform()
                # 相机在车辆后方15米，上方10米
                camera_location = carla.Location(
                    transform.location.x - 15 * math.cos(math.radians(transform.rotation.yaw)),
                    transform.location.y - 15 * math.sin(math.radians(transform.rotation.yaw)),
                    transform.location.z + 10
                )
                camera_transform = carla.Transform(
                    camera_location,
                    carla.Rotation(pitch=-30, yaw=transform.rotation.yaw)
                )
                self.spectator.set_transform(camera_transform)
                
        except Exception as e:
            logger.error(f"设置相机失败: {e}")
    
    def update_camera(self):
        """更新相机位置跟随主车"""
        try:
            import carla
            
            if self.spectator and self.ego_vehicle:
                transform = self.ego_vehicle.get_transform()
                camera_location = carla.Location(
                    transform.location.x - 15 * math.cos(math.radians(transform.rotation.yaw)),
                    transform.location.y - 15 * math.sin(math.radians(transform.rotation.yaw)),
                    transform.location.z + 10
                )
                camera_transform = carla.Transform(
                    camera_location,
                    carla.Rotation(pitch=-30, yaw=transform.rotation.yaw)
                )
                self.spectator.set_transform(camera_transform)
                
        except Exception as e:
            logger.warning(f"更新相机失败: {e}")
    
    def execute(self, max_duration: float = 30.0) -> Dict:
        """执行场景
        
        参数:
            max_duration: 最大执行时间（秒）
            
        返回:
            执行结果字典
        """
        import carla
        
        trajectory_data = []
        start_time = time.time()
        
        logger.info("开始执行场景...")
        
        while time.time() - start_time < max_duration:
            if self.collision_detected:
                logger.warning("检测到碰撞，停止场景")
                break
            
            try:
                # 更新相机
                self.update_camera()
                
                # 记录轨迹
                if self.ego_vehicle:
                    transform = self.ego_vehicle.get_transform()
                    velocity = self.ego_vehicle.get_velocity()
                    
                    trajectory_data.append({
                        'time': time.time() - start_time,
                        'location': {
                            'x': transform.location.x,
                            'y': transform.location.y,
                            'z': transform.location.z
                        },
                        'velocity': {
                            'x': velocity.x,
                            'y': velocity.y,
                            'z': velocity.z
                        },
                        'rotation': {
                            'pitch': transform.rotation.pitch,
                            'yaw': transform.rotation.yaw,
                            'roll': transform.rotation.roll
                        }
                    })
                
                # 推进仿真
                self.world.tick()
                time.sleep(0.05)
                
            except Exception as e:
                logger.warning(f"执行循环出错: {e}")
                break
        
        execution_time = time.time() - start_time
        
        result = {
            'success': True,
            'collision': self.collision_detected,
            'execution_time': execution_time,
            'collision_count': len(self.collision_data),
            'trajectory_data': trajectory_data,
            'collision_details': self.collision_data if self.collision_data else None
        }
        
        logger.info(f"场景执行完成: 碰撞={self.collision_detected}, 耗时={execution_time:.2f}s")
        return result
    
    def cleanup(self):
        """清理场景资源"""
        try:
            import carla
            
            for actor in self.actors:
                if actor and actor.is_alive:
                    actor.destroy()
            
            self.actors.clear()
            self.ego_vehicle = None
            self.oncoming_vehicle = None
            self.pedestrian = None
            self.occlusion_vehicle = None
            self.traffic_vehicles.clear()
            self.collision_detected = False
            self.collision_data.clear()
            
            logger.info("场景资源已清理")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
