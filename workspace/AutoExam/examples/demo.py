#!/usr/bin/env python3
"""
AutoExam Demo演示
演示从自然语言生成场景、执行测试、输出结果的完整流程
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# 添加项目src目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from autoexam.generators import UnprotectedLeftTurnGenerator
from autoexam.analyzers import DifficultyRater, TestReportGenerator
from autoexam.exporters import OpenScenarioExporter
from autoexam.library import SceneLibrary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AutoExamDemo')

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_subsection(title):
    """打印子章节标题"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)

def demo():
    """演示流程"""
    print_section("AutoExam 无保护左转场景智能生成与测试系统 - Demo演示")
    
    # 初始化组件
    print("\n初始化系统组件...")
    generator = UnprotectedLeftTurnGenerator(use_llm=False)
    rater = DifficultyRater()
    exporter = OpenScenarioExporter()
    library = SceneLibrary(os.path.join(project_root, 'data', 'scenarios'))
    report_generator = TestReportGenerator()
    
    print("✓ 场景生成器初始化完成")
    print("✓ 难度评级器初始化完成")
    print("✓ OpenSCENARIO导出器初始化完成")
    print("✓ 场景库初始化完成")
    print("✓ 测试报告生成器初始化完成")
    
    # 步骤1：自然语言输入
    print_section("步骤1：自然语言输入")
    
    prompt = "生成100个雨天无保护左转场景"
    print(f"\n用户输入: {prompt}")
    print("\n系统解析:")
    print("  - 数量: 100")
    print("  - 场景类型: 无保护左转")
    print("  - 天气: 雨天")
    print("  - 难度: 自动（中等）")
    
    # 步骤2：场景生成
    print_section("步骤2：场景生成")
    
    print("\n正在生成场景...")
    scenarios = generator.generate_from_natural_language(prompt)
    print(f"✓ 成功生成 {len(scenarios)} 个场景")
    
    # 显示前3个场景
    print_subsection("生成的场景示例（前3个）")
    for i, scenario in enumerate(scenarios[:3], 1):
        print(f"\n场景 {i}: {scenario['id']}")
        print(f"  难度: {scenario['difficulty']}")
        print(f"  天气: {scenario['environment']['weather']}")
        print(f"  间隙时间: {scenario['parameters']['gap_time']} 秒")
        print(f"  主车速度: {scenario['ego_vehicle']['initial_speed']} km/h")
        print(f"  对向来车速度: {scenario['parameters']['oncoming_speed']} km/h")
        print(f"  对向来车数量: {scenario['parameters']['oncoming_vehicle_count']}")
    
    # 步骤3：难度评级
    print_section("步骤3：难度评级")
    
    print("\n正在评级场景...")
    for scenario in scenarios:
        rating = rater.rate(scenario)
        scenario['rating'] = rating
    
    print(f"✓ 完成 {len(scenarios)} 个场景的难度评级")
    
    # 显示评级统计
    statistics = rater.get_statistics(scenarios)
    print_subsection("难度分布")
    print(f"  总场景数: {statistics['total_scenarios']}")
    print(f"  简单: {statistics['difficulty_distribution']['easy']} ({statistics['difficulty_distribution']['easy']/statistics['total_scenarios']*100:.1f}%)")
    print(f"  中等: {statistics['difficulty_distribution']['medium']} ({statistics['difficulty_distribution']['medium']/statistics['total_scenarios']*100:.1f}%)")
    print(f"  困难: {statistics['difficulty_distribution']['hard']} ({statistics['difficulty_distribution']['hard']/statistics['total_scenarios']*100:.1f}%)")
    print(f"  地狱: {statistics['difficulty_distribution']['extreme']} ({statistics['difficulty_distribution']['extreme']/statistics['total_scenarios']*100:.1f}%)")
    print(f"  平均难度分数: {statistics['average_score']:.2f}")
    
    # 步骤4：场景导出
    print_section("步骤4：场景导出（OpenSCENARIO格式）")
    
    output_dir = './demo_openscenario'
    print(f"\n正在导出场景到: {output_dir}")
    exporter.export_batch(scenarios, output_dir)
    print(f"✓ 成功导出 {len(scenarios)} 个场景")
    
    # 步骤5：场景保存
    print_section("步骤5：场景保存")
    
    print("\n正在保存场景到场景库...")
    for scenario in scenarios:
        library.save_scenario(scenario)
    print(f"✓ 成功保存 {len(scenarios)} 个场景到场景库")
    
    # 步骤6：模拟测试执行
    print_section("步骤6：模拟测试执行")
    
    print("\n正在模拟测试执行...")
    print("注意：由于需要CARLA服务器，此处为模拟执行")
    
    # 模拟测试结果
    results = []
    for i, scenario in enumerate(scenarios):
        # 模拟测试结果
        difficulty = scenario['difficulty']
        
        if difficulty == 'easy':
            success_rate = 0.9
        elif difficulty == 'medium':
            success_rate = 0.7
        elif difficulty == 'hard':
            success_rate = 0.5
        else:  # extreme
            success_rate = 0.3
        
        import random
        if random.random() < success_rate:
            result = {
                'success': True,
                'collision': False,
                'timeout': False,
                'response_time': 1.5 + random.random() * 1.0,
                'max_deceleration': -2.0 - random.random() * 2.0,
                'execution_time': 5.0 + random.random() * 3.0
            }
        else:
            if random.random() < 0.7:
                result = {
                    'success': False,
                    'collision': True,
                    'timeout': False,
                    'response_time': 2.0 + random.random() * 1.5,
                    'max_deceleration': -5.0 - random.random() * 3.0,
                    'execution_time': 3.0 + random.random() * 2.0,
                    'collision_time': 2.5 + random.random() * 2.0
                }
            else:
                result = {
                    'success': False,
                    'collision': False,
                    'timeout': True,
                    'response_time': 10.0,
                    'max_deceleration': -2.0,
                    'execution_time': 10.0
                }
        
        result['scenario_id'] = scenario['id']
        result['scenario_type'] = scenario['type']
        result['difficulty'] = scenario['difficulty']
        result['test_execution_time'] = datetime.now().isoformat()
        result['environment'] = 'CARLA'
        
        results.append(result)
    
    # 统计测试结果
    success_count = sum(1 for r in results if r['success'])
    collision_count = sum(1 for r in results if r['collision'])
    timeout_count = sum(1 for r in results if r['timeout'])
    
    print(f"✓ 完成 {len(results)} 个场景的测试执行")
    print_subsection("测试结果统计")
    print(f"  成功: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"  碰撞: {collision_count} ({collision_count/len(results)*100:.1f}%)")
    print(f"  超时: {timeout_count} ({timeout_count/len(results)*100:.1f}%)")
    
    # 步骤7：失败案例分析
    print_section("步骤7：失败案例分析")
    
    failure_cases = [r for r in results if not r['success']]
    print(f"\n找到 {len(failure_cases)} 个失败案例")
    
    if failure_cases:
        print_subsection("失败案例示例（前5个）")
        for i, result in enumerate(failure_cases[:5], 1):
            scenario = next((s for s in scenarios if s['id'] == result['scenario_id']), None)
            if scenario:
                failure_type = "碰撞" if result['collision'] else "超时"
                print(f"\n失败案例 {i}:")
                print(f"  场景ID: {result['scenario_id']}")
                print(f"  失败类型: {failure_type}")
                print(f"  难度: {scenario['difficulty']}")
                print(f"  天气: {scenario['environment']['weather']}")
                print(f"  间隙时间: {scenario['parameters']['gap_time']} 秒")
                if result['collision']:
                    print(f"  碰撞时间: {result['collision_time']:.2f} 秒")
                else:
                    print(f"  执行时间: 10.0 秒")
    
    # 步骤8：生成测试报告
    print_section("步骤8：生成测试报告")
    
    print("\n正在生成测试报告...")
    output_dir = './demo_results'
    report_path = report_generator.generate(scenarios, results, output_dir)
    print(f"✓ 测试报告已生成: {report_path}")
    
    # 步骤9：总结
    print_section("演示总结")
    
    print("\n本次演示完成了以下步骤:")
    print("  1. ✓ 自然语言输入解析")
    print("  2. ✓ 场景生成（100个雨天无保护左转场景）")
    print("  3. ✓ 难度评级（简单/中等/困难/地狱）")
    print("  4. ✓ OpenSCENARIO格式导出")
    print("  5. ✓ 场景保存到场景库")
    print("  6. ✓ 模拟测试执行")
    print("  7. ✓ 失败案例分析")
    print("  8. ✓ 测试报告生成")
    
    print("\n输出文件:")
    print(f"  - OpenSCENARIO文件: {output_dir}/")
    print(f"  - 测试报告: {report_path}")
    print(f"  - 测试数据: {output_dir}/test_data.json")
    
    print("\n系统特点:")
    print("  ✓ 支持自然语言输入，自动解析场景需求")
    print("  ✓ 智能生成多样化场景，覆盖不同难度和天气条件")
    print("  ✓ 自动评级场景难度，支持4级难度分级")
    print("  ✓ 导出OpenSCENARIO标准格式，兼容多种仿真平台")
    print("  ✓ 集成场景库管理，方便场景复用和检索")
    print("  ✓ 支持CARLA仿真环境测试")
    print("  ✓ 智能分析失败模式，提供改进建议")
    print("  ✓ 自动生成详细测试报告")
    
    print("\n" + "=" * 70)
    print("  演示完成！")
    print("=" * 70)
    print()

if __name__ == '__main__':
    demo()
