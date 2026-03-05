#!/usr/bin/env python3
"""
LLM驱动场景测试脚本
演示如何使用Qwen-72B生成控制逻辑并执行场景
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from autoexam.integrations.llm_client import LLMClient
from autoexam.executors.llm_scenario_executor import LLMScenarioExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LLMScenarioTest')


def test_llm_control_generation():
    """测试LLM控制逻辑生成"""
    logger.info("=" * 60)
    logger.info("测试LLM控制逻辑生成")
    logger.info("=" * 60)
    
    llm_client = LLMClient()
    
    scenario_params = {
        'ego_speed': 20,
        'oncoming_speed': 60,
        'time_gap': 3.0,
        'oncoming_vehicle_type': 'truck',
        'weather': 'clear',
        'occlusion': False,
        'traffic_flow': 'low',
        'has_pedestrian': True
    }
    
    logger.info(f"场景参数: {json.dumps(scenario_params, indent=2, ensure_ascii=False)}")
    
    logger.info("\n调用LLM生成控制逻辑...")
    result = llm_client.generate_vehicle_control_logic(scenario_params)
    
    if result['success']:
        logger.info("\n控制逻辑生成成功!")
        logic = result['logic']
        
        logger.info("\n阶段:")
        for i, phase in enumerate(logic.get('phases', []), 1):
            logger.info(f"  {i}. {phase['name']}")
            logger.info(f"     触发: {phase['trigger']}")
            logger.info(f"     动作: {', '.join(phase['actions'])}")
        
        logger.info("\n决策点:")
        for dp in logic.get('decision_points', []):
            logger.info(f"  位置: {dp['location']}")
            logger.info(f"  条件: {dp['condition']}")
            logger.info(f"  成立: {dp['if_true']}")
            logger.info(f"  不成立: {dp['if_false']}")
        
        logger.info("\n安全规则:")
        for rule in logic.get('safety_rules', []):
            logger.info(f"  - {rule}")
        
        return True
    else:
        logger.error(f"\n控制逻辑生成失败: {result.get('error')}")
        if 'raw_text' in result:
            logger.info(f"\n原始输出:\n{result['raw_text']}")
        return False


def test_carla_execution_with_llm(use_llm=True):
    """测试CARLA场景执行（可选使用LLM）"""
    logger.info("=" * 60)
    logger.info("测试CARLA场景执行")
    logger.info("=" * 60)
    
    try:
        import carla
    except ImportError:
        logger.error("未安装CARLA Python API")
        return False
    
    carla_path = os.environ.get('CARLA_PATH', '/home/xcc/UROVAs/close_loop/SparseDrive_MomAD/CARLA')
    carla_egg = os.path.join(carla_path, 'PythonAPI', 'carla', 'dist', 'carla-0.9.15-py3.7-linux-x86_64.egg')
    
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
        
        world = client.load_world('Town05')
        logger.info(f"已加载地图: {world.get_map().name}")
        
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.05
        world.apply_settings(settings)
        
        scenario_params = {
            'ego_speed': 20,
            'oncoming_speed': 50,
            'time_gap': 4.0,
            'oncoming_vehicle_type': 'sedan',
            'weather': 'clear',
            'occlusion': False,
            'traffic_flow': 'low',
            'has_pedestrian': False
        }
        
        llm_client = None
        if use_llm:
            logger.info("\n使用LLM生成控制逻辑...")
            llm_client = LLMClient()
        else:
            logger.info("\n使用默认控制逻辑...")
        
        executor = LLMScenarioExecutor(world, client, llm_client)
        
        if not executor.setup_scenario(scenario_params):
            logger.error("场景设置失败")
            return False
        
        carla_map = world.get_map()
        spawn_points = carla_map.get_spawn_points()
        intersection_location = spawn_points[0].location if spawn_points else None
        
        if not intersection_location:
            logger.error("无法获取路口位置")
            return False
        
        logger.info("\n开始执行场景...")
        result = executor.execute(intersection_location, max_duration=30.0)
        
        logger.info("\n执行结果:")
        logger.info(f"  成功: {result['success']}")
        logger.info(f"  碰撞: {result['collision']}")
        logger.info(f"  执行时间: {result['execution_time']:.2f}s")
        logger.info(f"  左转完成: {result.get('left_turn_completed', False)}")
        
        if result.get('control_logic'):
            logger.info("\n使用的控制逻辑:")
            logger.info(json.dumps(result['control_logic'], indent=2, ensure_ascii=False))
        
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
    parser = argparse.ArgumentParser(description='LLM驱动场景测试')
    parser.add_argument('--test', choices=['llm', 'carla', 'both'], default='llm',
                       help='测试类型: llm=仅测试LLM生成, carla=测试CARLA执行, both=两者都测试')
    parser.add_argument('--no-llm', action='store_true',
                       help='CARLA测试时不使用LLM（使用默认逻辑）')
    
    args = parser.parse_args()
    
    if args.test in ['llm', 'both']:
        test_llm_control_generation()
        print()
    
    if args.test in ['carla', 'both']:
        use_llm = not args.no_llm
        test_carla_execution_with_llm(use_llm=use_llm)


if __name__ == '__main__':
    main()
