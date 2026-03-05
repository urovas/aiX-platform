#!/usr/bin/env python3
"""
AutoExam Web界面
集成智能体系统
"""

import os
import sys
import json
import random
import datetime
import logging
from flask import Flask, render_template, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AutoExamWeb')

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(project_root, 'src'))

from autoexam.library import SceneLibrary
from autoexam.analyzers import ResultAnalyzer, TestReportGenerator, DifficultyRater
from autoexam.generators import UnprotectedLeftTurnGenerator
from autoexam.exporters import OpenScenarioExporter
from autoexam.integrations import AgentInterface
from autoexam.executors import CarlaExecutorEnhanced, SimulationRecorder

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'autoexam-secret-key'

# 初始化组件
data_dir = os.path.join(project_root, 'data')
scene_library = SceneLibrary(os.path.join(data_dir, 'scenarios'))
result_analyzer = ResultAnalyzer()
test_report_generator = TestReportGenerator()
unprotected_left_turn_generator = UnprotectedLeftTurnGenerator(use_llm=False)
difficulty_rater = DifficultyRater()
openscenario_exporter = OpenScenarioExporter()
agent_interface = AgentInterface()

# CARLA集成组件
carla_executor = None
simulation_recorder = SimulationRecorder(os.path.join(data_dir, 'results'))

try:
    carla_executor = CarlaExecutorEnhanced()
    logger.info("CARLA执行器初始化成功")
except Exception as e:
    logger.warning(f"CARLA执行器初始化失败: {e}")

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/unprotected_left_turn')
def unprotected_left_turn():
    """无保护左转场景页面"""
    return render_template('unprotected_left_turn.html')

@app.route('/scenarios')
def scenarios():
    """场景管理页面"""
    # 获取场景列表
    scenarios = []
    for scenario_id in scene_library.list_scenarios():
        metadata = scene_library.get_scenario_metadata(scenario_id)
        if metadata:
            scenarios.append(metadata)
    
    return render_template('scenarios.html', scenarios=scenarios)

