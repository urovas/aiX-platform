#!/usr/bin/env python3
"""
LLM驱动的无保护左转场景执行器
使用Qwen-72B生成控制逻辑，在CARLA中执行
"""

import math
import time
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('LLMScenarioExecutor')


class LLMScenarioExecutor:
    """LLM驱动的场景执行器"""
    
    def __init__(self, world, client, llm_client=None):
        """初始化执行器
        
        参数:
            world: CARLA世界对象
            client: CARLA客户端对象
            llm_client: LLM客户端
        """
        self.world = world
        self.client = client
        self.llm_client = llm_client
        
        self.ego_vehicle = None
        self.oncoming_vehicle = None
        self.actors = []
        self.collision_detected = False
        self.collision_data = []
        self.spectator = None
        
        self.control_logic = None
        self.trajectory_data = []
        
        self.left_turn_started = False
        self.left_turn_in_progress = False
        self.target_yaw = None
        self.turn_start_yaw = None
        
    def setup_scenario(self, params: Dict) -> bool:
        """设置场景
        
        参数:
            params: 场景参数
            
        返回:
            是否成功
        """
        try:
            import carla
            
            logger.info("设置无保护左转场景...")
            
            # 1. 使用LLM生成控制逻辑
            if self.llm_client:
                logger.info("调用LLM生成控制逻辑...")
                result = self.llm_client.generate_vehicle_control_logic(params)
                if result['success']:
                    self.control_logic = result['logic']
                    logger.info(f"控制逻辑生成成功: {len(self.control_logic.get('phases', []))} 个阶段")
                else:
                    logger.warning(f"LLM生成失败，使用默认逻辑: {result.get('error')}")
                    self.control_logic = self._get_default_control_logic(params)
            else:
                self.control_logic = self._get_default_control_logic(params)
            
            # 2. 设置天气
            self._setup_weather(params.get('weather', 'clear'))
            
            # 3. 获取生成点
            carla_map = self.world.get_map()
            spawn_points = carla_map.get_spawn_points()
            
            if len(spawn_points) < 2:
                logger.error("生成点不足")
                return False
            
            # 使用第一个生成点作为路口
            intersection_spawn = spawn_points[0]
            intersection_yaw = intersection_spawn.rotation.yaw
            
            # 4. 生成主车
            ego_success = self._spawn_ego_vehicle(intersection_spawn, params)
            if not ego_success:
                return False
            
            # 5. 生成对向来车
            self._spawn_oncoming_vehicle(intersection_spawn, params)
            
            # 6. 生成额外元素
            if params.get('occlusion'):
                self._spawn_occlusion_vehicle(intersection_spawn)
            
            if params.get('traffic_flow') == 'high':
                self._spawn_traffic_vehicles(intersection_spawn, params)
            
            if params.get('has_pedestrian'):
                self._spawn_pedestrian(intersection_spawn)
            
            # 7. 设置相机
            self._setup_camera()
            
            logger.info("场景设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置场景失败: {e}")
            return False
    
    def _get_default_control_logic(self, params: Dict) -> Dict:
        """获取默认控制逻辑
        
        参数:
            params: 场景参数
            
        返回:
            控制逻辑字典
        """
        ego_speed = params.get('ego_speed', 15)
        time_gap = params.get('time_gap', 4)
        
        return {
            "phases": [
                {
                    "name": "接近路口",
                    "trigger": "距离路口 > 30米",
                    "actions": ["保持速度", "观察路况"],
                    "duration": 2.0
                },
                {
                    "name": "减速观察",
                    "trigger": "距离路口 10-30米",
                    "actions": ["减速至5km/h", "观察对向来车", "计算安全间隙"],
                    "duration": 2.0
                },
                {
                    "name": "决策点",
                    "trigger": "距离路口 < 10米",
                    "actions": ["判断是否可以左转"],
                    "duration": 0.5
                },
                {
                    "name": "执行左转或等待",
                    "trigger": "决策完成",
                    "actions": ["如果安全则左转", "否则停车等待"],
                    "duration": 5.0
                }
            ],
            "decision_points": [
                {
                    "location": "路口入口",
                    "condition": "对向来车到达时间 > 时间间隙",
                    "if_true": "开始左转",
                    "if_false": "停车等待"
                }
            ],
            "safety_rules": [
                "对向来车到达时间必须大于时间间隙",
                "左转时保持速度不超过20km/h",
                "发现碰撞风险立即制动"
            ],
            "parameters": {
                "safe_time_gap": time_gap,
                "turn_speed": min(ego_speed * 0.5, 15),
                "approach_speed": ego_speed,
                "wait_speed": 0
            }
        }
    
    def _spawn_ego_vehicle(self, intersection_spawn, params: Dict) -> bool:
        """生成主车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            ego_bp = blueprint_library.filter('vehicle.tesla.model3')[0]
            ego_bp.set_attribute('role_name', 'ego')
            
            intersection_yaw = intersection_spawn.rotation.yaw
            ego_speed = params.get('ego_speed', 15)
            
            spawn_location = carla.Location(
                intersection_spawn.location.x - 50 * math.cos(math.radians(intersection_yaw)),
                intersection_spawn.location.y - 50 * math.sin(math.radians(intersection_yaw)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location, carla.Rotation(yaw=intersection_yaw))
            
            self.ego_vehicle = self.world.spawn_actor(ego_bp, spawn_transform)
            if not self.ego_vehicle:
                return False
            
            self.actors.append(self.ego_vehicle)
            
            speed_mps = ego_speed / 3.6
            yaw_rad = math.radians(intersection_yaw)
            velocity = carla.Vector3D(
                speed_mps * math.cos(yaw_rad),
                speed_mps * math.sin(yaw_rad),
                0
            )
            self.ego_vehicle.set_target_velocity(velocity)
            
            self._setup_collision_sensor()
            
            logger.info(f"主车已生成，初始速度: {ego_speed}km/h")
            return True
            
        except Exception as e:
            logger.error(f"生成主车失败: {e}")
            return False
    
    def _spawn_oncoming_vehicle(self, intersection_spawn, params: Dict):
        """生成对向来车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            vehicle_type = params.get('oncoming_vehicle_type', 'sedan')
            if vehicle_type == 'truck':
                vehicle_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
            elif vehicle_type == 'bus':
                vehicle_bp = blueprint_library.filter('vehicle.volkswagen.t2')[0]
            else:
                vehicle_bp = blueprint_library.filter('vehicle.audi.a2')[0]
            
            intersection_yaw = intersection_spawn.rotation.yaw
            oncoming_speed = params.get('oncoming_speed', 50)
            time_gap = params.get('time_gap', 4)
            
            oncoming_yaw = intersection_yaw + 90
            distance = oncoming_speed * time_gap / 3.6 + 20  # 增加20米缓冲距离
            
            spawn_location = carla.Location(
                intersection_spawn.location.x + distance * math.cos(math.radians(oncoming_yaw)),
                intersection_spawn.location.y + distance * math.sin(math.radians(oncoming_yaw)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location, carla.Rotation(yaw=oncoming_yaw - 180))
            
            self.oncoming_vehicle = self.world.spawn_actor(vehicle_bp, spawn_transform)
            if self.oncoming_vehicle:
                self.actors.append(self.oncoming_vehicle)
                
                speed_mps = oncoming_speed / 3.6
                yaw_rad = math.radians(oncoming_yaw - 180)
                velocity = carla.Vector3D(
                    speed_mps * math.cos(yaw_rad),
                    speed_mps * math.sin(yaw_rad),
                    0
                )
                self.oncoming_vehicle.set_target_velocity(velocity)
                
                logger.info(f"对向来车已生成，距离: {distance:.1f}m, 速度: {oncoming_speed}km/h")
                
        except Exception as e:
            logger.warning(f"生成对向来车失败: {e}")
    
    def _spawn_occlusion_vehicle(self, intersection_spawn):
        """生成遮挡车辆"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            truck_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
            
            intersection_yaw = intersection_spawn.rotation.yaw
            spawn_location = carla.Location(
                intersection_spawn.location.x - 30 * math.cos(math.radians(intersection_yaw))
                + 5 * math.cos(math.radians(intersection_yaw - 90)),
                intersection_spawn.location.y - 30 * math.sin(math.radians(intersection_yaw))
                + 5 * math.sin(math.radians(intersection_yaw - 90)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location, carla.Rotation(yaw=intersection_yaw))
            
            vehicle = self.world.spawn_actor(truck_bp, spawn_transform)
            if vehicle:
                self.actors.append(vehicle)
                logger.info("遮挡车辆已生成")
                
        except Exception as e:
            logger.warning(f"生成遮挡车辆失败: {e}")
    
    def _spawn_traffic_vehicles(self, intersection_spawn, params: Dict):
        """生成交通流车辆"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            intersection_yaw = intersection_spawn.rotation.yaw
            
            for i in range(2):
                vehicle_bp = blueprint_library.filter('vehicle.audi.a2')[0]
                spawn_location = carla.Location(
                    intersection_spawn.location.x - (80 + i * 30) * math.cos(math.radians(intersection_yaw)),
                    intersection_spawn.location.y - (80 + i * 30) * math.sin(math.radians(intersection_yaw)),
                    intersection_spawn.location.z + 0.5
                )
                spawn_transform = carla.Transform(spawn_location, carla.Rotation(yaw=intersection_yaw))
                
                vehicle = self.world.spawn_actor(vehicle_bp, spawn_transform)
                if vehicle:
                    self.actors.append(vehicle)
                    velocity = carla.Vector3D(
                        10 * math.cos(math.radians(intersection_yaw)),
                        10 * math.sin(math.radians(intersection_yaw)),
                        0
                    )
                    vehicle.set_target_velocity(velocity)
            
            logger.info("交通流车辆已生成")
            
        except Exception as e:
            logger.warning(f"生成交通流失败: {e}")
    
    def _spawn_pedestrian(self, intersection_spawn):
        """生成行人"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            pedestrian_bp = blueprint_library.filter('walker.pedestrian.*')[0]
            
            intersection_yaw = intersection_spawn.rotation.yaw
            spawn_location = carla.Location(
                intersection_spawn.location.x + 10 * math.cos(math.radians(intersection_yaw)),
                intersection_spawn.location.y + 10 * math.sin(math.radians(intersection_yaw)),
                intersection_spawn.location.z + 0.5
            )
            spawn_transform = carla.Transform(spawn_location)
            
            pedestrian = self.world.spawn_actor(pedestrian_bp, spawn_transform)
            if pedestrian:
                self.actors.append(pedestrian)
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
        """设置相机"""
        try:
            import carla
            
            self.spectator = self.world.get_spectator()
            
            if self.ego_vehicle:
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
            logger.error(f"设置相机失败: {e}")
    
    def _update_camera(self):
        """更新相机位置"""
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
    
    def _get_distance_to_intersection(self, intersection_location) -> float:
        """获取到路口的距离"""
        if self.ego_vehicle:
            ego_location = self.ego_vehicle.get_location()
            distance = math.sqrt(
                (ego_location.x - intersection_location.x) ** 2 +
                (ego_location.y - intersection_location.y) ** 2
            )
            return distance
        return float('inf')
    
    def _get_oncoming_vehicle_info(self, intersection_location) -> Dict:
        """获取对向来车信息"""
        if self.oncoming_vehicle:
            oncoming_location = self.oncoming_vehicle.get_location()
            oncoming_velocity = self.oncoming_vehicle.get_velocity()
            
            distance = math.sqrt(
                (oncoming_location.x - intersection_location.x) ** 2 +
                (oncoming_location.y - intersection_location.y) ** 2
            )
            
            speed = math.sqrt(oncoming_velocity.x ** 2 + oncoming_velocity.y ** 2)
            
            arrival_time = distance / speed if speed > 0 else float('inf')
            
            return {
                'distance': distance,
                'speed': speed * 3.6,
                'arrival_time': arrival_time
            }
        return {'distance': float('inf'), 'speed': 0, 'arrival_time': float('inf')}
    
    def execute(self, intersection_location, max_duration: float = 30.0) -> Dict:
        """执行场景 - 使用LLM生成的控制逻辑
        
        参数:
            intersection_location: 路口位置
            max_duration: 最大执行时间
            
        返回:
            执行结果
        """
        import carla
        
        start_time = time.time()
        phase_index = 0
        phase_start_time = start_time
        left_turn_started = False
        waiting = False
        
        logger.info("开始执行场景...")
        logger.info(f"控制逻辑: {json.dumps(self.control_logic, indent=2, ensure_ascii=False)}")
        
        while time.time() - start_time < max_duration:
            if self.collision_detected:
                logger.warning("检测到碰撞，停止执行")
                break
            
            current_time = time.time() - start_time
            
            try:
                ego_transform = self.ego_vehicle.get_transform()
                ego_velocity = self.ego_vehicle.get_velocity()
                ego_speed = math.sqrt(ego_velocity.x ** 2 + ego_velocity.y ** 2) * 3.6
                
                distance_to_intersection = self._get_distance_to_intersection(intersection_location)
                oncoming_info = self._get_oncoming_vehicle_info(intersection_location)
                
                self._update_camera()
                
                self.trajectory_data.append({
                    'time': current_time,
                    'location': {
                        'x': ego_transform.location.x,
                        'y': ego_transform.location.y,
                        'z': ego_transform.location.z
                    },
                    'velocity': {
                        'x': ego_velocity.x,
                        'y': ego_velocity.y,
                        'z': ego_velocity.z
                    },
                    'speed_kmh': ego_speed,
                    'rotation': {
                        'pitch': ego_transform.rotation.pitch,
                        'yaw': ego_transform.rotation.yaw,
                        'roll': ego_transform.rotation.roll
                    },
                    'distance_to_intersection': distance_to_intersection,
                    'oncoming_vehicle': oncoming_info
                })
                
                params = self.control_logic.get('parameters', {})
                safe_time_gap = params.get('safe_time_gap', 4)
                turn_speed = params.get('turn_speed', 10)
                
                if distance_to_intersection > 30:
                    if ego_speed < params.get('approach_speed', 15):
                        self._accelerate(params.get('approach_speed', 15))
                
                elif 10 < distance_to_intersection <= 30:
                    if ego_speed > 10:
                        self._decelerate(10)
                    logger.debug(f"减速观察: 距离路口 {distance_to_intersection:.1f}m, "
                               f"对向来车到达时间 {oncoming_info['arrival_time']:.1f}s")
                
                elif distance_to_intersection <= 10:
                    if not left_turn_started:
                        if oncoming_info['arrival_time'] > safe_time_gap:
                            logger.info(f"安全间隙足够 ({oncoming_info['arrival_time']:.1f}s > {safe_time_gap}s), 开始左转")
                            left_turn_started = True
                            self._start_left_turn(turn_speed)
                        elif not waiting:
                            logger.info(f"对向来车太近 ({oncoming_info['arrival_time']:.1f}s < {safe_time_gap}s), 停车等待")
                            waiting = True
                            self._stop_vehicle()
                
                if self.left_turn_started:
                    self._continue_left_turn()
                
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
            'trajectory_data': self.trajectory_data,
            'collision_details': self.collision_data if self.collision_data else None,
            'control_logic': self.control_logic,
            'left_turn_completed': left_turn_started and not self.collision_detected
        }
        
        logger.info(f"场景执行完成: 碰撞={self.collision_detected}, 耗时={execution_time:.2f}s, "
                   f"左转={'完成' if result['left_turn_completed'] else '未完成'}")
        return result
    
    def _accelerate(self, target_speed_kmh: float):
        """加速"""
        try:
            import carla
            
            if not self.ego_vehicle:
                return
            
            transform = self.ego_vehicle.get_transform()
            yaw_rad = math.radians(transform.rotation.yaw)
            speed_mps = target_speed_kmh / 3.6
            
            velocity = carla.Vector3D(
                speed_mps * math.cos(yaw_rad),
                speed_mps * math.sin(yaw_rad),
                0
            )
            self.ego_vehicle.set_target_velocity(velocity)
            
        except Exception as e:
            logger.warning(f"加速失败: {e}")
    
    def _decelerate(self, target_speed_kmh: float):
        """减速"""
        self._accelerate(target_speed_kmh)
    
    def _stop_vehicle(self):
        """停车"""
        try:
            import carla
            
            if self.ego_vehicle:
                velocity = carla.Vector3D(0, 0, 0)
                self.ego_vehicle.set_target_velocity(velocity)
                
        except Exception as e:
            logger.warning(f"停车失败: {e}")
    
    def _start_left_turn(self, turn_speed_kmh: float):
        """开始左转"""
        try:
            import carla
            
            if not self.ego_vehicle:
                return
            
            transform = self.ego_vehicle.get_transform()
            current_yaw = transform.rotation.yaw
            
            # 目标朝向：左转90度
            self.target_yaw = (current_yaw + 90) % 360
            self.turn_start_yaw = current_yaw
            self.left_turn_started = True
            self.left_turn_in_progress = True
            
            logger.info(f"开始左转，转弯速度: {turn_speed_kmh}km/h, 当前朝向: {current_yaw:.1f}°, 目标朝向: {self.target_yaw:.1f}°")
            
            # 设置转向速度
            self._accelerate(turn_speed_kmh)
            
        except Exception as e:
            logger.error(f"开始左转失败: {e}")
    
    def _continue_left_turn(self):
        """继续左转 - 调整朝向"""
        try:
            import carla
            
            if not self.ego_vehicle or not self.left_turn_in_progress:
                return
            
            transform = self.ego_vehicle.get_transform()
            current_yaw = transform.rotation.yaw
            current_location = transform.location
            
            # 计算到目标朝向的角度差
            yaw_diff = (self.target_yaw - current_yaw) % 360
            if yaw_diff > 180:
                yaw_diff -= 360
            
            # 如果角度差很小，认为左转完成
            if abs(yaw_diff) < 3:
                self.left_turn_in_progress = False
                logger.info(f"左转完成，当前朝向: {current_yaw:.1f}°")
                return
            
            # 计算转向速度（每帧调整的角度）
            # 使用更小的转向速度使转弯更平滑
            turn_rate = 1.0  # 每帧调整1度
            
            # 计算新的朝向
            if yaw_diff > 0:
                new_yaw = current_yaw + min(turn_rate, yaw_diff)
            else:
                new_yaw = current_yaw + max(-turn_rate, yaw_diff)
            
            # 计算新的位置（沿着当前朝向移动一点）
            move_distance = 0.5  # 每帧移动0.5米
            yaw_rad = math.radians(new_yaw)
            new_location = carla.Location(
                x=current_location.x + move_distance * math.cos(yaw_rad),
                y=current_location.y + move_distance * math.sin(yaw_rad),
                z=current_location.z
            )
            
            # 应用新的变换
            new_rotation = carla.Rotation(
                pitch=transform.rotation.pitch,
                yaw=new_yaw % 360,
                roll=transform.rotation.roll
            )
            new_transform = carla.Transform(new_location, new_rotation)
            self.ego_vehicle.set_transform(new_transform)
            
        except Exception as e:
            logger.warning(f"继续左转失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            import carla
            
            for actor in self.actors:
                if actor and actor.is_alive:
                    actor.destroy()
            
            self.actors.clear()
            self.ego_vehicle = None
            self.oncoming_vehicle = None
            self.collision_detected = False
            self.collision_data.clear()
            self.trajectory_data.clear()
            
            self.left_turn_started = False
            self.left_turn_in_progress = False
            self.target_yaw = None
            self.turn_start_yaw = None
            
            logger.info("资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
