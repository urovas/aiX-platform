#!/usr/bin/env python3
"""
CARLA仿真集成测试脚本
演示如何使用CARLA执行器进行无保护左转场景测试
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from autoexam.generators import UnprotectedLeftTurnGenerator
from autoexam.executors import CarlaExecutorEnhanced, SimulationRecorder
from autoexam.analyzers import DifficultyRater

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CarlaIntegrationTest')

def test_single_scenario(executor, scenario):
    """测试单个场景
    
    参数:
        executor: CARLA执行器
        scenario: 场景字典
        
    返回:
        测试结果
    """
    logger.info(f"测试场景: {scenario.get('id')}")
    logger.info(f"  参数: {scenario.get('parameters')}")
    
    try:
        result = executor.execute(scenario)
        logger.info(f"  结果: 碰撞={result.get('collision')}, 耗时={result.get('execution_time', 0):.2f}s")
        return result
    except Exception as e:
        logger.error(f"  测试失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'scenario_id': scenario.get('id')
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CARLA仿真集成测试')
    parser.add_argument('--count', type=int, default=5, help='测试场景数量')
    parser.add_argument('--weather', type=str, default='clear', 
                       choices=['clear', 'rain', 'fog', 'night'], help='天气条件')
    parser.add_argument('--start-carla', action='store_true', help='启动CARLA服务器')
    parser.add_argument('--session', type=str, help='会话名称')
    parser.add_argument('--output', type=str, help='输出目录')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("CARLA仿真集成测试")
    logger.info("=" * 60)
    
    data_dir = os.path.join(project_root, 'data')
    results_dir = args.output if args.output else os.path.join(data_dir, 'results')
    
    generator = UnprotectedLeftTurnGenerator(use_llm=False)
    difficulty_rater = DifficultyRater()
    recorder = SimulationRecorder(results_dir)
    
    session_name = args.session if args.session else f"carla_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    recorder.start_session(session_name)
    
    try:
        executor = CarlaExecutorEnhanced()
        
        if args.start_carla:
            logger.info("启动CARLA服务器...")
            if not executor.start_carla_server():
                logger.error("启动CARLA服务器失败")
                return 1
        
        if not executor.is_carla_running():
            logger.error("CARLA服务器未运行，请先启动CARLA或使用 --start-carla 选项")
            logger.info(f"CARLA路径: {executor.carla_path}")
            logger.info(f"启动命令: cd {executor.carla_path} && ./CarlaUE4.sh")
            return 1
        
        logger.info(f"CARLA服务器运行正常")
        
        logger.info(f"生成{args.count}个测试场景...")
        scenarios = generator.generate(
            count=args.count,
            difficulty='medium',
            weather=args.weather
        )
        
        logger.info(f"成功生成{len(scenarios)}个场景")
        
        logger.info("开始执行场景测试...")
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"\n[{i}/{len(scenarios)}] 测试场景: {scenario.get('id')}")
            
            difficulty = difficulty_rater.rate(scenario)
            scenario['difficulty'] = difficulty['difficulty_level']
            
            result = test_single_scenario(executor, scenario)
            recorder.record_result(result)
            
            if i < len(scenarios):
                logger.info("等待3秒后继续...")
                import time
                time.sleep(3)
        
        logger.info("\n" + "=" * 60)
        logger.info("测试完成")
        logger.info("=" * 60)
        
        analysis = recorder.analyze_session()
        logger.info(f"统计结果:")
        logger.info(f"  总场景数: {analysis['total_scenarios']}")
        logger.info(f"  碰撞数: {analysis['collision_count']}")
        logger.info(f"  成功数: {analysis['success_count']}")
        logger.info(f"  碰撞率: {analysis['collision_rate']:.2%}")
        logger.info(f"  成功率: {analysis['success_rate']:.2%}")
        logger.info(f"  平均执行时间: {analysis['avg_execution_time']:.2f}s")
        
        filepath = recorder.save_session()
        logger.info(f"\n结果已保存: {filepath}")
        
        recorder.export_to_csv(recorder.session_data, f"{session_name}.csv")
        logger.info(f"CSV已保存: {os.path.join(results_dir, f'{session_name}.csv')}")
        
        report = recorder.generate_report()
        report_path = os.path.join(results_dir, f"{session_name}_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"报告已保存: {report_path}")
        
        if recorder.session_data:
            logger.info("\n生成可视化图表...")
            
            for i, result in enumerate(recorder.session_data):
                if 'trajectory_data' in result and result['trajectory_data']:
                    trajectory_img = recorder.plot_trajectory(
                        result['trajectory_data'],
                        os.path.join(results_dir, f"{session_name}_trajectory_{i}.png")
                    )
                    
                    velocity_img = recorder.plot_velocity_profile(
                        result['trajectory_data'],
                        os.path.join(results_dir, f"{session_name}_velocity_{i}.png")
                    )
                    
                    if trajectory_img:
                        logger.info(f"  轨迹图已生成: 场景{i+1}")
                    if velocity_img:
                        logger.info(f"  速度曲线已生成: 场景{i+1}")
            
            stats_img = recorder.plot_statistics(
                recorder.session_data,
                os.path.join(results_dir, f"{session_name}_statistics.png")
            )
            if stats_img:
                logger.info(f"  统计图表已生成")
        
        logger.info("\n测试完成！")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n测试被用户中断")
        return 1
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return 1
    finally:
        try:
            if 'executor' in locals():
                executor.cleanup()
        except Exception as e:
            logger.error(f"清理资源失败: {e}")

if __name__ == '__main__':
    sys.exit(main())
