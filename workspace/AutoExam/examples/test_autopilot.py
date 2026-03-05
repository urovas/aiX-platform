#!/usr/bin/env python3
"""
Autopilot场景测试脚本
使用CARLA的Autopilot功能，让车辆自动处理路口转向
"""

import os
import sys
import logging
import argparse
from datetime import datetime

from pathlib import Path
project_root = str(Path(__file__).resolve().parent.parent)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from autoexam.executors.autopilot_scenario import AutopilotScenario

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AutopilotTest')


def test_autopilot_scenario(args):
    """测试Autopilot场景"""
    logger.info("=" * 60)
    logger.info("测试CARLA Autopilot无保护左转场景")
    logger.info("=" * 60)
 # 设置CARLA路径
    carla_path = os.environ.get('CARLA_PATH', '/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA')
    carla_egg = os.path.join(carla_path, 'PythonAPI', 'carla', 'dist', 'carla-0.9.15-py3.7-linux-x86_64.egg')
    
    # 添加CARLA egg到Python路径
    if os.path.exists(carla_egg):
        sys.path.append(carla_egg)
    else:
        logger.error(f"CARLA egg文件不存在: {carla_egg}")
        return
    
    # 检查CARLA Python API
    try:
        import carla
    except ImportError:
        logger.error("未安装CARLA Python API")
        return False
    
    if carla_egg not in sys.path:
        sys.path.append(carla_egg)
    
    try:
        import carla
    except ImportError as e:
        logger.error(f"无法导入CARLA: {e}")
        return False
    
    client = None
    world = None
    executor = None
    
    try:
        logger.info("连接CARLA服务器...")
        client = carla.Client('localhost', 2000)
        client.set_timeout(10.0)
        
        world = client.load_world(args.map)
        logger.info(f"已加载地图: {world.get_map().name}")
        
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05
        world.apply_settings(settings)
        
        scenario_params = {
            'map': args.map,
            'ego_speed': args.ego_speed,
            'oncoming_speed': args.oncoming_speed,
            'time_gap': args.time_gap,
            'oncoming_vehicle_type': args.oncoming_vehicle,
            'weather': args.weather,
            'occlusion': args.occlusion,
            'traffic_flow': args.traffic_flow if hasattr(args, 'traffic_flow') else args.traffic_density,
            'has_pedestrian': args.pedestrian,
            'pedestrian_density': getattr(args, 'pedestrian_density', 'low'),
            'bicycle_density': getattr(args, 'bicycle_density', 'low'),
            'motorcycle_density': getattr(args, 'motorcycle_density', 'low'),
            'parked_density': getattr(args, 'parked_density', 'low')
        }
        
        logger.info(f"场景参数: {scenario_params}")
        
        executor = AutopilotScenario(world, client)
        
        if not executor.setup_scenario(scenario_params):
            logger.error("场景设置失败")
            return False
        
        logger.info("\n开始执行场景...")
        result = executor.execute(max_duration=45.0)
        
        logger.info("\n执行结果:")
        logger.info(f"  成功: {result['success']}")
        logger.info(f"  碰撞: {result['collision']}")
        logger.info(f"  执行时间: {result['execution_time']:.2f}s")
        logger.info(f"  左转完成: {result.get('left_turn_completed', False)}")
        
        if result.get('trajectory_data'):
            trajectory = result['trajectory_data']
            if len(trajectory) > 0:
                first_yaw = trajectory[0]['rotation']['yaw']
                last_yaw = trajectory[-1]['rotation']['yaw']
                yaw_change = abs(last_yaw - first_yaw)
                logger.info(f"  朝向变化: {first_yaw:.1f}° -> {last_yaw:.1f}° (变化{yaw_change:.1f}°)")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if executor:
            executor.cleanup()
        
        if world:
            settings = world.get_settings()
            settings.synchronous_mode = False
            world.apply_settings(settings)
        
        logger.info("测试完成")


def main():
    parser = argparse.ArgumentParser(description='Autopilot场景测试')
    parser.add_argument('--map', type=str, default='Town05', help='地图名称')
    parser.add_argument('--ego-speed', type=float, default=30, help='主车速度（km/h）')
    parser.add_argument('--oncoming-speed', type=float, default=40, help='对向车速（km/h）')
    parser.add_argument('--time-gap', type=float, default=4.0, help='时间间隙（秒）')
    parser.add_argument('--oncoming-vehicle', type=str, default='sedan', 
                       choices=['sedan', 'truck', 'bus'], help='对向车型')
    parser.add_argument('--weather', type=str, default='clear_day',
                       choices=['clear_day', 'clear_night', 'rain_day', 'rain_night', 'fog_day', 'fog_night', 'heavy_rain', 'wet_sunset', 'clear', 'rain', 'fog', 'night'], help='天气')
    parser.add_argument('--occlusion', action='store_true', help='添加遮挡车辆')
    parser.add_argument('--traffic-flow', type=str, default='low', 
                       choices=['low', 'medium', 'high'], help='交通流密度')
    parser.add_argument('--pedestrian', action='store_true', help='添加行人')
    
    # 详细密度参数
    parser.add_argument('--pedestrian-density', type=str, default='low', 
                       choices=['none', 'low', 'medium', 'high', 'extreme'], help='行人密度')
    parser.add_argument('--bicycle-density', type=str, default='low', 
                       choices=['none', 'low', 'medium', 'high'], help='自行车密度')
    parser.add_argument('--motorcycle-density', type=str, default='low', 
                       choices=['none', 'low', 'medium', 'high'], help='摩托车密度')
    parser.add_argument('--traffic-density', type=str, default='low', 
                       choices=['none', 'low', 'medium', 'high'], help='交通流密度（别名）')
    parser.add_argument('--parked-density', type=str, default='low', 
                       choices=['none', 'low', 'medium', 'high'], help='路边停车密度')
    
    args = parser.parse_args()
    
    test_autopilot_scenario(args)


if __name__ == '__main__':
    main()
