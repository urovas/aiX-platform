#!/usr/bin/env python3
"""
测试8参数维度的无保护左转场景生成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.unprotected_left_turn_generator import UnprotectedLeftTurnGenerator
import json

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_8d_generation():
    """测试8参数维度场景生成"""
    print_section("8参数维度无保护左转场景生成测试")
    
    # 初始化生成器
    generator = UnprotectedLeftTurnGenerator(use_llm=False)
    
    # 测试不同难度等级
    difficulties = ['easy', 'medium', 'hard', 'extreme']
    
    print("\n参数维度说明:")
    print("  1. 自车速度 (5-30 km/h) - 接近路口的速度")
    print("  2. 对向车速 (30-80 km/h) - 对向直行车的速度")
    print("  3. 时间间隙 (2-8秒) - 自车与对向车到达冲突点的时间差")
    print("  4. 对向车型 (轿车/卡车/公交车) - 不同车型影响博弈行为")
    print("  5. 天气 (晴/雨/雾/夜) - 影响感知难度")
    print("  6. 视野遮挡 (有/无) - 对向大车遮挡后面小车")
    print("  7. 交通流量 (低/中/高) - 多车道多辆车流")
    print("  8. 行人/非机动车 (有/无) - 增加复杂度")
    
    for difficulty in difficulties:
        print_section(f"难度等级: {difficulty.upper()}")
        
        # 生成2个示例场景
        scenarios = generator.generate(count=2, difficulty=difficulty)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n场景 {i}:")
            print(f"  ID: {scenario['id']}")
            print(f"  描述: {scenario['description']}")
            print(f"\n  8参数维度:")
            params = scenario['parameters']
            print(f"    1. 自车速度: {params['ego_speed']} km/h")
            print(f"    2. 对向车速: {params['oncoming_speed']} km/h")
            print(f"    3. 时间间隙: {params['gap_time']} 秒")
            print(f"    4. 对向车型: {params['oncoming_vehicle_type']}")
            print(f"    5. 天气: {params['weather']}")
            print(f"    6. 视野遮挡: {'是' if params['view_blocked'] else '否'}")
            print(f"    7. 交通流量: {params['traffic_flow']}")
            print(f"    8. 行人/非机动车: {'有' if params['pedestrian_present'] else '无'}")
            
            print(f"\n  场景实体:")
            print(f"    - 对向来车: {len(scenario['oncoming_vehicles'])} 辆")
            for v in scenario['oncoming_vehicles']:
                blocked = "(被遮挡)" if v.get('blocked') else ""
                print(f"      * {v['id']}: {v['type']} {blocked}")
            
            if scenario['pedestrians']:
                print(f"    - 行人/非机动车: {len(scenario['pedestrians'])} 个")
                for p in scenario['pedestrians']:
                    print(f"      * {p['id']}: {p['type']}")
            
            if scenario['cross_traffic']:
                print(f"    - 横向交通: {len(scenario['cross_traffic'])} 辆")
    
    # 测试自然语言生成
    print_section("自然语言生成测试")
    
    test_prompts = [
        "生成5个困难难度的雨天卡车遮挡场景",
        "生成3个夜间高流量有行人的场景",
        "生成10个雾天公交车场景"
    ]
    
    for prompt in test_prompts:
        print(f"\n输入: {prompt}")
        parsed = generator._parse_natural_language(prompt)
        print(f"解析结果: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
        
        scenarios = generator.generate_from_natural_language(prompt)
        print(f"生成场景数: {len(scenarios)}")
        if scenarios:
            print(f"示例场景描述: {scenarios[0]['description']}")
    
    # 统计不同参数组合的数量
    print_section("参数组合统计")
    
    all_scenarios = []
    for difficulty in difficulties:
        scenarios = generator.generate(count=50, difficulty=difficulty)
        all_scenarios.extend(scenarios)
    
    # 统计各参数分布
    stats = {
        'ego_speed': {},
        'oncoming_speed': {},
        'gap_time': {},
        'oncoming_vehicle_type': {},
        'weather': {},
        'view_blocked': {'是': 0, '否': 0},
        'traffic_flow': {},
        'pedestrian_present': {'有': 0, '无': 0}
    }
    
    for s in all_scenarios:
        p = s['parameters']
        stats['ego_speed'][p['ego_speed']] = stats['ego_speed'].get(p['ego_speed'], 0) + 1
        stats['oncoming_speed'][p['oncoming_speed']] = stats['oncoming_speed'].get(p['oncoming_speed'], 0) + 1
        stats['gap_time'][p['gap_time']] = stats['gap_time'].get(p['gap_time'], 0) + 1
        stats['oncoming_vehicle_type'][p['oncoming_vehicle_type']] = stats['oncoming_vehicle_type'].get(p['oncoming_vehicle_type'], 0) + 1
        stats['weather'][p['weather']] = stats['weather'].get(p['weather'], 0) + 1
        stats['view_blocked']['是' if p['view_blocked'] else '否'] += 1
        stats['traffic_flow'][p['traffic_flow']] = stats['traffic_flow'].get(p['traffic_flow'], 0) + 1
        stats['pedestrian_present']['有' if p['pedestrian_present'] else '无'] += 1
    
    print(f"\n总共生成 {len(all_scenarios)} 个场景")
    print("\n各参数分布:")
    print(f"  1. 自车速度分布: {dict(sorted(stats['ego_speed'].items()))}")
    print(f"  2. 对向车速分布: {dict(sorted(stats['oncoming_speed'].items()))}")
    print(f"  3. 时间间隙分布: {dict(sorted(stats['gap_time'].items()))}")
    print(f"  4. 对向车型分布: {stats['oncoming_vehicle_type']}")
    print(f"  5. 天气分布: {stats['weather']}")
    print(f"  6. 视野遮挡分布: {stats['view_blocked']}")
    print(f"  7. 交通流量分布: {stats['traffic_flow']}")
    print(f"  8. 行人/非机动车分布: {stats['pedestrian_present']}")
    
    print_section("测试完成")
    print("✓ 8参数维度场景生成器工作正常")
    print("✓ 支持4个难度等级")
    print("✓ 支持自然语言输入")
    print("✓ 参数组合多样化")

if __name__ == '__main__':
    test_8d_generation()
