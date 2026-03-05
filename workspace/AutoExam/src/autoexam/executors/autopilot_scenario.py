#!/usr/bin/env python3
"""
AutoExam - 终极版：十字路口横行道人潮 + 对向10人10非机动车 + 穿越对向车道
模拟真实城市路口最复杂的场景
"""

import math
import time
import logging
import random
from typing import Dict, Optional, Tuple, List
from enum import Enum

logger = logging.getLogger('AutoExam.UltimateLeftTurn')


class CrossingState(Enum):
    """行人过马路状态"""
    WAITING = "waiting"      # 等待
    CROSSING = "crossing"    # 正在过马路
    FINISHED = "finished"    # 已完成


class AutopilotScenario:
    """
    终极版无保护左转场景
    特点：
    - 十字路口4条人行横道上都有行人
    - 对向非机动车道密集的非机动车
    - 左转必须穿过对向车道才算完成
    - 不依赖Autopilot，使用自定义控制
    - 自动寻找地图中的十字路口
    """
    
    # 车辆类型映射
    VEHICLE_TYPES = {
        'sedan': 'vehicle.audi.a2',
        'suv': 'vehicle.tesla.model3',
        'truck': 'vehicle.carlamotors.carlacola',
        'bus': 'vehicle.volkswagen.t2',
        'police': 'vehicle.ford.police',
        'ambulance': 'vehicle.carlamotors.firetruck',
        'motorcycle': 'vehicle.yamaha.yzf',
        'bicycle': 'vehicle.diamondback.century'
    }
    
    # 行人类型
    PEDESTRIAN_TYPES = [
        'walker.pedestrian.0001',
        'walker.pedestrian.0002',
        'walker.pedestrian.0003',
        'walker.pedestrian.0004',
        'walker.pedestrian.0005',
        'walker.pedestrian.0006',
        'walker.pedestrian.0007',
        'walker.pedestrian.0008',
        'walker.pedestrian.0009',
        'walker.pedestrian.0010'
    ]
    
    # 非机动车类型
    BICYCLE_TYPES = [
        'vehicle.diamondback.century',
        'vehicle.gazelle.omafiets'
    ]
    
    # 摩托车类型
    MOTORCYCLE_TYPES = [
        'vehicle.yamaha.yzf',
        'vehicle.kawasaki.ninja',
        'vehicle.harley-davidson.low_rider'
    ]
    
    def __init__(self, world, client):
        """初始化场景"""
        self.world = world
        self.client = client
        
        # 车辆引用
        self.ego_vehicle = None
        self.oncoming_vehicle = None
        self.occlusion_vehicle = None
        self.traffic_vehicles = []
        
        # 非机动车
        self.bicycles = []
        self.motorcycles = []
        self.non_motor_vehicles = []  # 所有非机动车合并
        
        # 行人
        self.pedestrians = []
        self.pedestrian_controllers = []
        self.pedestrian_crossing_states = {}  # 记录每个行人的过马路状态
        
        # 路边停放的车辆
        self.parked_vehicles = []
        
        # 传感器
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.camera_sensor = None
        
        # 状态
        self.collision_detected = False
        self.collision_data = []
        self.lane_invasion_data = []
        self.trajectory_data = []
        
        # 场景参数
        self.junction = None
        self.ego_start_waypoint = None
        self.oncoming_start_waypoint = None
        self.left_target_waypoint = None
        self.left_target_lane = None  # 左转目标车道
        
        # 路口人行横道信息
        self.crosswalks = []  # 4条人行横道
        self.crosswalk_waypoints = []  # 每条人行横道上的waypoint
        
        # 对向车道信息
        self.opposite_lanes = []  # 对向车道
        
        # 控制相关
        self.ego_control = None
        self.oncoming_control = None
        self.last_tick = 0
        
        # 场景完成标志
        self.left_turn_completed = False
        self.reached_opposite_lane = False  # 是否已到达对向车道
        self.scenario_completed = False
        self.failure_reason = None
        
        # 所有生成的actor
        self.actors = []
        
        # 统计信息
        self.stats = {
            'vehicles': 0,
            'pedestrians': 0,
            'bicycles': 0,
            'motorcycles': 0,
            'parked_vehicles': 0
        }
    
    def setup_scenario(self, params: Dict) -> bool:
        """设置场景"""
        try:
            import carla
            
            # 设置随机种子
            random.seed(params.get('random_seed', 42))
            
            logger.info("=" * 70)
            logger.info("AutoExam - 终极版：十字路口横行道人潮 + 对向10人10非机动车")
            logger.info("=" * 70)
            
            # 加载地图
            map_name = params.get('map', 'Town05')
            if self.world.get_map().name.split('/')[-1] != map_name:
                logger.info(f"加载地图: {map_name}")
                self.world = self.client.load_world(map_name)
                time.sleep(2)
            
            # 设置天气
            weather_name = params.get('weather', 'clear')
            self._set_weather(weather_name)
            
            # 寻找合适的路口
            junction_info = self._find_suitable_intersection()
            if not junction_info:
                logger.error("未找到合适的路口")
                return False
            
            ego_spawn, oncoming_spawn, left_target = junction_info
            logger.info(f"找到路口: 主车={ego_spawn.location}, 对向={oncoming_spawn.location}")
            
            # 获取路口的人行横道信息
            self._find_crosswalks()
            
            # 获取对向车道信息
            self._find_opposite_lanes()
            
            # 生成主车
            if not self._spawn_ego_vehicle(ego_spawn, params):
                return False
            
            # 生成对向来车（用于博弈）
            self._spawn_oncoming_vehicle(oncoming_spawn, params)
            
            # 生成遮挡车辆（可选）
            if params.get('occlusion', False):
                self._spawn_occlusion_vehicle(ego_spawn, oncoming_spawn)
            
            # 生成交通流
            self._spawn_traffic_flow(ego_spawn, oncoming_spawn, 'medium')
            
            # 生成对向非机动车（10辆）
            logger.info("生成对向非机动车（10辆）...")
            self._spawn_opposite_non_motor_vehicles(oncoming_spawn, 10)
            
            # 生成十字路口人行横道上的行人（10人）
            logger.info("生成十字路口人行横道上的行人（10人）...")
            self._spawn_crosswalk_pedestrians(10)
            
            # 生成路边停放的车辆（增加复杂度）
            self._spawn_parked_vehicles(ego_spawn, oncoming_spawn, 'medium')
            
            # 设置传感器
            self._setup_sensors()
            
            # 设置观察视角
            self._setup_spectator()
            
            # 打印统计信息
            logger.info("=" * 70)
            logger.info("场景生成统计:")
            logger.info(f"  主车: 1")
            logger.info(f"  对向来车: {1 if self.oncoming_vehicle else 0}")
            logger.info(f"  交通流车辆: {len(self.traffic_vehicles)}")
            logger.info(f"  对向非机动车: {len(self.non_motor_vehicles)}")
            logger.info(f"  行人: {len(self.pedestrians)}")
            logger.info(f"  路边停车: {len(self.parked_vehicles)}")
            logger.info(f"  总Actor数: {len(self.actors)}")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"设置场景失败: {e}", exc_info=True)
            return False
    
    def _find_suitable_intersection(self) -> Optional[Tuple]:
        """在地图中寻找合适的十字路口"""
        import carla
        
        carla_map = self.world.get_map()
        
        # 获取所有路口
        junctions = []
        for waypoint in carla_map.generate_waypoints(2.0):
            if waypoint.is_junction and waypoint.get_junction():
                junction = waypoint.get_junction()
                if junction not in junctions:
                    junctions.append(junction)
        
        if not junctions:
            logger.error("地图中没有路口")
            return None
        
        # 选择最大的路口
        target_junction = max(junctions, key=lambda j: len(j.get_waypoints(carla.LaneType.Driving)))
        self.junction = target_junction
        
        # 获取路口的车道信息
        junction_ways = target_junction.get_waypoints(carla.LaneType.Driving)
        
        # 寻找适合左转的车道组合
        for entry_waypoint, exit_waypoint in junction_ways:
            if entry_waypoint.lane_type == carla.LaneType.Driving:
                # 寻找对向车道
                opposite_waypoint = None
                for wp in entry_waypoint.next(1):
                    yaw_diff = abs(wp.transform.rotation.yaw - entry_waypoint.transform.rotation.yaw)
                    if yaw_diff > 170:
                        opposite_waypoint = wp
                        break
                
                if opposite_waypoint and opposite_waypoint.lane_type == carla.LaneType.Driving:
                    
                    # 检查是否可以左转
                    entry_yaw = entry_waypoint.transform.rotation.yaw
                    exit_yaw = exit_waypoint.transform.rotation.yaw
                    yaw_diff = abs(entry_yaw - exit_yaw)
                    if yaw_diff > 180:
                        yaw_diff = 360 - yaw_diff
                    
                    if 70 < yaw_diff < 110:
                        self.ego_start_waypoint = entry_waypoint
                        self.oncoming_start_waypoint = opposite_waypoint
                        self.left_target_waypoint = exit_waypoint
                        
                        # 记录左转目标车道
                        self.left_target_lane = exit_waypoint.lane_id
                        
                        # 生成具体位置
                        ego_location = entry_waypoint.transform.location
                        oncoming_location = opposite_waypoint.transform.location
                        
                        forward_vector = entry_waypoint.transform.get_forward_vector()
                        # 增加主车与路口的距离，避免碰撞
                        ego_start = carla.Transform(
                            carla.Location(
                                x=ego_location.x - forward_vector.x * 70,
                                y=ego_location.y - forward_vector.y * 70,
                                z=ego_location.z + 0.5
                            ),
                            entry_waypoint.transform.rotation
                        )
                        
                        # 增加对向车与路口的距离，避免碰撞
                        oncoming_start = carla.Transform(
                            carla.Location(
                                x=oncoming_location.x + forward_vector.x * 100,
                                y=oncoming_location.y + forward_vector.y * 100,
                                z=oncoming_location.z + 0.5
                            ),
                            opposite_waypoint.transform.rotation
                        )
                        
                        return (ego_start, oncoming_start, exit_waypoint.transform.location)
        
        logger.warning("未找到合适的左转路口，使用默认位置")
        entry_waypoint, exit_waypoint = junction_ways[0]
        return (
            entry_waypoint.transform,
            entry_waypoint.get_opposite().transform,
            exit_waypoint.transform.location
        )
    
    def _find_crosswalks(self):
        """寻找路口的人行横道"""
        import carla
        
        if not self.junction:
            return
        
        carla_map = self.world.get_map()
        junction_center = self.junction.bounding_box.location
        
        # 在路口周围寻找人行横道
        for distance in [10, 20, 30]:
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                x = junction_center.x + distance * math.cos(rad)
                y = junction_center.y + distance * math.sin(rad)
                
                location = carla.Location(x=x, y=y, z=junction_center.z)
                waypoint = carla_map.get_waypoint(location, project_to_road=False)
                
                if waypoint and waypoint.lane_type == carla.LaneType.Sidewalk:
                    self.crosswalks.append({
                        'location': location,
                        'angle': angle,
                        'waypoint': waypoint
                    })
        
        logger.info(f"找到 {len(self.crosswalks)} 条人行横道")
    
    def _find_opposite_lanes(self):
        """寻找对向车道"""
        import carla
        
        if not self.junction:
            return
        
        carla_map = self.world.get_map()
        
        # 在路口周围寻找对向车道
        junction_center = self.junction.bounding_box.location
        
        for waypoint in carla_map.generate_waypoints(5.0):
            if waypoint.transform.location.distance(junction_center) < 80:
                if waypoint.lane_id < 0:  # 对向车道通常lane_id为负
                    self.opposite_lanes.append(waypoint)
        
        logger.info(f"找到 {len(self.opposite_lanes)} 个对向车道点")
    
    def _spawn_ego_vehicle(self, spawn_point, params: Dict) -> bool:
        """生成主车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            vehicle_type = params.get('ego_vehicle_type', 'suv')
            bp_name = self.VEHICLE_TYPES.get(vehicle_type, self.VEHICLE_TYPES['suv'])
            ego_bp = blueprint_library.filter(bp_name)[0]
            ego_bp.set_attribute('role_name', 'hero')
            
            self.ego_vehicle = self.world.try_spawn_actor(ego_bp, spawn_point)
            if not self.ego_vehicle:
                for i in range(5):
                    offset = carla.Location(x=random.uniform(-2, 2), y=random.uniform(-2, 2))
                    spawn_point.location += offset
                    self.ego_vehicle = self.world.try_spawn_actor(ego_bp, spawn_point)
                    if self.ego_vehicle:
                        break
            
            if not self.ego_vehicle:
                logger.error("无法生成主车")
                return False
            
            self.actors.append(self.ego_vehicle)
            
            target_speed = params.get('ego_speed', 30) / 3.6
            self.ego_vehicle.set_target_velocity(
                spawn_point.get_forward_vector() * target_speed
            )
            
            self.ego_control = carla.VehicleControl()
            self.ego_control.throttle = 0.5
            
            logger.info(f"主车已生成, 初始速度: {params.get('ego_speed', 30)}km/h")
            return True
            
        except Exception as e:
            logger.error(f"生成主车失败: {e}")
            return False
    
    def _spawn_oncoming_vehicle(self, spawn_point, params: Dict):
        """生成对向来车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            vehicle_type = params.get('oncoming_vehicle_type', 'sedan')
            bp_name = self.VEHICLE_TYPES.get(vehicle_type, self.VEHICLE_TYPES['sedan'])
            vehicle_bp = blueprint_library.filter(bp_name)[0]
            
            self.oncoming_vehicle = self.world.try_spawn_actor(vehicle_bp, spawn_point)
            if not self.oncoming_vehicle:
                for i in range(3):
                    offset = carla.Location(x=random.uniform(-2, 2), y=random.uniform(-2, 2))
                    spawn_point.location += offset
                    self.oncoming_vehicle = self.world.try_spawn_actor(vehicle_bp, spawn_point)
                    if self.oncoming_vehicle:
                        break
            
            if self.oncoming_vehicle:
                self.actors.append(self.oncoming_vehicle)
                
                target_speed = params.get('oncoming_speed', 40) / 3.6
                forward_vector = spawn_point.get_forward_vector()
                direction = carla.Vector3D(-forward_vector.x, -forward_vector.y, -forward_vector.z)
                self.oncoming_vehicle.set_target_velocity(direction * target_speed)
                
                self.oncoming_control = carla.VehicleControl()
                self.oncoming_control.throttle = 0.5
                
                logger.info(f"对向来车已生成, 速度: {params.get('oncoming_speed', 40)}km/h")
                
        except Exception as e:
            logger.warning(f"生成对向来车失败: {e}")
    
    def _spawn_occlusion_vehicle(self, ego_spawn, oncoming_spawn):
        """生成遮挡车辆"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            truck_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
            
            direction = (self.junction.bounding_box.location - ego_spawn.location).make_unit_vector()
            occlusion_location = ego_spawn.location + direction * 40
            
            waypoint = self.world.get_map().get_waypoint(occlusion_location)
            if waypoint:
                occlusion_transform = carla.Transform(
                    waypoint.transform.location + carla.Location(z=0.5),
                    ego_spawn.rotation
                )
                
                self.occlusion_vehicle = self.world.try_spawn_actor(truck_bp, occlusion_transform)
                if self.occlusion_vehicle:
                    self.actors.append(self.occlusion_vehicle)
                    self.occlusion_vehicle.set_target_velocity(carla.Vector3D())
                    self.occlusion_vehicle.set_autopilot(False)
                    
        except Exception as e:
            logger.warning(f"生成遮挡车辆失败: {e}")
    
    def _spawn_traffic_flow(self, ego_spawn, oncoming_spawn, density: str):
        """生成交通流"""
        try:
            import carla
            
            # 减少交通流车辆数量，避免碰撞
            densities = {'none': 0, 'low': 1, 'medium': 2, 'high': 3, 'extreme': 4}
            num_vehicles = densities.get(density, 1)
            
            blueprint_library = self.world.get_blueprint_library()
            
            # 在主车后方生成
            for i in range(num_vehicles):
                try:
                    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
                    if vehicle_bp.get_attribute('number_of_wheels').as_int() != 4:
                        continue
                    
                    # 增加间距，避免碰撞
                    distance = 40 + i * 20 + random.uniform(-5, 5)
                    location = ego_spawn.location - ego_spawn.get_forward_vector() * distance
                    
                    waypoint = self.world.get_map().get_waypoint(location)
                    if waypoint and waypoint.lane_type == carla.LaneType.Driving:
                        transform = carla.Transform(
                            waypoint.transform.location + carla.Location(z=0.5),
                            ego_spawn.rotation
                        )
                        
                        vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
                        if vehicle:
                            self.traffic_vehicles.append(vehicle)
                            self.actors.append(vehicle)
                            # 设置较低的速度
                            vehicle.set_autopilot(True)
                            
                except Exception:
                    continue
            
            logger.info(f"已生成 {len(self.traffic_vehicles)} 辆交通流车辆")
            
        except Exception as e:
            logger.warning(f"生成交通流失败: {e}")
    
    def _spawn_opposite_non_motor_vehicles(self, oncoming_spawn, count: int):
        """
        生成对向非机动车（自行车/摩托车）
        确保它们在对向车道行驶
        """
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            junction_center = self.junction.bounding_box.location
            
            # 生成非机动车
            spawned = 0
            attempts = 0
            max_attempts = count * 3
            
            while spawned < count and attempts < max_attempts:
                try:
                    # 交替生成自行车和摩托车
                    if spawned % 3 == 0:
                        bp_type = random.choice(self.MOTORCYCLE_TYPES)
                        speed = random.uniform(3, 8)
                    else:
                        bp_type = random.choice(self.BICYCLE_TYPES)
                        speed = random.uniform(2, 4)
                    
                    vehicle_bp = blueprint_library.filter(bp_type)[0]
                    
                    # 在对向车道上生成
                    if self.opposite_lanes:
                        # 选择对向车道上的点
                        base_wp = random.choice(self.opposite_lanes)
                        
                        # 沿着车道移动，分散生成
                        offset = spawned * 10 + random.uniform(-3, 3)
                        wp_list = base_wp.next(offset)
                        
                        if wp_list:
                            wp = wp_list[0]
                            
                            # 确保在路口附近
                            if wp.transform.location.distance(junction_center) < 80:
                                transform = carla.Transform(
                                    wp.transform.location + carla.Location(z=0.5),
                                    wp.transform.rotation
                                )
                                
                                vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
                                if vehicle:
                                    self.non_motor_vehicles.append(vehicle)
                                    self.actors.append(vehicle)
                                    
                                    # 设置速度
                                    vehicle.set_target_velocity(
                                        wp.transform.get_forward_vector() * speed
                                    )
                                    vehicle.set_autopilot(True)
                                    spawned += 1
                    
                except Exception as e:
                    pass
                finally:
                    attempts += 1
            
            logger.info(f"已生成 {len(self.non_motor_vehicles)} 辆对向非机动车")
            
        except Exception as e:
            logger.warning(f"生成非机动车失败: {e}")
    
    def _spawn_crosswalk_pedestrians(self, count: int):
        """
        在十字路口人行横道上生成行人
        让他们持续过马路
        """
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            junction_center = self.junction.bounding_box.location
            
            # 直接在路口四个方向生成行人，不依赖人行横道检测
            directions = [0, 90, 180, 270]  # 四个方向
            spawned = 0
            attempts = 0
            max_attempts = count * 2
            
            while spawned < count and attempts < max_attempts:
                try:
                    pedestrian_bp = blueprint_library.filter(random.choice(self.PEDESTRIAN_TYPES))[0]
                    
                    # 随机选择一个方向
                    direction = random.choice(directions)
                    angle_rad = math.radians(direction)
                    
                    # 随机选择起点位置（路口附近）
                    offset = random.uniform(5, 20)
                    spawn_location = carla.Location(
                        x=junction_center.x + offset * math.cos(angle_rad),
                        y=junction_center.y + offset * math.sin(angle_rad),
                        z=junction_center.z + 0.5
                    )
                    
                    # 生成行人
                    transform = carla.Transform(spawn_location)
                    pedestrian = self.world.try_spawn_actor(pedestrian_bp, transform)
                    if pedestrian:
                        self.pedestrians.append(pedestrian)
                        self.actors.append(pedestrian)
                        
                        # 添加控制器
                        controller_bp = blueprint_library.find('controller.ai.walker')
                        controller = self.world.try_spawn_actor(
                            controller_bp, 
                            carla.Transform(), 
                            attach_to=pedestrian
                        )
                        
                        if controller:
                            self.pedestrian_controllers.append(controller)
                            self.actors.append(controller)
                            controller.start()
                            
                            # 设置过马路的目标点（对面）
                            dest_location = carla.Location(
                                x=junction_center.x - offset * math.cos(angle_rad),
                                y=junction_center.y - offset * math.sin(angle_rad),
                                z=junction_center.z
                            )
                            
                            controller.go_to_location(dest_location)
                            controller.set_max_speed(random.uniform(1.0, 1.8))
                            
                            # 记录初始状态
                            self.pedestrian_crossing_states[pedestrian.id] = {
                                'state': CrossingState.CROSSING,
                                'start_time': time.time(),
                                'destination': dest_location
                            }
                            
                            spawned += 1
                    
                except Exception as e:
                    pass
                finally:
                    attempts += 1
            
            logger.info(f"已生成 {len(self.pedestrians)} 个过马路的行人")
            
        except Exception as e:
            logger.warning(f"生成行人失败: {e}")
    
    def _spawn_parked_vehicles(self, ego_spawn, oncoming_spawn, density: str):
        """生成路边停放的车辆"""
        try:
            import carla
            
            densities = {'none': 0, 'low': 2, 'medium': 4, 'high': 8, 'extreme': 12}
            num_parked = densities.get(density, 4)
            
            blueprint_library = self.world.get_blueprint_library()
            
            for i in range(num_parked):
                try:
                    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
                    if vehicle_bp.get_attribute('number_of_wheels').as_int() != 4:
                        continue
                    
                    offset = random.uniform(-40, 40)
                    spawn_location = carla.Location(
                        x=ego_spawn.location.x + offset,
                        y=ego_spawn.location.y + offset,
                        z=ego_spawn.location.z
                    )
                    
                    waypoint = self.world.get_map().get_waypoint(spawn_location)
                    if waypoint:
                        right_vector = waypoint.transform.get_right_vector()
                        parked_location = waypoint.transform.location + right_vector * 3.0
                        
                        transform = carla.Transform(
                            parked_location + carla.Location(z=0.5),
                            waypoint.transform.rotation
                        )
                        
                        vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
                        if vehicle:
                            self.parked_vehicles.append(vehicle)
                            self.actors.append(vehicle)
                            vehicle.set_target_velocity(carla.Vector3D())
                            vehicle.set_autopilot(False)
                            
                except Exception:
                    continue
            
            logger.info(f"已生成 {len(self.parked_vehicles)} 辆路边停车")
            
        except Exception as e:
            logger.warning(f"生成路边停车失败: {e}")
    
    def _set_weather(self, weather_name: str):
        """设置天气"""
        try:
            import carla
            
            weather_presets = {
                'clear': carla.WeatherParameters.ClearNoon,
                'rain': carla.WeatherParameters.HardRainNoon,
                'fog': carla.WeatherParameters.SoftRainSunset,
                'night': carla.WeatherParameters.ClearNight
            }
            
            weather = weather_presets.get(weather_name, carla.WeatherParameters.ClearNoon)
            self.world.set_weather(weather)
            logger.info(f"天气设置为: {weather_name}")
            
        except Exception as e:
            logger.error(f"设置天气失败: {e}")
    
    def _setup_sensors(self):
        """设置传感器"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            # 碰撞传感器
            collision_bp = blueprint_library.find('sensor.other.collision')
            self.collision_sensor = self.world.spawn_actor(
                collision_bp, 
                carla.Transform(), 
                attach_to=self.ego_vehicle
            )
            
            if self.collision_sensor:
                self.actors.append(self.collision_sensor)
                
                def on_collision(event):
                    self.collision_detected = True
                    impulse = event.normal_impulse
                    impulse_magnitude = math.sqrt(impulse.x**2 + impulse.y**2 + impulse.z**2)
                    
                    other_id = 'unknown'
                    if event.other_actor:
                        other_id = f"{event.other_actor.type_id}"
                        if 'walker' in other_id:
                            other_id = 'pedestrian'
                        elif 'vehicle' in other_id:
                            other_id = 'vehicle'
                    
                    self.collision_data.append({
                        'time': time.time(),
                        'other_actor': other_id,
                        'impulse': impulse_magnitude,
                        'location': {
                            'x': event.transform.location.x,
                            'y': event.transform.location.y,
                            'z': event.transform.location.z
                        }
                    })
                    
                    logger.warning(f"碰撞检测: 与 {other_id}, 冲量={impulse_magnitude:.2f}")
                
                self.collision_sensor.listen(on_collision)
            
            # 车道入侵传感器
            lane_bp = blueprint_library.find('sensor.other.lane_invasion')
            self.lane_invasion_sensor = self.world.spawn_actor(
                lane_bp,
                carla.Transform(),
                attach_to=self.ego_vehicle
            )
            
            if self.lane_invasion_sensor:
                self.actors.append(self.lane_invasion_sensor)
                
                def on_lane_invasion(event):
                    self.lane_invasion_data.append({
                        'time': time.time(),
                        'lane_types': [str(lt) for lt in event.crossed_lane_markings]
                    })
                
                self.lane_invasion_sensor.listen(on_lane_invasion)
                
        except Exception as e:
            logger.error(f"设置传感器失败: {e}")
    
    def _setup_spectator(self):
        """设置观察视角"""
        try:
            import carla
            
            self.spectator = self.world.get_spectator()
            
            if self.ego_vehicle and self.junction:
                junction_center = self.junction.bounding_box.location
                
                # 设置高空俯瞰视角，看到整个十字路口
                camera_location = carla.Location(
                    x=junction_center.x,
                    y=junction_center.y - 150,
                    z=100
                )
                
                camera_rotation = carla.Rotation(
                    pitch=-70,
                    yaw=90
                )
                
                self.spectator.set_transform(carla.Transform(camera_location, camera_rotation))
                logger.info("相机设置为高空俯瞰视角")
                
        except Exception as e:
            logger.error(f"设置相机失败: {e}")
    
    def _update_spectator(self):
        """更新观察视角"""
        try:
            import carla
            
            if self.spectator and self.junction:
                junction_center = self.junction.bounding_box.location
                
                # 固定在路口中心上空
                camera_location = carla.Location(
                    x=junction_center.x,
                    y=junction_center.y - 150,
                    z=100
                )
                
                self.spectator.set_transform(carla.Transform(
                    camera_location,
                    carla.Rotation(pitch=-70, yaw=90)
                ))
                
        except Exception as e:
            pass
    
    def _is_safe_to_turn(self) -> bool:
        """判断是否可以安全左转（考虑对向车和非机动车）"""
        if not self.oncoming_vehicle:
            # 即使没有对向车，也要考虑非机动车
            return self._is_safe_from_non_motor()
        
        ego_loc = self.ego_vehicle.get_location()
        oncoming_loc = self.oncoming_vehicle.get_location()
        junction_center = self.junction.bounding_box.location
        
        # 计算到路口的距离
        ego_to_junction = ego_loc.distance(junction_center)
        oncoming_to_junction = oncoming_loc.distance(junction_center)
        
        # 获取对向车速度
        oncoming_velocity = self.oncoming_vehicle.get_velocity()
        oncoming_speed = math.sqrt(
            oncoming_velocity.x**2 + 
            oncoming_velocity.y**2 + 
            oncoming_velocity.z**2
        )
        
        if oncoming_speed < 0.1:
            return self._is_safe_from_non_motor()
        
        # 估算到达路口的时间
        ego_speed = self._get_vehicle_speed(self.ego_vehicle)
        if ego_speed < 0.1:
            ego_speed = 3.0  # 更保守
        
        time_to_junction_ego = ego_to_junction / ego_speed
        time_to_junction_oncoming = oncoming_to_junction / oncoming_speed
        
        # 安全间隙
        base_gap = 5.0  # 更保守
        
        vehicle_safe = (time_to_junction_oncoming - time_to_junction_ego) > base_gap
        
        # 同时检查非机动车
        non_motor_safe = self._is_safe_from_non_motor()
        
        return vehicle_safe and non_motor_safe
    
    def _is_safe_from_non_motor(self) -> bool:
        """判断是否与对向非机动车安全"""
        if not self.non_motor_vehicles:
            return True
        
        ego_loc = self.ego_vehicle.get_location()
        junction_center = self.junction.bounding_box.location
        
        # 检查每个非机动车
        for vehicle in self.non_motor_vehicles:
            if not vehicle.is_alive:
                continue
            
            v_loc = vehicle.get_location()
            v_vel = vehicle.get_velocity()
            v_speed = math.sqrt(v_vel.x**2 + v_vel.y**2)
            
            # 计算到路口的距离
            v_to_junction = v_loc.distance(junction_center)
            ego_to_junction = ego_loc.distance(junction_center)
            
            # 如果非机动车在路口附近
            if v_to_junction < 40:  # 更大的检测范围
                # 估算到达路口的时间
                time_to_junction_v = v_to_junction / max(v_speed, 0.1)
                time_to_junction_ego = ego_to_junction / max(self._get_vehicle_speed(self.ego_vehicle), 0.1)
                
                # 如果时间差太小，不安全
                if abs(time_to_junction_v - time_to_junction_ego) < 3.0:  # 更保守的时间差
                    return False
        
        return True
    
    def _check_pedestrian_crossing(self) -> bool:
        """检查是否有行人在过马路"""
        if not self.pedestrians:
            return False
        
        ego_loc = self.ego_vehicle.get_location()
        junction_center = self.junction.bounding_box.location
        
        # 如果主车已经在路口，检查是否有行人在人行横道上
        if ego_loc.distance(junction_center) < 20:
            for pedestrian in self.pedestrians:
                if not pedestrian.is_alive:
                    continue
                
                ped_loc = pedestrian.get_location()
                
                # 如果行人在路口附近
                if ped_loc.distance(junction_center) < 30:
                    # 检查是否在人行横道上（简单判断）
                    for crosswalk in self.crosswalks[:4]:
                        if abs(ped_loc.distance(crosswalk['location'])) < 20:
                            return True
        
        return False
    
    def _get_vehicle_speed(self, vehicle) -> float:
        """获取车辆速度"""
        velocity = vehicle.get_velocity()
        return math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    
    def _check_reached_opposite_lane(self) -> bool:
        """
        检查是否已到达对向车道
        这是左转完成的真正标志
        """
        if not self.ego_vehicle or not self.left_target_lane:
            return False
        
        ego_loc = self.ego_vehicle.get_location()
        waypoint = self.world.get_map().get_waypoint(ego_loc)
        
        if waypoint:
            # 检查是否在目标车道上
            if waypoint.lane_id == self.left_target_lane:
                # 同时检查距离路口足够远
                if waypoint.transform.location.distance(self.junction.bounding_box.location) > 20:
                    return True
        
        return False
    
    def _control_ego_vehicle(self):
        """控制主车"""
        if not self.ego_vehicle or not self.ego_control:
            return
        
        import carla
        
        ego_loc = self.ego_vehicle.get_location()
        junction_center = self.junction.bounding_box.location
        
        # 到路口的距离
        distance_to_junction = ego_loc.distance(junction_center)
        
        # 获取当前速度
        current_speed = self._get_vehicle_speed(self.ego_vehicle)
        
        # 检查是否有行人在过马路
        pedestrian_crossing = self._check_pedestrian_crossing()
        
        # 阶段1: 接近路口
        if distance_to_junction > 40:
            # 保持速度
            target_speed = 3.0  # 进一步降低速度，更安全
            if current_speed < target_speed:
                self.ego_control.throttle = 0.2
            else:
                self.ego_control.throttle = 0.05
            self.ego_control.brake = 0.0
            self.ego_control.steer = 0.0
            
        # 阶段2: 到达路口，观察并决策
        elif distance_to_junction <= 40 and not self.left_turn_completed:
            # 减速观察
            if current_speed > 1.0:
                self.ego_control.throttle = 0.0
                self.ego_control.brake = 0.5
                self.ego_control.steer = 0.0
            else:
                self.ego_control.brake = 0.0
                
                # 判断是否安全（考虑对向车、非机动车和行人）
                if self._is_safe_to_turn() and not pedestrian_crossing:
                    # 安全，开始左转
                    self.ego_control.throttle = 0.15
                    self.ego_control.steer = 0.9  # 更大的转向角度
                    
                    # 检查是否已到达对向车道
                    if self._check_reached_opposite_lane():
                        self.left_turn_completed = True
                        self.reached_opposite_lane = True
                        logger.info("✅ 左转完成！已到达对向车道")
                else:
                    # 不安全，等待
                    self.ego_control.throttle = 0.0
                    self.ego_control.steer = 0.0
        
        # 阶段3: 左转完成，驶离
        else:
            target_speed = 2.0  # 进一步降低速度
            if current_speed < target_speed:
                self.ego_control.throttle = 0.1
            else:
                self.ego_control.throttle = 0.0
            self.ego_control.steer = 0.0
        
        # 应用控制
        self.ego_vehicle.apply_control(self.ego_control)
    
    def _control_oncoming_vehicle(self):
        """控制对向来车"""
        if not self.oncoming_vehicle or not self.oncoming_control:
            return
        
        self.oncoming_vehicle.apply_control(self.oncoming_control)
    
    def execute(self, max_duration: float = 60.0) -> Dict:
        """
        执行场景
        """
        import carla
        
        self.trajectory_data = []
        start_time = time.time()
        last_log_time = start_time
        
        logger.info("开始执行终极版无保护左转场景...")
        logger.info(f"目标: 穿过对向车道完成左转")
        
        try:
            while time.time() - start_time < max_duration:
                current_time = time.time()
                
                # 检查碰撞
                if self.collision_detected:
                    logger.warning("❌ 检测到碰撞，场景终止")
                    self.failure_reason = 'collision'
                    break
                
                # 获取主车状态
                if self.ego_vehicle:
                    transform = self.ego_vehicle.get_transform()
                    velocity = self.ego_vehicle.get_velocity()
                    speed = math.sqrt(velocity.x**2 + velocity.y**2) * 3.6
                    
                    # 记录轨迹
                    if current_time - last_log_time >= 1.0:
                        self.trajectory_data.append({
                            'time': current_time - start_time,
                            'location': {
                                'x': transform.location.x,
                                'y': transform.location.y,
                                'z': transform.location.z
                            },
                            'speed_kmh': speed,
                            'rotation': {
                                'pitch': transform.rotation.pitch,
                                'yaw': transform.rotation.yaw,
                                'roll': transform.rotation.roll
                            }
                        })
                        last_log_time = current_time
                        
                        # 每5秒打印一次状态
                        if int(current_time - start_time) % 5 == 0:
                            distance_to_opposite = self._check_reached_opposite_lane()
                            if not self.left_turn_completed:
                                logger.info(f"⏳ 正在左转... 距离路口: {transform.location.distance(self.junction.bounding_box.location):.1f}m")
                    
                    # 检查场景完成
                    if self.left_turn_completed:
                        # 再行驶一段距离确认
                        if self.left_target_waypoint:
                            distance = transform.location.distance(self.left_target_waypoint.transform.location)
                            if distance > 30:
                                self.scenario_completed = True
                                logger.info("✅ 场景成功完成！已驶离路口")
                                break
                
                # 控制车辆
                self._control_ego_vehicle()
                self._control_oncoming_vehicle()
                
                # 更新视角
                self._update_spectator()
                
                # 推进仿真
                self.world.tick()
                time.sleep(0.05)
                
        except Exception as e:
            logger.error(f"执行场景时出错: {e}", exc_info=True)
            self.failure_reason = 'exception'
        
        execution_time = time.time() - start_time
        
        # 构建结果
        collision_details = None
        if self.collision_data:
            collision_details = self.collision_data
        
        result = {
            'success': self.scenario_completed and not self.collision_detected,
            'collision': self.collision_detected,
            'collision_with': collision_details[0]['other_actor'] if collision_details else None,
            'left_turn_completed': self.left_turn_completed,
            'reached_opposite_lane': self.reached_opposite_lane,
            'scenario_completed': self.scenario_completed,
            'failure_reason': self.failure_reason,
            'execution_time': execution_time,
            'collision_count': len(self.collision_data),
            'collision_details': collision_details,
            'lane_invasion_count': len(self.lane_invasion_data),
            'trajectory_data': self.trajectory_data,
            'stats': {
                'vehicles': len(self.traffic_vehicles),
                'pedestrians': len(self.pedestrians),
                'non_motor_vehicles': len(self.non_motor_vehicles),
                'parked_vehicles': len(self.parked_vehicles),
                'total_actors': len(self.actors)
            }
        }
        
        # 添加速度统计
        if self.trajectory_data:
            speeds = [d['speed_kmh'] for d in self.trajectory_data]
            result['max_speed'] = max(speeds)
            result['avg_speed'] = sum(speeds) / len(speeds)
        else:
            result['max_speed'] = 0
            result['avg_speed'] = 0
        
        logger.info("=" * 70)
        logger.info("🏁 场景执行结果:")
        logger.info(f"  成功: {result['success']}")
        logger.info(f"  碰撞: {result['collision']}")
        if result['collision']:
            logger.info(f"  碰撞对象: {result['collision_with']}")
        logger.info(f"  左转完成: {result['left_turn_completed']}")
        logger.info(f"  到达对向车道: {result['reached_opposite_lane']}")
        logger.info(f"  耗时: {execution_time:.2f}秒")
        logger.info("  场景统计:")
        for k, v in result['stats'].items():
            logger.info(f"    {k}: {v}")
        logger.info("=" * 70)
        
        return result
    
    def cleanup(self):
        """清理资源"""
        try:
            import carla
            
            logger.info("清理场景资源...")
            
            # 停止所有行人控制器
            for controller in self.pedestrian_controllers:
                if controller and controller.is_alive:
                    try:
                        controller.stop()
                    except:
                        pass
            
            # 停止所有传感器
            for sensor in [self.collision_sensor, self.lane_invasion_sensor, self.camera_sensor]:
                if sensor and sensor.is_alive:
                    sensor.stop()
                    sensor.destroy()
            
            # 销毁所有actor
            for actor in self.actors:
                if actor and actor.is_alive:
                    try:
                        actor.destroy()
                    except:
                        pass
            
            # 清空列表
            self.actors.clear()
            self.traffic_vehicles.clear()
            self.pedestrians.clear()
            self.pedestrian_controllers.clear()
            self.bicycles.clear()
            self.motorcycles.clear()
            self.non_motor_vehicles.clear()
            self.parked_vehicles.clear()
            self.collision_data.clear()
            self.lane_invasion_data.clear()
            self.trajectory_data.clear()
            self.pedestrian_crossing_states.clear()
            
            # 重置状态
            self.ego_vehicle = None
            self.oncoming_vehicle = None
            self.occlusion_vehicle = None
            self.collision_sensor = None
            self.lane_invasion_sensor = None
            self.camera_sensor = None
            self.collision_detected = False
            self.left_turn_completed = False
            self.reached_opposite_lane = False
            self.scenario_completed = False
            self.failure_reason = None
            
            logger.info("资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# ==================== 使用示例 ====================
if __name__ == '__main__':
    import carla
    import argparse
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 解析参数
    parser = argparse.ArgumentParser(description='AutoExam - 终极版无保护左转场景')
    parser.add_argument('--host', default='localhost', help='CARLA服务器地址')
    parser.add_argument('--port', type=int, default=2000, help='CARLA服务器端口')
    parser.add_argument('--map', default='Town05', help='地图名称')
    parser.add_argument('--weather', default='clear', choices=['clear', 'rain', 'fog', 'night'], help='天气')
    parser.add_argument('--ego-speed', type=float, default=20, help='主车速度 (km/h)')
    parser.add_argument('--oncoming-speed', type=float, default=30, help='对向车速度 (km/h)')
    parser.add_argument('--occlusion', action='store_true', help='启用遮挡车辆')
    
    args = parser.parse_args()
    
    # 连接CARLA
    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)
    
    # 获取世界
    world = client.get_world()
    
    # 创建场景
    scenario = AutopilotScenario(world, client)
    
    try:
        # 设置参数
        params = {
            'map': args.map,
            'weather': args.weather,
            'ego_speed': args.ego_speed,
            'oncoming_speed': args.oncoming_speed,
            'occlusion': args.occlusion
        }
        
        # 设置场景
        if scenario.setup_scenario(params):
            # 执行场景
            result = scenario.execute(max_duration=90)
            
            # 输出结果
            print("\n" + "="*70)
            print("🏁 场景执行结果:")
            print(f"  成功: {result['success']}")
            print(f"  碰撞: {result['collision']}")
            if result['collision']:
                print(f"  碰撞对象: {result['collision_with']}")
            print(f"  左转完成: {result['left_turn_completed']}")
            print(f"  到达对向车道: {result['reached_opposite_lane']}")
            print(f"  耗时: {result['execution_time']:.2f}秒")
            print("\n  场景统计:")
            for k, v in result.get('stats', {}).items():
                print(f"    {k}: {v}")
            print("="*70 + "\n")
        else:
            print("场景设置失败")
            
    finally:
        # 清理
        scenario.cleanup()