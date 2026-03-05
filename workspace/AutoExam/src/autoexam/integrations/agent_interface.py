#!/usr/bin/env python3
"""
智能体调用接口模块
用于与OpenClaw和现有的智能体系统交互
"""

import subprocess
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('AgentInterface')

class AgentInterface:
    """智能体接口类"""
    
    def __init__(self):
        """初始化智能体接口"""
        self.agents = {
            'ego-controller': '主车控制器',
            'adversarial-vehicle-a': '干扰车A',
            'adversarial-vehicle-b': '干扰车B',
            'vulnerable-road-user': '弱势道路使用者',
            'environment-controller': '环境参数控制器',
            'sensor-simulator': '传感器噪声模拟器',
            'world-model-renderer': '世界模型渲染器',
            'scenario-recorder': '场景记录与标注器',
            'rl-optimizer': '强化学习优化器',
            'safety-monitor': '安全监控器',
            'diagnostic-analyzer': '诊断分析器'
        }
    
    def run_agent(self, agent_id: str, prompt: str, timeout: int = 60) -> Dict:
        """运行智能体
        
        参数:
            agent_id: 智能体ID
            prompt: 提示词
            timeout: 超时时间（秒）
            
        返回:
            智能体响应结果
        """
        try:
            cmd = [
                'openclaw-cn', 'run',
                '--agent', agent_id,
                '--prompt', prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                logger.info(f"智能体 {agent_id} 执行成功")
                return {
                    'success': True,
                    'agent_id': agent_id,
                    'output': result.stdout,
                    'error': None
                }
            else:
                logger.error(f"智能体 {agent_id} 执行失败: {result.stderr}")
                return {
                    'success': False,
                    'agent_id': agent_id,
                    'output': None,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"智能体 {agent_id} 执行超时")
            return {
                'success': False,
                'agent_id': agent_id,
                'output': None,
                'error': '执行超时'
            }
        except Exception as e:
            logger.error(f"智能体 {agent_id} 执行异常: {e}")
            return {
                'success': False,
                'agent_id': agent_id,
                'output': None,
                'error': str(e)
            }
    
    def generate_scenario(self, scenario_type: str, risk_level: str = 'high') -> Dict:
        """使用智能体生成场景
        
        参数:
            scenario_type: 场景类型
            risk_level: 风险等级
            
        返回:
            生成的场景
        """
        # 根据场景类型选择智能体
        agent_mapping = {
            'cut-in': 'adversarial-vehicle-a',
            'emergency-brake': 'adversarial-vehicle-a',
            'occlusion': 'adversarial-vehicle-b',
            'pedestrian-crossing': 'vulnerable-road-user',
            'multi-vehicle': 'adversarial-vehicle-b',
            'adverse-weather': 'environment-controller'
        }
        
        agent_id = agent_mapping.get(scenario_type, 'adversarial-vehicle-a')
        
        # 构建提示词
        prompt = f"""生成一个{risk_level}风险等级的{scenario_type}场景。
要求：
1. 场景参数必须符合物理规律
2. 输出格式为JSON，包含以下字段：
   - type: 场景类型
   - risk_level: 风险等级
   - parameters: 场景参数（角度、速度、距离等）
   - environment: 环境条件（天气、光照、路面）
3. 参数范围：
   - 切入角度：15-45度
   - 速度差：20-60km/h
   - 距离：10-80米
   - 减速度：-4到-8m/s²
4. 输出完整的JSON格式"""
        
        result = self.run_agent(agent_id, prompt)
        
        if result['success']:
            try:
                # 解析JSON响应
                output = result['output']
                scenario = json.loads(output)
                return {
                    'success': True,
                    'scenario': scenario
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析场景JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"解析JSON失败: {e}"
                }
        else:
            return result
    
    def execute_test(self, scenario: Dict) -> Dict:
        """执行测试场景
        
        参数:
            scenario: 场景字典
            
        返回:
            测试结果
        """
        # 使用主车控制器执行测试
        prompt = f"""执行以下场景测试：
场景类型：{scenario['type']}
风险等级：{scenario['risk_level']}
场景参数：{json.dumps(scenario['parameters'], ensure_ascii=False)}
环境条件：{json.dumps(scenario['environment'], ensure_ascii=False)}

要求：
1. 模拟自动驾驶系统在该场景下的反应
2. 输出格式为JSON，包含：
   - success: 是否成功
   - collision: 是否发生碰撞
   - response_time: 响应时间（秒）
   - max_deceleration: 最大减速度（m/s²）
   - lane_departure: 是否偏离车道
3. 输出完整的JSON格式"""
        
        result = self.run_agent('ego-controller', prompt)
        
        if result['success']:
            try:
                output = result['output']
                test_result = json.loads(output)
                return {
                    'success': True,
                    'result': test_result
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析测试结果JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"解析JSON失败: {e}"
                }
        else:
            return result
    
    def analyze_failure(self, scenario: Dict, test_result: Dict) -> Dict:
        """分析失败案例
        
        参数:
            scenario: 场景字典
            test_result: 测试结果
            
        返回:
            分析结果
        """
        prompt = f"""分析以下测试失败案例：
场景类型：{scenario['type']}
风险等级：{scenario['risk_level']}
场景参数：{json.dumps(scenario['parameters'], ensure_ascii=False)}
测试结果：{json.dumps(test_result, ensure_ascii=False)}

要求：
1. 识别失败模式（感知错误/决策错误/执行错误）
2. 分析根本原因
3. 提供改进建议
4. 输出格式为JSON，包含：
   - failure_mode: 失败模式
   - root_cause: 根本原因
   - improvement_suggestion: 改进建议
5. 输出完整的JSON格式"""
        
        result = self.run_agent('diagnostic-analyzer', prompt)
        
        if result['success']:
            try:
                output = result['output']
                analysis = json.loads(output)
                return {
                    'success': True,
                    'analysis': analysis
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析分析结果JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"解析JSON失败: {e}"
                }
        else:
            return result
    
    def optimize_parameters(self, scenario_type: str, iterations: int = 100) -> Dict:
        """优化场景参数
        
        参数:
            scenario_type: 场景类型
            iterations: 迭代次数
            
        返回:
            优化后的参数
        """
        prompt = f"""优化{scenario_type}场景的参数，迭代{iterations}次。
要求：
1. 使用强化学习算法优化参数
2. 目标是最大化场景的挑战性和稀缺性
3. 输出格式为JSON，包含：
   - scenario_type: 场景类型
   - optimized_parameters: 优化后的参数
   - reward: 最佳奖励值
4. 输出完整的JSON格式"""
        
        result = self.run_agent('rl-optimizer', prompt)
        
        if result['success']:
            try:
                output = result['output']
                optimized = json.loads(output)
                return {
                    'success': True,
                    'optimized': optimized
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析优化结果JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"解析JSON失败: {e}"
                }
        else:
            return result
    
    def generate_video(self, scenario: Dict) -> Dict:
        """生成场景视频
        
        参数:
            scenario: 场景字典
            
        返回:
            视频生成结果
        """
        prompt = f"""生成以下场景的视频：
场景类型：{scenario['type']}
场景参数：{json.dumps(scenario['parameters'], ensure_ascii=False)}
环境条件：{json.dumps(scenario['environment'], ensure_ascii=False)}

要求：
1. 生成物理一致的驾驶场景视频
2. 生成OpenSCENARIO格式标注
3. 确保车辆运动、光照、天气等参数的一致性
4. 输出视频文件路径和标注文件路径"""
        
        result = self.run_agent('world-model-renderer', prompt)
        return result
    
    def check_safety(self, scenario: Dict) -> Dict:
        """检查场景安全性
        
        参数:
            scenario: 场景字典
            
        返回:
            安全检查结果
        """
        prompt = f"""检查以下场景的安全性和物理合理性：
场景类型：{scenario['type']}
风险等级：{scenario['risk_level']}
场景参数：{json.dumps(scenario['parameters'], ensure_ascii=False)}
环境条件：{json.dumps(scenario['environment'], ensure_ascii=False)}

要求：
1. 评估风险等级（低/中/高/极高）
2. 检查是否违反物理规律（如刹车距离不足、加速度超限）
3. 对高风险场景提出调整建议
4. 输出格式为JSON，包含：
   - risk_assessment: 风险评估
   - physical_constraints: 物理约束检查
   - adjustment_suggestion: 调整建议
5. 输出完整的JSON格式"""
        
        result = self.run_agent('safety-monitor', prompt)
        
        if result['success']:
            try:
                output = result['output']
                safety = json.loads(output)
                return {
                    'success': True,
                    'safety': safety
                }
            except json.JSONDecodeError as e:
                logger.error(f"解析安全检查结果JSON失败: {e}")
                return {
                    'success': False,
                    'error': f"解析JSON失败: {e}"
                }
        else:
            return result
    
    def list_agents(self) -> List[Dict]:
        """列出所有智能体
        
        返回:
            智能体列表
        """
        try:
            cmd = ['openclaw-cn', 'agent', 'list']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("获取智能体列表成功")
                return {
                    'success': True,
                    'agents': result.stdout
                }
            else:
                logger.error(f"获取智能体列表失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            logger.error(f"获取智能体列表异常: {e}")
            return {
                'success': False,
                'error': str(e)
            }
