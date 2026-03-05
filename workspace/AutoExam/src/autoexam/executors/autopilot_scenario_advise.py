#!/usr/bin/env python3
"""
AutoExam - 高复杂度无保护左转场景生成器 (V2.0)
特性：
- 智能行人行为（速度/路径/群体）
- 行人与车辆互动
- 优化交通流路径
- 多天气场景库
"""

import math
import time
import logging
import random
from typing import Dict, Optional, Tuple, List
from enum import Enum
import numpy as np

logger = logging.getLogger('AutoExam.UnprotectedLeftTurn')


class PedestrianBehavior(Enum):
    """行人行为模式"""
    NORMAL = "normal"          # 正常行走
    CAUTIOUS = "cautious"       # 谨慎（先观察再走）
    RECKLESS = "reckless"       # 鲁莽（不看车）
    GROUP = "group"             # 结伴而行
    ERRATIC = "erratic"         #  erratic（突然变向/停留）
    EMERGENCY = "emergency"     # 紧急情况（奔跑）


class WeatherScenario(Enum):
    """天气场景"""
    CLEAR_DAY = "clear_day"
    CLEAR_NIGHT = "clear_night"
    RAIN_DAY = "rain_day"
    RAIN_NIGHT = "rain_night"
    FOG_DAY = "fog_day"
    FOG_NIGHT = "fog_night"
    HEAVY_RAIN = "heavy_rain"
    WET_SUNSET = "wet_sunset"