@app.route('/results')
def results():
    """测试结果页面"""
    # 加载测试结果
    results = []
    results_dir = './results'
    if os.path.exists(results_dir):
        for filename in os.listdir(results_dir):
            if filename.endswith('_result.json'):
                result_path = os.path.join(results_dir, filename)
                try:
                    with open(result_path, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        results.append(result_data)
                except Exception as e:
                    print(f"加载结果文件失败: {e}")
    
    return render_template('results.html', results=results)

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """场景生成页面"""
    if request.method == 'POST':
        # 生成场景
        count = int(request.form.get('count', 1))
        risk_level = request.form.get('risk_level', 'high')
        scenario_type = request.form.get('scenario_type', '')
        
        scenarios = []
        for i in range(count):
            if scenario_type:
                # 使用智能体生成指定类型的场景
                result = agent_interface.generate_scenario(scenario_type, risk_level)
            else:
                # 随机选择场景类型
                scenario_types = ['cut-in', 'emergency-brake', 'occlusion', 
                               'pedestrian-crossing', 'multi-vehicle', 'adverse-weather']
                scenario_type = random.choice(scenario_types)
                result = agent_interface.generate_scenario(scenario_type, risk_level)
            
            if result['success']:
                scenarios.append(result['scenario'])
        
        return render_template('generate.html', scenarios=scenarios, count=count)
    
    return render_template('generate.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    """测试执行页面"""
    if request.method == 'POST':
        scenario_id = request.form.get('scenario_id')
        test_type = request.form.get('test_type', 'simulation')
        
        # 加载场景
        scenario = scene_library.load_scenario(scenario_id)
        if not scenario:
            return render_template('test.html', error='场景不存在')
        
        # 执行测试
        if test_type == 'simulation':
            # 使用智能体执行测试
            result = agent_interface.execute_test(scenario)
        else:
            # 真实环境测试
            result = agent_interface.execute_real_test(scenario)
        
        if result['success']:
            # 保存测试结果
            result_data = {
                'scenario_id': scenario_id,
                'test_type': test_type,
                'result': result['result'],
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            result_path = os.path.join('./results', f"{scenario_id}_result.json")
            os.makedirs('./results', exist_ok=True)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            return render_template('test.html', result=result['result'], scenario=scenario)
        else:
            return render_template('test.html', error=result.get('error', '测试失败'))
    
    # 获取场景列表
    scenarios = []
    for scenario_id in scene_library.list_scenarios():
        metadata = scene_library.get_scenario_metadata(scenario_id)
        if metadata:
            scenarios.append(metadata)
    
    return render_template('test.html', scenarios=scenarios)

@app.route('/analyze/<scenario_id>')
def analyze(scenario_id):
    """分析结果页面"""
    # 加载场景和结果
    scenario = scene_library.load_scenario(scenario_id)
    if not scenario:
        return render_template('analyze.html', error='场景不存在')
    
    result_path = os.path.join('./results', f"{scenario_id}_result.json")
    if not os.path.exists(result_path):
        return render_template('analyze.html', error='测试结果不存在')
    
    with open(result_path, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    
    # 分析结果
    analysis = result_analyzer.analyze(scenario, result_data['result'])
    
    return render_template('analyze.html', scenario=scenario, 
                         result=result_data['result'], analysis=analysis)

@app.route('/report')
def report():
    """报告页面"""
    # 生成测试报告
    scenarios = []
    results = []
    
    for scenario_id in scene_library.list_scenarios():
        scenario = scene_library.load_scenario(scenario_id)
        if scenario:
            scenarios.append(scenario)
            
            # 加载结果
            result_path = os.path.join('./results', f"{scenario_id}_result.json")
            if os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                    results.append(result_data['result'])
    
    if scenarios and results:
        report_path = test_report_generator.generate(scenarios, results, './results')
        return render_template('report.html', report_path=report_path)
    
    return render_template('report.html', error='没有足够的场景或结果数据')

# API路由
@app.route('/api/scenarios')
def api_scenarios():
    """场景API"""
    scenarios = []
    for scenario_id in scene_library.list_scenarios():
        metadata = scene_library.get_scenario_metadata(scenario_id)
        if metadata:
            scenarios.append(metadata)
    return jsonify(scenarios)

@app.route('/api/results')
def api_results():
    """结果API"""
    results = []
    results_dir = './results'
    if os.path.exists(results_dir):
        for filename in os.listdir(results_dir):
            if filename.endswith('_result.json'):
                result_path = os.path.join(results_dir, filename)
                try:
                    with open(result_path, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        results.append(result_data)
                except Exception as e:
                    print(f"加载结果文件失败: {e}")
    return jsonify(results)

@app.route('/api/statistics')
def api_statistics():
    """统计API"""
    stats = scene_library.get_statistics()
    return jsonify(stats)

@app.route('/api/agents')
def api_agents():
    """智能体列表API"""
    result = agent_interface.list_agents()
    return jsonify(result)

@app.route('/api/unprotected_left_turn/generate', methods=['POST'])
def api_generate_unprotected_left_turn():
    """生成无保护左转场景API"""
    data = request.get_json()
    
    count = data.get('count', 1)
    difficulty = data.get('difficulty', 'medium')
    weather = data.get('weather', None)
    
    # 生成场景
    scenarios = unprotected_left_turn_generator.generate(count, difficulty, weather)
    
    # 评级场景
    for scenario in scenarios:
        rating = difficulty_rater.rate(scenario)
        scenario['rating'] = rating
    
    # 保存场景
    for scenario in scenarios:
        scene_library.save_scenario(scenario)
    
    return jsonify({
        'success': True,
        'scenarios': scenarios,
        'count': len(scenarios)
    })

@app.route('/api/unprotected_left_turn/generate_from_natural_language', methods=['POST'])
def api_generate_from_natural_language():
    """从自然语言生成无保护左转场景API"""
    data = request.get_json()
    
    prompt = data.get('prompt', '')
    
    # 从自然语言生成场景
    scenarios = unprotected_left_turn_generator.generate_from_natural_language(prompt)
    
    # 评级场景
    for scenario in scenarios:
        rating = difficulty_rater.rate(scenario)
        scenario['rating'] = rating
    
    # 保存场景
    for scenario in scenarios:
        scene_library.save_scenario(scenario)
    
    return jsonify({
        'success': True,
        'scenarios': scenarios,
        'count': len(scenarios)
    })

@app.route('/api/unprotected_left_turn/export', methods=['POST'])
def api_export_unprotected_left_turn():
    """导出无保护左转场景为OpenSCENARIO格式API"""
    data = request.get_json()
    
    scenario_ids = data.get('scenario_ids', [])
    output_dir = data.get('output_dir', './openscenario/unprotected_left_turn')
    
    # 加载场景
    scenarios = []
    for scenario_id in scenario_ids:
        scenario = scene_library.load_scenario(scenario_id)
        if scenario:
            scenarios.append(scenario)
    
    # 导出场景
    openscenario_exporter.export_batch(scenarios, output_dir)
    
    return jsonify({
        'success': True,
        'count': len(scenarios),
        'output_dir': output_dir
    })

@app.route('/api/unprotected_left_turn/adversarial_generate', methods=['POST'])
def api_adversarial_generate():
    """对抗性生成无保护左转场景API"""
    data = request.get_json()
    
    initial_count = data.get('initial_count', 100)
    iterations = data.get('iterations', 3)
    executor = data.get('executor', 'simulate')
    
    try:
        # 执行迭代对抗性生成
        results = unprotected_left_turn_generator.iterative_adversarial_generation(
            initial_count=initial_count,
            iterations=iterations
        )
        
        # 保存所有生成的场景
        total_saved = 0
        for iteration in results['iterations']:
            for scenario in iteration['scenarios']:
                scene_library.save_scenario(scenario)
                total_saved += 1
        
        return jsonify({
            'success': True,
            'total_scenarios': results['total_scenarios'],
            'total_failures': results['total_failures'],
            'high_risk_count': len(results['final_high_risk_params']),
            'saved_count': total_saved,
            'iterations': len(results['iterations'])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/unprotected_left_turn/scenarios')
def api_unprotected_left_turn_scenarios():
    """获取无保护左转场景列表API"""
    scenarios = []
    for scenario_id in scene_library.list_scenarios():
        scenario = scene_library.load_scenario(scenario_id)
        if scenario and scenario.get('type') == 'unprotected-left-turn':
            scenarios.append({
                'id': scenario['id'],
                'description': scenario.get('description', ''),
                'difficulty': scenario.get('difficulty', 'medium'),
                'weather': scenario.get('parameters', {}).get('weather', 'clear'),
                'vehicle_type': scenario.get('parameters', {}).get('oncoming_vehicle_type', 'sedan'),
                'gap_time': scenario.get('parameters', {}).get('gap_time', 0),
                'tested': scenario.get('tested', False),
                'success': scenario.get('success', False)
            })
    return jsonify({'success': True, 'scenarios': scenarios})

@app.route('/api/unprotected_left_turn/statistics')
def api_unprotected_left_turn_statistics():
    """获取无保护左转场景统计API"""
    stats = {'total': 0, 'easy': 0, 'medium': 0, 'hard': 0, 'extreme': 0, 'adversarial': 0}
    
    for scenario_id in scene_library.list_scenarios():
        scenario = scene_library.load_scenario(scenario_id)
        if scenario and scenario.get('type') == 'unprotected-left-turn':
            stats['total'] += 1
            difficulty = scenario.get('difficulty', 'medium')
            if difficulty in stats:
                stats[difficulty] += 1
    
    return jsonify(stats)

@app.route('/api/unprotected_left_turn/scenario/<scenario_id>')
def api_get_scenario(scenario_id):
    """获取单个场景详情API"""
    scenario = scene_library.load_scenario(scenario_id)
    if scenario:
        return jsonify({'success': True, 'scenario': scenario})
    else:
        return jsonify({'success': False, 'error': '场景不存在'})

@app.route('/api/unprotected_left_turn/export/<scenario_id>')
def api_export_scenario(scenario_id):
    """导出单个场景为OpenSCENARIO格式API"""
    scenario = scene_library.load_scenario(scenario_id)
    if not scenario:
        return jsonify({'success': False, 'error': '场景不存在'})
    
    output_dir = './openscenario/unprotected_left_turn'
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = openscenario_exporter.export(scenario, output_dir)
    
    return jsonify({
        'success': True,
        'file_path': file_path
    })

@app.route('/api/unprotected_left_turn/generate_report', methods=['POST'])
def api_generate_report():
    """生成测试报告API"""
    try:
        # 加载所有场景和结果
        scenarios = []
        results = []
        
        for scenario_id in scene_library.list_scenarios():
            scenario = scene_library.load_scenario(scenario_id)
            if scenario and scenario.get('type') == 'unprotected-left-turn':
                scenarios.append(scenario)
                
                # 加载测试结果
                result_path = os.path.join('./results', f"{scenario_id}_result.json")
                if os.path.exists(result_path):
                    with open(result_path, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        results.append(result_data.get('result', {}))
                else:
                    # 模拟结果
                    results.append({
                        'scenario_id': scenario_id,
                        'success': True,
                        'collision': False,
                        'timeout': False
                    })
        
        # 生成报告
        output_dir = './reports'
        os.makedirs(output_dir, exist_ok=True)
        report_path = test_report_generator.generate(scenarios, results, output_dir)
        
        return jsonify({
            'success': True,
            'report_path': report_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/unprotected_left_turn/batch_generate', methods=['POST'])
def api_batch_generate_unprotected_left_turn():
    """批量生成无保护左转场景API"""
    data = request.get_json()
    
    generation_config = data.get('config', [
        {'count': 125, 'difficulty': 'easy', 'weather': 'clear'},
        {'count': 125, 'difficulty': 'medium', 'weather': 'clear'},
        {'count': 125, 'difficulty': 'hard', 'weather': 'rain'},
        {'count': 125, 'difficulty': 'extreme', 'weather': 'rain_night'}
    ])
    
    all_scenarios = []
    
    # 按配置生成场景
    for config in generation_config:
        count = config['count']
        difficulty = config['difficulty']
        weather = config['weather']
        
        scenarios = unprotected_left_turn_generator.generate(count, difficulty, weather)
        
        # 评级场景
        for scenario in scenarios:
            rating = difficulty_rater.rate(scenario)
            scenario['rating'] = rating
        
        all_scenarios.extend(scenarios)
    
    # 保存场景
    for scenario in all_scenarios:
        scene_library.save_scenario(scenario)
    
    # 生成统计信息
    statistics = difficulty_rater.get_statistics(all_scenarios)
    
    # 导出OpenSCENARIO格式
    output_dir = './openscenario/unprotected_left_turn'
    openscenario_exporter.export_batch(all_scenarios, output_dir)
    
    return jsonify({
        'success': True,
        'scenarios': all_scenarios,
        'count': len(all_scenarios),
        'statistics': statistics,
        'output_dir': output_dir
    })

@app.route('/api/carla/status', methods=['GET'])
def api_carla_status():
    """获取CARLA状态API"""
    try:
        if carla_executor is None:
            return jsonify({
                'success': False,
                'status': 'not_initialized',
                'message': 'CARLA执行器未初始化'
            })
        
        is_running = carla_executor.is_carla_running()
        
        return jsonify({
            'success': True,
            'status': 'running' if is_running else 'stopped',
            'carla_path': carla_executor.carla_path,
            'host': carla_executor.host,
            'port': carla_executor.port,
            'town': carla_executor.town
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/carla/execute', methods=['POST'])
def api_carla_execute():
    """CARLA执行场景API"""
    try:
        if carla_executor is None:
            return jsonify({
                'success': False,
                'error': 'CARLA执行器未初始化'
            })
        
        data = request.get_json()
        scenario = data.get('scenario')
        
        if not scenario:
            return jsonify({
                'success': False,
                'error': '缺少场景参数'
            })
        
        logger.info(f"CARLA执行场景: {scenario.get('id')}")
        
        result = carla_executor.execute(scenario)
        simulation_recorder.record_result(result)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        logger.error(f"CARLA执行失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/carla/batch_execute', methods=['POST'])
def api_carla_batch_execute():
    """CARLA批量执行场景API"""
    try:
        if carla_executor is None:
            return jsonify({
                'success': False,
                'error': 'CARLA执行器未初始化'
            })
        
        data = request.get_json()
        scenarios = data.get('scenarios', [])
        session_name = data.get('session_name')
        
        if not scenarios:
            return jsonify({
                'success': False,
                'error': '缺少场景列表'
            })
        
        if session_name:
            simulation_recorder.start_session(session_name)
        
        results = []
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"[{i}/{len(scenarios)}] 执行场景: {scenario.get('id')}")
            
            result = carla_executor.execute(scenario)
            simulation_recorder.record_result(result)
            results.append(result)
        
        analysis = simulation_recorder.analyze_session()
        
        return jsonify({
            'success': True,
            'results': results,
            'analysis': analysis,
            'count': len(results)
        })
    except Exception as e:
        logger.error(f"CARLA批量执行失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/carla/visualization/trajectory', methods=['POST'])
def api_carla_visualization_trajectory():
    """生成轨迹可视化API"""
    try:
        data = request.get_json()
        trajectory_data = data.get('trajectory_data', [])
        
        if not trajectory_data:
            return jsonify({
                'success': False,
                'error': '缺少轨迹数据'
            })
        
        img_base64 = simulation_recorder.plot_trajectory(trajectory_data)
        
        return jsonify({
            'success': True,
            'image': img_base64
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/carla/visualization/velocity', methods=['POST'])
def api_carla_visualization_velocity():
    """生成速度曲线可视化API"""
    try:
        data = request.get_json()
        trajectory_data = data.get('trajectory_data', [])
        
        if not trajectory_data:
            return jsonify({
                'success': False,
                'error': '缺少轨迹数据'
            })
        
        img_base64 = simulation_recorder.plot_velocity_profile(trajectory_data)
        
        return jsonify({
            'success': True,
            'image': img_base64
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/carla/sessions', methods=['GET'])
def api_carla_sessions():
    """获取测试会话列表API"""
    try:
        results_dir = os.path.join(data_dir, 'results')
        
        if not os.path.exists(results_dir):
            return jsonify({
                'success': True,
                'sessions': []
            })
        
        sessions = []
        for filename in os.listdir(results_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(results_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        'name': filename,
                        'count': len(data),
                        'path': filepath
                    })
                except Exception as e:
                    logger.warning(f"加载会话文件失败: {filename}")
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("Starting AutoExam Web Server...")
    print("Access the web interface at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