class AutopilotScenario:
    """
    高复杂度无保护左转场景 V2.0
    特点：
    - 不依赖Autopilot，使用自定义控制
    - 自动寻找地图中的十字路口
    - 支持参数化配置（车速、距离、天气等）
    - 包含博弈逻辑（等待合适时机左转）
    - 智能行人和非机动车
    - 可配置路口嘈杂程度
    - 多天气场景
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
    
    # 行人类型 (不同年龄/体型)
    PEDESTRIAN_TYPES = {
        'adult_male': 'walker.pedestrian.0001',
        'adult_female': 'walker.pedestrian.0002',
        'child': 'walker.pedestrian.0003',
        'elderly': 'walker.pedestrian.0004',
        'business': 'walker.pedestrian.0005',
        'tourist': 'walker.pedestrian.0006',
        'worker': 'walker.pedestrian.0007',
        'jogger': 'walker.pedestrian.0008',
        'dog_walker': 'walker.pedestrian.0009',
        'homeless': 'walker.pedestrian.0010'
    }
    
    # 行人速度范围 (m/s)
    PEDESTRIAN_SPEEDS = {
        'adult_male': (1.2, 1.6),
        'adult_female': (1.1, 1.5),
        'child': (0.8, 1.2),
        'elderly': (0.5, 0.9),
        'business': (1.4, 1.8),
        'tourist': (0.8, 1.2),
        'worker': (1.2, 1.6),
        'jogger': (2.0, 3.0),
        'dog_walker': (0.9, 1.3),
        'homeless': (0.4, 0.7)
    }
    
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
    
    # 天气场景配置
    WEATHER_SCENARIOS = {
        WeatherScenario.CLEAR_DAY: {
            'sun_altitude_angle': 70,
            'sun_azimuth_angle': 0,
            'cloudiness': 0.0,
            'precipitation': 0.0,
            'precipitation_deposits': 0.0,
            'wind_intensity': 0.0,
            'fog_density': 0.0,
            'fog_distance': 0.0,
            'wetness': 0.0
        },
        WeatherScenario.CLEAR_NIGHT: {
            'sun_altitude_angle': -30,
            'sun_azimuth_angle': 0,
            'cloudiness': 0.0,
            'precipitation': 0.0,
            'precipitation_deposits': 0.0,
            'wind_intensity': 0.0,
            'fog_density': 0.0,
            'fog_distance': 0.0,
            'wetness': 0.0
        },
        WeatherScenario.RAIN_DAY: {
            'sun_altitude_angle': 50,
            'sun_azimuth_angle': 0,
            'cloudiness': 80.0,
            'precipitation': 60.0,
            'precipitation_deposits': 40.0,
            'wind_intensity': 30.0,
            'fog_density': 10.0,
            'fog_distance': 0.0,
            'wetness': 60.0
        },
        WeatherScenario.RAIN_NIGHT: {
            'sun_altitude_angle': -30,
            'sun_azimuth_angle': 0,
            'cloudiness': 90.0,
            'precipitation': 70.0,
            'precipitation_deposits': 50.0,
            'wind_intensity': 40.0,
            'fog_density': 20.0,
            'fog_distance': 0.0,
            'wetness': 70.0
        },
        WeatherScenario.FOG_DAY: {
            'sun_altitude_angle': 60,
            'sun_azimuth_angle': 0,
            'cloudiness': 60.0,
            'precipitation': 0.0,
            'precipitation_deposits': 0.0,
            'wind_intensity': 10.0,
            'fog_density': 60.0,
            'fog_distance': 15.0,
            'wetness': 20.0
        },
        WeatherScenario.FOG_NIGHT: {
            'sun_altitude_angle': -30,
            'sun_azimuth_angle': 0,
            'cloudiness': 70.0,
            'precipitation': 0.0,
            'precipitation_deposits': 0.0,
            'wind_intensity': 10.0,
            'fog_density': 80.0,
            'fog_distance': 10.0,
            'wetness': 30.0
        },
        WeatherScenario.HEAVY_RAIN: {
            'sun_altitude_angle': 40,
            'sun_azimuth_angle': 0,
            'cloudiness': 100.0,
            'precipitation': 100.0,
            'precipitation_deposits': 80.0,
            'wind_intensity': 70.0,
            'fog_density': 40.0,
            'fog_distance': 20.0,
            'wetness': 100.0
        },
        WeatherScenario.WET_SUNSET: {
            'sun_altitude_angle': 15,
            'sun_azimuth_angle': 0,
            'cloudiness': 40.0,
            'precipitation': 0.0,
            'precipitation_deposits': 30.0,
            'wind_intensity': 10.0,
            'fog_density': 10.0,
            'fog_distance': 0.0,
            'wetness': 40.0
        }
    }
    
    def __init__(self, world, client):
        """初始化场景
        
        参数:
            world: CARLA世界对象
            client: CARLA客户端对象
        """
        self.world = world
        self.client = client
        
        # 车辆引用
        self.ego_vehicle = None
        self.oncoming_vehicle = None
        self.occlusion_vehicle = None
        self.traffic_vehicles = []
        self.pedestrians = []
        self.pedestrian_controllers = []
        self.bicycles = []
        self.motorcycles = []
        self.parked_vehicles = []  # 路边停放的车辆
        
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
        
        # 控制相关
        self.ego_control = None
        self.oncoming_control = None
        self.last_tick = 0
        
        # 场景完成标志
        self.left_turn_completed = False
        self.scenario_completed = False
        self.failure_reason = None
        
        # 所有生成的actor
        self.actors = []
        
        # 嘈杂度配置
        self.chaos_level = 'medium'  # low, medium, high, extreme
        
        # 天气场景
        self.weather_scenario = WeatherScenario.CLEAR_DAY
        
        # 统计信息
        self.stats = {
            'vehicles': 0,
            'pedestrians': 0,
            'bicycles': 0,
            'motorcycles': 0,
            'parked_vehicles': 0
        }
        
        # 交叉口区域
        self.junction_area = None
        
        # 行人目标点缓存
        self.pedestrian_destinations = []
    
    def setup_scenario(self, params: Dict) -> bool:
        """设置场景
        
        参数:
            params: 场景参数字典
                - map: 地图名称 (默认: 'Town05')
                - weather: 天气场景
                - ego_speed: 主车初始速度 (km/h)
                - oncoming_speed: 对向车速度 (km/h)
                - time_gap: 安全时间间隙 (秒)
                - oncoming_vehicle_type: 对向车型
                - has_occlusion: 是否有遮挡车辆
                - chaos_level: 嘈杂度级别 (low/medium/high/extreme)
                - pedestrian_behavior: 行人行为模式
                - dynamic_weather: 是否动态变化天气
                - random_seed: 随机种子
        """
        try:
            import carla
            
            # 设置随机种子
            random.seed(params.get('random_seed', 42))
            
            # 获取嘈杂度级别
            self.chaos_level = params.get('chaos_level', 'medium')
            
            # 获取天气场景
            weather_scenario = params.get('weather', 'clear_day')
            if isinstance(weather_scenario, str):
                try:
                    self.weather_scenario = WeatherScenario(weather_scenario)
                except:
                    self.weather_scenario = WeatherScenario.CLEAR_DAY
            else:
                self.weather_scenario = weather_scenario
            
            logger.info("=" * 60)
            logger.info(f"AutoExam V2.0 - 高复杂度无保护左转场景")
            logger.info(f"嘈杂度: {self.chaos_level}, 天气: {self.weather_scenario.value}")
            logger.info("=" * 60)
            
            # 加载地图
            map_name = params.get('map', 'Town05')
            if self.world.get_map().name.split('/')[-1] != map_name:
                logger.info(f"加载地图: {map_name}")
                self.world = self.client.load_world(map_name)
                time.sleep(2)  # 等待地图加载
            
            # 设置天气
            self._set_weather_scenario(self.weather_scenario)
            
            # 寻找合适的路口
            junction_info = self._find_suitable_intersection()
            if not junction_info:
                logger.error("未找到合适的路口")
                return False
            
            ego_spawn, oncoming_spawn, left_target = junction_info
            logger.info(f"找到路口: 主车={ego_spawn.location}, 对向={oncoming_spawn.location}")
            
            # 定义路口区域（用于行人/车辆互动）
            self.junction_area = {
                'center': self.junction.bounding_box.location,
                'radius': 50.0
            }
            
            # 生成主车
            if not self._spawn_ego_vehicle(ego_spawn, params):
                return False
            
            # 生成对向来车
            self._spawn_oncoming_vehicle(oncoming_spawn, params)
            
            # 生成遮挡车辆（可选）
            if params.get('occlusion', False):
                self._spawn_occlusion_vehicle(ego_spawn, oncoming_spawn)
            
            # 生成交通流（根据密度）
            traffic_density = params.get('traffic_density', self._density_from_chaos('traffic'))
            self._spawn_traffic_flow(ego_spawn, oncoming_spawn, traffic_density)
            
            # 生成非机动车（自行车/摩托车）
            bicycle_density = params.get('bicycle_density', self._density_from_chaos('bicycle'))
            self._spawn_bicycles(ego_spawn, oncoming_spawn, left_target, bicycle_density)
            
            motorcycle_density = params.get('motorcycle_density', self._density_from_chaos('motorcycle'))
            self._spawn_motorcycles(ego_spawn, oncoming_spawn, left_target, motorcycle_density)
            
            # 生成行人（使用指定的行为模式）
            pedestrian_density = params.get('pedestrian_density', self._density_from_chaos('pedestrian'))
            pedestrian_behavior = params.get('pedestrian_behavior', 'normal')
            self._spawn_pedestrians_v2(left_target, pedestrian_density, pedestrian_behavior)
            
            # 生成路边停放的车辆
            parked_density = params.get('parked_vehicle_density', self._density_from_chaos('parked'))
            self._spawn_parked_vehicles(ego_spawn, oncoming_spawn, parked_density)
            
            # 设置传感器
            self._setup_sensors()
            
            # 设置观察视角
            self._setup_spectator()
            
            # 打印统计信息
            logger.info("=" * 60)
            logger.info("场景生成统计:")
            logger.info(f"  主车: 1")
            logger.info(f"  对向来车: {1 if self.oncoming_vehicle else 0}")
            logger.info(f"  交通流车辆: {len(self.traffic_vehicles)}")
            logger.info(f"  自行车: {len(self.bicycles)}")
            logger.info(f"  摩托车: {len(self.motorcycles)}")
            logger.info(f"  行人: {len(self.pedestrians)}")
            logger.info(f"  路边停车: {len(self.parked_vehicles)}")
            logger.info(f"  总Actor数: {len(self.actors)}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"设置场景失败: {e}", exc_info=True)
            return False
    
    def _set_weather_scenario(self, scenario: WeatherScenario):
        """设置天气场景"""
        try:
            import carla
            
            if scenario not in self.WEATHER_SCENARIOS:
                logger.warning(f"未知天气场景: {scenario}, 使用默认")
                scenario = WeatherScenario.CLEAR_DAY
            
            weather_params = self.WEATHER_SCENARIOS[scenario]
            weather = carla.WeatherParameters(
                sun_altitude_angle=weather_params['sun_altitude_angle'],
                sun_azimuth_angle=weather_params['sun_azimuth_angle'],
                cloudiness=weather_params['cloudiness'],
                precipitation=weather_params['precipitation'],
                precipitation_deposits=weather_params['precipitation_deposits'],
                wind_intensity=weather_params['wind_intensity'],
                fog_density=weather_params['fog_density'],
                fog_distance=weather_params['fog_distance'],
                wetness=weather_params['wetness']
            )
            
            self.world.set_weather(weather)
            logger.info(f"天气设置为: {scenario.value}")
            
        except Exception as e:
            logger.error(f"设置天气失败: {e}")
    
    def _density_from_chaos(self, category: str) -> str:
        """根据嘈杂度级别获取密度配置"""
        chaos_map = {
            'low': {
                'traffic': 'low',
                'pedestrian': 'none',
                'bicycle': 'none',
                'motorcycle': 'none',
                'parked': 'none'
            },
            'medium': {
                'traffic': 'medium',
                'pedestrian': 'low',
                'bicycle': 'low',
                'motorcycle': 'low',
                'parked': 'low'
            },
            'high': {
                'traffic': 'high',
                'pedestrian': 'medium',
                'bicycle': 'medium',
                'motorcycle': 'medium',
                'parked': 'medium'
            },
            'extreme': {
                'traffic': 'extreme',
                'pedestrian': 'high',
                'bicycle': 'high',
                'motorcycle': 'high',
                'parked': 'high'
            }
        }
        return chaos_map.get(self.chaos_level, chaos_map['medium']).get(category, 'low')
    
    def _find_suitable_intersection(self) -> Optional[Tuple]:
        """
        在地图中寻找合适的十字路口
        返回: (主车生成点, 对向车生成点, 左转目标点)
        """
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
        
        # 选择最大的路口（通常是主要交叉口）
        target_junction = max(junctions, key=lambda j: len(j.get_waypoints(carla.LaneType.Driving)))
        self.junction = target_junction
        
        # 获取路口的车道信息
        junction_ways = target_junction.get_waypoints(carla.LaneType.Driving)
        
        # 寻找适合左转的车道组合
        for entry_waypoint, exit_waypoint in junction_ways:
            # 主车应该在进入路口前50-100米
            if entry_waypoint.lane_type == carla.LaneType.Driving:
                # 寻找对向车道
                # 获取对向车道的waypoint
                opposite_waypoint = None
                for wp in entry_waypoint.next(1):
                    # 寻找与当前车道方向相反的车道
                    yaw_diff = abs(wp.transform.rotation.yaw - entry_waypoint.transform.rotation.yaw)
                    if yaw_diff > 170:
                        opposite_waypoint = wp
                        break
                
                if opposite_waypoint and opposite_waypoint.lane_type == carla.LaneType.Driving:
                    
                    # 检查是否可以左转（进入路口的朝向与离开路口的朝向成90度左右）
                    entry_yaw = entry_waypoint.transform.rotation.yaw
                    exit_yaw = exit_waypoint.transform.rotation.yaw
                    yaw_diff = abs(entry_yaw - exit_yaw)
                    if yaw_diff > 180:
                        yaw_diff = 360 - yaw_diff
                    
                    # 左转应该是90度左右
                    if 70 < yaw_diff < 110:
                        # 找到左转的目标点
                        self.ego_start_waypoint = entry_waypoint
                        self.oncoming_start_waypoint = opposite_waypoint
                        self.left_target_waypoint = exit_waypoint
                        
                        # 生成具体位置（往前移动一段距离）
                        ego_location = entry_waypoint.transform.location
                        oncoming_location = opposite_waypoint.transform.location
                        target_location = exit_waypoint.transform.location
                        
                        # 沿着道路方向移动50米
                        forward_vector = entry_waypoint.transform.get_forward_vector()
                        ego_start = carla.Transform(
                            carla.Location(
                                x=ego_location.x - forward_vector.x * 50,
                                y=ego_location.y - forward_vector.y * 50,
                                z=ego_location.z + 0.5
                            ),
                            entry_waypoint.transform.rotation
                        )
                        
                        # 对向车移动80米（稍微远一点，模拟接近过程）
                        oncoming_start = carla.Transform(
                            carla.Location(
                                x=oncoming_location.x + forward_vector.x * 80,  # 对向车朝我们驶来
                                y=oncoming_location.y + forward_vector.y * 80,
                                z=oncoming_location.z + 0.5
                            ),
                            opposite_waypoint.transform.rotation
                        )
                        
                        return (ego_start, oncoming_start, target_location)
        
        logger.warning("未找到合适的左转路口，使用默认位置")
        # 降级：使用第一个路口
        entry_waypoint, exit_waypoint = junction_ways[0]
        return (
            entry_waypoint.transform,
            entry_waypoint.get_opposite().transform,
            exit_waypoint.transform.location
        )
    
    def _spawn_ego_vehicle(self, spawn_point, params: Dict) -> bool:
        """生成主车"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            
            # 选择车型
            vehicle_type = params.get('ego_vehicle_type', 'suv')
            bp_name = self.VEHICLE_TYPES.get(vehicle_type, self.VEHICLE_TYPES['suv'])
            ego_bp = blueprint_library.filter(bp_name)[0]
            ego_bp.set_attribute('role_name', 'hero')
            
            # 生成车辆
            self.ego_vehicle = self.world.try_spawn_actor(ego_bp, spawn_point)
            if not self.ego_vehicle:
                # 如果失败，尝试附近位置
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
            
            # 设置初始速度
            target_speed = params.get('ego_speed', 30) / 3.6  # km/h to m/s
            self.ego_vehicle.set_target_velocity(
                spawn_point.get_forward_vector() * target_speed
            )
            
            # 创建控制器
            self.ego_control = carla.VehicleControl()
            self.ego_control.throttle = 0.5
            
            logger.info(f"主车已生成: {bp_name}, 初始速度: {params.get('ego_speed', 30)}km/h")
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
                # 尝试附近位置
                for i in range(3):
                    offset = carla.Location(x=random.uniform(-2, 2), y=random.uniform(-2, 2))
                    spawn_point.location += offset
                    self.oncoming_vehicle = self.world.try_spawn_actor(vehicle_bp, spawn_point)
                    if self.oncoming_vehicle:
                        break
            
            if self.oncoming_vehicle:
                self.actors.append(self.oncoming_vehicle)
                
                # 设置初始速度（对向车朝主车驶来）
                target_speed = params.get('oncoming_speed', 40) / 3.6
                forward_vector = spawn_point.get_forward_vector()
                # 朝反方向行驶
                direction = carla.Vector3D(-forward_vector.x, -forward_vector.y, -forward_vector.z)
                self.oncoming_vehicle.set_target_velocity(direction * target_speed)
                
                # 创建控制器
                self.oncoming_control = carla.VehicleControl()
                self.oncoming_control.throttle = 0.5
                
                logger.info(f"对向来车已生成: {bp_name}, 速度: {params.get('oncoming_speed', 40)}km/h")
            else:
                logger.warning("无法生成对向来车")
                
        except Exception as e:
            logger.warning(f"生成对向来车失败: {e}")
    
    def _spawn_occlusion_vehicle(self, ego_spawn, oncoming_spawn):
        """生成遮挡车辆（大车挡住主车视线）"""
        try:
            import carla
            
            blueprint_library = self.world.get_blueprint_library()
            truck_bp = blueprint_library.filter('vehicle.carlamotors.carlacola')[0]
            
            # 在主车和路口之间生成遮挡车辆
            direction = (self.junction.bounding_box.location - ego_spawn.location).make_unit_vector()
            occlusion_location = ego_spawn.location + direction * 40  # 在主车前40米，避免碰撞
            
            # 调整到正确车道
            waypoint = self.world.get_map().get_waypoint(occlusion_location)
            if waypoint:
                occlusion_transform = carla.Transform(
                    waypoint.transform.location + carla.Location(z=0.5),
                    ego_spawn.rotation
                )
                
                self.occlusion_vehicle = self.world.try_spawn_actor(truck_bp, occlusion_transform)
                if self.occlusion_vehicle:
                    self.actors.append(self.occlusion_vehicle)
                    
                    # 停在原地
                    self.occlusion_vehicle.set_target_velocity(carla.Vector3D())
                    self.occlusion_vehicle.set_autopilot(False)
                    
                    logger.info(f"遮挡车辆已生成 (位置: {occlusion_transform.location})")
                    
        except Exception as e:
            logger.warning(f"生成遮挡车辆失败: {e}")
    
    def _spawn_traffic_flow(self, ego_spawn, oncoming_spawn, density: str):
        """生成交通流 - 优化版（使用waypoint导航，避免碰撞）"""
        try:
            import carla
            
            densities = {
                'none': 0,
                'low': 3,
                'medium': 6,
                'high': 10,
                'extreme': 15
            }
            num_vehicles = densities.get(density, 3)
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            
            # 获取道路上的所有waypoint
            all_waypoints = carla_map.generate_waypoints(5.0)
            
            # 按车道分组
            lanes = {}
            for wp in all_waypoints:
                lane_id = (wp.road_id, wp.lane_id)
                if lane_id not in lanes:
                    lanes[lane_id] = []
                lanes[lane_id].append(wp)
            
            # 选择几条主要车道
            main_lanes = list(lanes.keys())[:4]  # 最多4条车道
            
            vehicles_per_lane = max(1, num_vehicles // len(main_lanes))
            
            for lane_id in main_lanes[:vehicles_per_lane]:
                lane_wps = lanes[lane_id]
                if len(lane_wps) < 5:
                    continue
                
                # 在车道上均匀分布车辆
                for i in range(vehicles_per_lane):
                    try:
                        vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
                        if vehicle_bp.get_attribute('number_of_wheels').as_int() != 4:
                            continue
                        
                        # 选择waypoint
                        wp_index = (i * len(lane_wps)) // vehicles_per_lane
                        wp = lane_wps[wp_index % len(lane_wps)]
                        
                        # 避免在路口内生成
                        if wp.is_junction:
                            continue
                        
                        # 避免离主车太近
                        if self.ego_vehicle:
                            dist_to_ego = wp.transform.location.distance(self.ego_vehicle.get_location())
                            if dist_to_ego < 20:
                                continue
                        
                        transform = carla.Transform(
                            wp.transform.location + carla.Location(z=0.5),
                            wp.transform.rotation
                        )
                        
                        vehicle = self.world.try_spawn_actor(vehicle_bp, transform)
                        if vehicle:
                            self.traffic_vehicles.append(vehicle)
                            self.actors.append(vehicle)
                            
                            # 设置autopilot，但调整速度范围
                            vehicle.set_autopilot(True)
                            
                            # 随机速度偏移
                            try:
                                speed_diff = random.uniform(-2, 2)
                                vehicle.apply_control(carla.VehicleControl(throttle=0.5))
                            except:
                                pass
                            
                    except Exception as e:
                        continue
            
            logger.info(f"已生成 {len(self.traffic_vehicles)} 辆交通流车辆")
            
        except Exception as e:
            logger.warning(f"生成交通流失败: {e}")
    
    def _spawn_bicycles(self, ego_spawn, oncoming_spawn, target_location, density: str):
        """生成自行车"""
        try:
            import carla
            
            densities = {
                'none': 0,
                'low': 2,
                'medium': 4,
                'high': 8,
                'extreme': 12
            }
            num_bikes = densities.get(density, 2)
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            
            for i in range(num_bikes):
                try:
                    bike_bp = blueprint_library.filter(random.choice(self.BICYCLE_TYPES))[0]
                    
                    # 选择生成位置
                    spawn_choices = [
                        ego_spawn.location + carla.Location(x=random.uniform(-30, 30), y=random.uniform(-30, 30)),
                        oncoming_spawn.location + carla.Location(x=random.uniform(-30, 30), y=random.uniform(-30, 30)),
                        target_location + carla.Location(x=random.uniform(-20, 20), y=random.uniform(-20, 20))
                    ]
                    spawn_loc = random.choice(spawn_choices)
                    
                    # 找到最近的道路点
                    waypoint = carla_map.get_waypoint(spawn_loc)
                    if waypoint:
                        transform = carla.Transform(
                            waypoint.transform.location + carla.Location(z=0.5),
                            waypoint.transform.rotation
                        )
                        
                        bike = self.world.try_spawn_actor(bike_bp, transform)
                        if bike:
                            self.bicycles.append(bike)
                            self.actors.append(bike)
                            
                            # 随机速度
                            speed = random.uniform(2, 5)
                            bike.set_target_velocity(
                                waypoint.transform.get_forward_vector() * speed
                            )
                            bike.set_autopilot(True)
                            
                except Exception as e:
                    continue
            
            logger.info(f"已生成 {len(self.bicycles)} 辆自行车")
            
        except Exception as e:
            logger.warning(f"生成自行车失败: {e}")
    
    def _spawn_motorcycles(self, ego_spawn, oncoming_spawn, target_location, density: str):
        """生成摩托车"""
        try:
            import carla
            
            densities = {
                'none': 0,
                'low': 1,
                'medium': 3,
                'high': 5,
                'extreme': 8
            }
            num_motos = densities.get(density, 1)
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            
            for i in range(num_motos):
                try:
                    moto_bp = blueprint_library.filter(random.choice(self.MOTORCYCLE_TYPES))[0]
                    
                    # 选择生成位置
                    spawn_choices = [
                        ego_spawn.location + carla.Location(x=random.uniform(-40, 40), y=random.uniform(-40, 40)),
                        oncoming_spawn.location + carla.Location(x=random.uniform(-40, 40), y=random.uniform(-40, 40)),
                        target_location + carla.Location(x=random.uniform(-30, 30), y=random.uniform(-30, 30))
                    ]
                    spawn_loc = random.choice(spawn_choices)
                    
                    waypoint = carla_map.get_waypoint(spawn_loc)
                    if waypoint:
                        transform = carla.Transform(
                            waypoint.transform.location + carla.Location(z=0.5),
                            waypoint.transform.rotation
                        )
                        
                        moto = self.world.try_spawn_actor(moto_bp, transform)
                        if moto:
                            self.motorcycles.append(moto)
                            self.actors.append(moto)
                            
                            # 摩托车速度较快
                            speed = random.uniform(5, 12)
                            moto.set_target_velocity(
                                waypoint.transform.get_forward_vector() * speed
                            )
                            moto.set_autopilot(True)
                            
                except Exception as e:
                    continue
            
            logger.info(f"已生成 {len(self.motorcycles)} 辆摩托车")
            
        except Exception as e:
            logger.warning(f"生成摩托车失败: {e}")
    
    def _spawn_pedestrians_v2(self, target_location, density: str, behavior_mode: str = 'normal'):
        """
        生成行人 - V2版
        支持多种行为模式
        """
        try:
            import carla
            
            densities = {
                'none': 0,
                'low': 4,
                'medium': 10,
                'high': 20,
                'extreme': 35
            }
            num_pedestrians = densities.get(density, 4)
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            
            # 创建几个兴趣点作为行人目的地
            interest_points = [
                target_location,
                target_location + carla.Location(x=30, y=30),
                target_location + carla.Location(x=-30, y=30),
                target_location + carla.Location(x=30, y=-30),
                target_location + carla.Location(x=-30, y=-30),
            ]
            
            # 如果有主车，也可以作为兴趣点
            if self.ego_vehicle:
                interest_points.append(self.ego_vehicle.get_location())
            
            # 解析行为模式
            try:
                behavior = PedestrianBehavior(behavior_mode)
            except:
                behavior = PedestrianBehavior.NORMAL
            
            logger.info(f"行人行为模式: {behavior.value}")
            
            for i in range(num_pedestrians):
                try:
                    # 随机选择行人类型
                    ped_type = random.choice(list(self.PEDESTRIAN_TYPES.keys()))
                    ped_bp = blueprint_library.filter(self.PEDESTRIAN_TYPES[ped_type])[0]
                    
                    # 获取该类型行人的速度范围
                    speed_min, speed_max = self.PEDESTRIAN_SPEEDS.get(ped_type, (1.0, 1.5))
                    
                    # 根据行为模式调整速度
                    if behavior == PedestrianBehavior.RECKLESS:
                        speed_min *= 1.5
                        speed_max *= 1.5
                    elif behavior == PedestrianBehavior.CAUTIOUS:
                        speed_min *= 0.7
                        speed_max *= 0.7
                    elif behavior == PedestrianBehavior.EMERGENCY:
                        speed_min = 2.5
                        speed_max = 4.0
                    
                    # 生成位置
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(15, 35)
                    offset_x = radius * math.cos(angle)
                    offset_y = radius * math.sin(angle)
                    
                    spawn_location = carla.Location(
                        x=target_location.x + offset_x,
                        y=target_location.y + offset_y,
                        z=target_location.z + 0.5
                    )
                    
                    # 确保在可行走区域
                    waypoint = carla_map.get_waypoint(spawn_location, project_to_road=False)
                    if waypoint and waypoint.lane_type == carla.LaneType.Sidewalk:
                        transform = carla.Transform(spawn_location)
                        
                        pedestrian = self.world.try_spawn_actor(ped_bp, transform)
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
                                
                                # 根据行为模式设置行为
                                self._setup_pedestrian_behavior(
                                    controller, pedestrian, 
                                    interest_points, behavior,
                                    speed_min, speed_max
                                )
                                
                except Exception as e:
                    continue
            
            logger.info(f"已生成 {len(self.pedestrians)} 个行人 (模式: {behavior.value})")
            
        except Exception as e:
            logger.warning(f"生成行人失败: {e}")
    
    def _setup_pedestrian_behavior(self, controller, pedestrian, interest_points, 
                                   behavior: PedestrianBehavior, speed_min: float, speed_max: float):
        """设置行人具体行为"""
        import carla
        
        if behavior == PedestrianBehavior.NORMAL:
            # 正常行走：随机目的地，偶尔停留
            dest = random.choice(interest_points)
            controller.go_to_location(dest)
            controller.set_max_speed(random.uniform(speed_min, speed_max))
            
            # 随机停留
            if random.random() < 0.3:
                time.sleep(random.uniform(1, 3))
                
        elif behavior == PedestrianBehavior.CAUTIOUS:
            # 谨慎：先观察再走，速度慢
            dest = random.choice(interest_points)
            controller.go_to_location(dest)
            controller.set_max_speed(speed_min)
            
            # 经常停下来观察
            if random.random() < 0.5:
                time.sleep(random.uniform(2, 4))
                
        elif behavior == PedestrianBehavior.RECKLESS:
            # 鲁莽：不看车，直接冲
            # 可能直接冲向马路
            road_waypoint = self.world.get_map().get_waypoint(pedestrian.get_location())
            if road_waypoint:
                controller.go_to_location(road_waypoint.transform.location)
            controller.set_max_speed(speed_max)
            
        elif behavior == PedestrianBehavior.GROUP:
            # 结伴：多个行人有相似目的地
            # 随机选择一个"领头"目的地
            group_dest = random.choice(interest_points)
            controller.go_to_location(group_dest)
            controller.set_max_speed(random.uniform(speed_min, speed_max))
            
        elif behavior == PedestrianBehavior.ERRATIC:
            #  erratic：突然变向/停留
            # 每5-10秒改变一次目的地
            def change_destination():
                import threading
                def _change():
                    while pedestrian.is_alive:
                        time.sleep(random.uniform(5, 10))
                        new_dest = random.choice(interest_points)
                        controller.go_to_location(new_dest)
                
                thread = threading.Thread(target=_change)
                thread.daemon = True
                thread.start()
            
            change_destination()
            controller.set_max_speed(random.uniform(speed_min, speed_max))
            
        elif behavior == PedestrianBehavior.EMERGENCY:
            # 紧急：快速奔跑，可能不看路
            # 直接冲向某个点
            dest = random.choice(interest_points)
            controller.go_to_location(dest)
            controller.set_max_speed(speed_max)
    
    def _spawn_parked_vehicles(self, ego_spawn, oncoming_spawn, density: str):
        """生成路边停放的车辆"""
        try:
            import carla
            
            densities = {
                'none': 0,
                'low': 3,
                'medium': 6,
                'high': 12,
                'extreme': 18
            }
            num_parked = densities.get(density, 3)
            
            blueprint_library = self.world.get_blueprint_library()
            carla_map = self.world.get_map()
            
            for i in range(num_parked):
                try:
                    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
                    if vehicle_bp.get_attribute('number_of_wheels').as_int() != 4:
                        continue
                    
                    # 在路边生成
                    offset = random.uniform(-40, 40)
                    spawn_location = carla.Location(
                        x=ego_spawn.location.x + offset,
                        y=ego_spawn.location.y + offset,
                        z=ego_spawn.location.z
                    )
                    
                    waypoint = carla_map.get_waypoint(spawn_location)
                    if waypoint:
                        # 稍微偏离道路中心
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
                            
                            # 停在原地
                            vehicle.set_target_velocity(carla.Vector3D())
                            vehicle.set_autopilot(False)
                            
                except Exception as e:
                    continue
            
            logger.info(f"已生成 {len(self.parked_vehicles)} 辆路边停车")
            
        except Exception as e:
            logger.warning(f"生成路边停车失败: {e}")
    
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
                # 获取路口中心
                junction_center = self.junction.bounding_box.location
                
                # 设置俯瞰视角
                camera_location = carla.Location(
                    x=junction_center.x,
                    y=junction_center.y - 60,  # 从侧面观察
                    z=45  # 更高视角，看到更多行人
                )
                
                camera_rotation = carla.Rotation(
                    pitch=-60,  # 更陡的俯角
                    yaw=90
                )
                
                self.spectator.set_transform(carla.Transform(camera_location, camera_rotation))
                logger.info("相机设置为俯瞰视角")
                
        except Exception as e:
            logger.error(f"设置相机失败: {e}")
    
    def _update_spectator(self):
        """更新观察视角（保持俯瞰）"""
        try:
            import carla
            
            if self.spectator and self.ego_vehicle and self.junction:
                junction_center = self.junction.bounding_box.location
                ego_loc = self.ego_vehicle.get_location()
                
                # 动态调整视角：跟随主车但保持俯瞰路口
                camera_location = carla.Location(
                    x=ego_loc.x,
                    y=junction_center.y - 60,
                    z=45
                )
                
                self.spectator.set_transform(carla.Transform(
                    camera_location,
                    carla.Rotation(pitch=-60, yaw=90)
                ))
                
        except Exception as e:
            logger.warning(f"更新相机失败: {e}")
    
    def _check_pedestrian_vehicle_interaction(self):
        """
        检查行人与车辆的互动
        模拟行人观察车辆、车辆避让行人的行为
        """
        try:
            import carla
            
            if not self.ego_vehicle or len(self.pedestrians) == 0:
                return
            
            ego_loc = self.ego_vehicle.get_location()
            ego_velocity = self.ego_vehicle.get_velocity()
            ego_speed = math.sqrt(ego_velocity.x**2 + ego_velocity.y**2)
            
            for pedestrian in self.pedestrians:
                if not pedestrian.is_alive:
                    continue
                
                ped_loc = pedestrian.get_location()
                distance = ego_loc.distance(ped_loc)
                
                # 如果行人在主车附近
                if distance < 15:
                    # 判断行人是否在过马路（在人行横道或路口）
                    waypoint = self.world.get_map().get_waypoint(ped_loc)
                    if waypoint and (waypoint.is_junction or distance < 10):
                        
                        # 行人观察车辆
                        # 如果车辆速度快，行人可能犹豫
                        if ego_speed > 8.0:  # >28.8km/h
                            # 让行人的控制器暂停一下（模拟观察）
                            for controller in self.pedestrian_controllers:
                                if controller.parent == pedestrian:
                                    # 短暂停顿
                                    controller.pause()
                                    # 0.5秒后继续
                                    def resume(c):
                                        time.sleep(0.5)
                                        c.resume()
                                    import threading
                                    thread = threading.Thread(target=resume, args=(controller,))
                                    thread.daemon = True
                                    thread.start()
                        
                        # 车辆减速逻辑（在控制主车时处理）
                        # 这里只记录互动
                        logger.debug(f"行人-车辆互动: 距离={distance:.1f}m, 车速={ego_speed*3.6:.1f}km/h")
                        
        except Exception as e:
            logger.warning(f"检查行人与车辆互动失败: {e}")
    
    def _is_safe_to_turn(self) -> bool:
        """
        判断是否可以安全左转
        基于对向车辆的距离和速度，以及行人的位置
        """
        if not self.oncoming_vehicle:
            return True
        
        ego_loc = self.ego_vehicle.get_location()
        oncoming_loc = self.oncoming_vehicle.get_location()
        junction_center = self.junction.bounding_box.location
        
        # 计算到路口的距离
        ego_to_junction = math.sqrt(
            (ego_loc.x - junction_center.x)**2 + 
            (ego_loc.y - junction_center.y)**2
        )
        
        oncoming_to_junction = math.sqrt(
            (oncoming_loc.x - junction_center.x)**2 + 
            (oncoming_loc.y - junction_center.y)**2
        )
        
        # 获取对向车速度
        oncoming_velocity = self.oncoming_vehicle.get_velocity()
        oncoming_speed = math.sqrt(
            oncoming_velocity.x**2 + 
            oncoming_velocity.y**2 + 
            oncoming_velocity.z**2
        )
        
        if oncoming_speed < 0.1:  # 对向车停住了
            return True
        
        # 估算到达路口的时间
        ego_speed = self._get_vehicle_speed(self.ego_vehicle)
        if ego_speed < 0.1:
            ego_speed = 5.0  # 假设起步速度
        
        time_to_junction_ego = ego_to_junction / ego_speed
        time_to_junction_oncoming = oncoming_to_junction / oncoming_speed
        
        # 安全间隙：根据嘈杂度调整
        base_gap = 3.0
        if self.chaos_level == 'high':
            base_gap = 4.0
        elif self.chaos_level == 'extreme':
            base_gap = 5.0
        
        # 检查是否有行人在路口
        pedestrian_danger = self._check_pedestrian_danger()
        if pedestrian_danger:
            base_gap += 1.0
        
        safe = (time_to_junction_oncoming - time_to_junction_ego) > base_gap
        
        return safe
    
    def _check_pedestrian_danger(self) -> bool:
        """检查是否有行人在危险区域"""
        if not self.pedestrians or not self.junction_area:
            return False
        
        junction_center = self.junction_area['center']
        
        for pedestrian in self.pedestrians:
            if not pedestrian.is_alive:
                continue
            
            ped_loc = pedestrian.get_location()
            dist_to_junction = ped_loc.distance(junction_center)
            
            # 如果行人在路口附近且正在过马路
            if dist_to_junction < 30:
                # 检查行人是否在车道上
                waypoint = self.world.get_map().get_waypoint(ped_loc)
                if waypoint and waypoint.lane_type.name == 'Driving':
                    return True
        
        return False
    
    def _get_vehicle_speed(self, vehicle) -> float:
        """获取车辆速度（m/s）"""
        velocity = vehicle.get_velocity()
        return math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
    
    def _control_ego_vehicle(self):
        """控制主车 - 增加对行人的感知"""
        if not self.ego_vehicle or not self.ego_control:
            return
        
        import carla
        
        ego_loc = self.ego_vehicle.get_location()
        junction_center = self.junction.bounding_box.location
        
        # 到路口的距离
        distance_to_junction = math.sqrt(
            (ego_loc.x - junction_center.x)**2 + 
            (ego_loc.y - junction_center.y)**2
        )
        
        # 获取当前速度
        current_speed = self._get_vehicle_speed(self.ego_vehicle)
        
        # 检查是否有行人在前方
        pedestrian_ahead = self._check_pedestrian_ahead()
        
        # 阶段1: 接近路口
        if distance_to_junction > 15:
            # 保持速度，但如果有行人则减速
            if pedestrian_ahead:
                self.ego_control.throttle = 0.2
                self.ego_control.brake = 0.1
            else:
                target_speed = 10.0  # 约36km/h
                if current_speed < target_speed:
                    self.ego_control.throttle = 0.5
                else:
                    self.ego_control.throttle = 0.2
                self.ego_control.brake = 0.0
            self.ego_control.steer = 0.0
            
        # 阶段2: 到达路口，观察并决策
        elif distance_to_junction <= 15 and not self.left_turn_completed:
            # 减速观察
            if current_speed > 3.0:
                self.ego_control.throttle = 0.0
                self.ego_control.brake = 0.4
                self.ego_control.steer = 0.0
            else:
                self.ego_control.brake = 0.0
                
                # 判断是否安全（考虑车辆和行人）
                if self._is_safe_to_turn() and not pedestrian_ahead:
                    # 安全，开始左转
                    self.ego_control.throttle = 0.4
                    self.ego_control.steer = 0.7  # 增大转向角度
                    
                    # 检查左转是否完成
                    if self.left_target_waypoint:
                        target_loc = self.left_target_waypoint.transform.location
                        distance_to_target = math.sqrt(
                            (ego_loc.x - target_loc.x)**2 + 
                            (ego_loc.y - target_loc.y)**2
                        )
                        
                        if distance_to_target < 15:
                            self.left_turn_completed = True
                            logger.info("左转完成！")
                else:
                    # 不安全，等待
                    self.ego_control.throttle = 0.0
                    self.ego_control.steer = 0.0
        
        # 阶段3: 完成左转，驶离
        else:
            target_speed = 10.0
            if current_speed < target_speed:
                self.ego_control.throttle = 0.5
            else:
                self.ego_control.throttle = 0.2
            self.ego_control.steer = 0.0
        
        # 应用控制
        self.ego_vehicle.apply_control(self.ego_control)
    
    def _check_pedestrian_ahead(self) -> bool:
        """检查主车前方是否有行人"""
        if not self.ego_vehicle or not self.pedestrians:
            return False
        
        ego_loc = self.ego_vehicle.get_location()
        ego_forward = self.ego_vehicle.get_transform().get_forward_vector()
        
        for pedestrian in self.pedestrians:
            if not pedestrian.is_alive:
                continue
            
            ped_loc = pedestrian.get_location()
            
            # 计算相对位置
            to_ped = ped_loc - ego_loc
            
            # 计算点积，判断是否在前方
            dot = ego_forward.x * to_ped.x + ego_forward.y * to_ped.y
            
            # 距离
            distance = math.sqrt(to_ped.x**2 + to_ped.y**2)
            
            # 如果行人在前方15米内，且在车辆朝向的45度范围内
            if distance < 15 and dot > 0 and dot > distance * 0.7:
                return True
        
        return False
    
    def _control_oncoming_vehicle(self):
        """控制对向来车"""
        if not self.oncoming_vehicle or not self.oncoming_control:
            return
        
        # 简单逻辑：保持直行，接近路口
        self.oncoming_vehicle.apply_control(self.oncoming_control)
    
    def execute(self, max_duration: float = 30.0) -> Dict:
        """
        执行场景
        
        参数:
            max_duration: 最大执行时间（秒）
            
        返回:
            执行结果
        """
        import carla
        
        self.trajectory_data = []
        start_time = time.time()
        last_log_time = start_time
        interaction_check_time = start_time
        
        logger.info("开始执行高复杂度无保护左转场景 V2.0...")
        
        try:
            while time.time() - start_time < max_duration:
                current_time = time.time()
                
                # 检查碰撞
                if self.collision_detected:
                    logger.warning("检测到碰撞，场景终止")
                    self.failure_reason = 'collision'
                    break
                
                # 检查行人-车辆互动（每秒5次）
                if current_time - interaction_check_time > 0.2:
                    self._check_pedestrian_vehicle_interaction()
                    interaction_check_time = current_time
                
                # 获取主车状态
                if self.ego_vehicle:
                    transform = self.ego_vehicle.get_transform()
                    velocity = self.ego_vehicle.get_velocity()
                    speed = math.sqrt(velocity.x**2 + velocity.y**2) * 3.6
                    
                    # 记录轨迹（每秒一次）
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
                    
                    # 检查场景完成
                    if self.left_turn_completed:
                        # 左转完成后，再行驶一段距离确认
                        if self.left_target_waypoint:
                            target_loc = self.left_target_waypoint.transform.location
                            distance = math.sqrt(
                                (transform.location.x - target_loc.x)**2 + 
                                (transform.location.y - target_loc.y)**2
                            )
                            if distance > 20:  # 驶离路口足够远
                                self.scenario_completed = True
                                logger.info("场景成功完成")
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
            'scenario_completed': self.scenario_completed,
            'failure_reason': self.failure_reason,
            'execution_time': execution_time,
            'collision_count': len(self.collision_data),
            'collision_details': collision_details,
            'lane_invasion_count': len(self.lane_invasion_data),
            'trajectory_data': self.trajectory_data,
            'weather': self.weather_scenario.value,
            'stats': {
                'vehicles': len(self.traffic_vehicles),
                'pedestrians': len(self.pedestrians),
                'bicycles': len(self.bicycles),
                'motorcycles': len(self.motorcycles),
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
        
        logger.info("=" * 60)
        logger.info(f"场景执行完成:")
        logger.info(f"  成功: {result['success']}")
        logger.info(f"  碰撞: {result['collision']}")
        if result['collision']:
            logger.info(f"  碰撞对象: {result['collision_with']}")
        logger.info(f"  左转完成: {result['left_turn_completed']}")
        logger.info(f"  天气: {result['weather']}")
        logger.info(f"  耗时: {execution_time:.2f}秒")
        logger.info(f"  总Actor数: {len(self.actors)}")
        logger.info("=" * 60)
        
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
            self.parked_vehicles.clear()
            self.collision_data.clear()
            self.lane_invasion_data.clear()
            self.trajectory_data.clear()
            
            # 重置状态
            self.ego_vehicle = None
            self.oncoming_vehicle = None
            self.occlusion_vehicle = None
            self.collision_sensor = None
            self.lane_invasion_sensor = None
            self.camera_sensor = None
            self.collision_detected = False
            self.left_turn_completed = False
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
    parser = argparse.ArgumentParser(description='AutoExam V2.0 - 高复杂度无保护左转场景')
    parser.add_argument('--host', default='localhost', help='CARLA服务器地址')
    parser.add_argument('--port', type=int, default=2000, help='CARLA服务器端口')
    parser.add_argument('--map', default='Town05', help='地图名称')
    
    # 天气场景
    parser.add_argument('--weather', default='clear_day', 
                       choices=['clear_day', 'clear_night', 'rain_day', 'rain_night',
                               'fog_day', 'fog_night', 'heavy_rain', 'wet_sunset'],
                       help='天气场景')
    
    # 速度配置
    parser.add_argument('--ego-speed', type=float, default=30, help='主车速度 (km/h)')
    parser.add_argument('--oncoming-speed', type=float, default=40, help='对向车速度 (km/h)')
    parser.add_argument('--occlusion', action='store_true', help='启用遮挡车辆')
    
    # 嘈杂度配置
    parser.add_argument('--chaos', default='medium', 
                       choices=['low', 'medium', 'high', 'extreme'],
                       help='路口嘈杂度级别')
    
    # 行人行为
    parser.add_argument('--pedestrian-behavior', default='normal',
                       choices=['normal', 'cautious', 'reckless', 'group', 'erratic', 'emergency'],
                       help='行人行为模式')
    
    # 详细密度配置
    parser.add_argument('--pedestrian-density', choices=['none', 'low', 'medium', 'high', 'extreme'],
                       help='行人密度')
    parser.add_argument('--bicycle-density', choices=['none', 'low', 'medium', 'high', 'extreme'],
                       help='自行车密度')
    parser.add_argument('--motorcycle-density', choices=['none', 'low', 'medium', 'high', 'extreme'],
                       help='摩托车密度')
    parser.add_argument('--traffic-density', choices=['none', 'low', 'medium', 'high', 'extreme'],
                       help='交通流密度')
    parser.add_argument('--parked-density', choices=['none', 'low', 'medium', 'high', 'extreme'],
                       help='路边停车密度')
    
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
            'occlusion': args.occlusion,
            'chaos_level': args.chaos,
            'pedestrian_behavior': args.pedestrian_behavior
        }
        
        # 覆盖详细密度
        if args.pedestrian_density:
            params['pedestrian_density'] = args.pedestrian_density
        if args.bicycle_density:
            params['bicycle_density'] = args.bicycle_density
        if args.motorcycle_density:
            params['motorcycle_density'] = args.motorcycle_density
        if args.traffic_density:
            params['traffic_density'] = args.traffic_density
        if args.parked_density:
            params['parked_vehicle_density'] = args.parked_density
        
        # 设置场景
        if scenario.setup_scenario(params):
            # 执行场景
            result = scenario.execute(max_duration=60)
            
            # 输出结果
            print("\n" + "="*60)
            print("场景执行结果:")
            print(f"  成功: {result['success']}")
            print(f"  碰撞: {result['collision']}")
            if result['collision']:
                print(f"  碰撞对象: {result['collision_with']}")
            print(f"  左转完成: {result['left_turn_completed']}")
            print(f"  天气: {result['weather']}")
            print(f"  耗时: {result['execution_time']:.2f}秒")
            print("\n场景统计:")
            for k, v in result.get('stats', {}).items():
                print(f"  {k}: {v}")
            print("="*60 + "\n")
        else:
            print("场景设置失败")
            
    finally:
        # 清理
        scenario.cleanup()